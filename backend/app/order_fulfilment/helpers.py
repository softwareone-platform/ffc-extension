import logging
import secrets
from datetime import UTC, date, datetime, timedelta

from app.api_clients.api_modifier import APIModifierClient
from app.api_clients.mpt import MPTClient
from app.api_clients.optscale import OptscaleAuthClient, UserDoesNotExist
from app.db.handlers import OrganizationHandler
from app.db.models import Organization
from app.order_fulfilment.error import ERR_ADMIN_CONTACT, ERR_CURRENCY, ERR_ORGANIZATION_NAME
from app.order_fulfilment.parameters import (
    PARAM_ADMIN_CONTACT,
    PARAM_CURRENCY,
    PARAM_ORGANIZATION_NAME,
    get_ordering_parameter,
    set_ordering_parameter_error,
)
from app.parameters import (
    PARAM_BILLED_PERCENTAGE,
    PARAM_DUE_DATE,
    PARAM_TRIAL_END_DATE,
    PARAM_TRIAL_START_DATE,
    get_due_date,
    get_fulfillment_parameter,
    set_is_new_user,
)

logger = logging.getLogger(__name__)


def check_order_parameters(order) -> tuple[dict, bool]:
    """
    Check that all required ordering parameters have a value.
    For each missing parameter, attach its error to the order. Returns the
    (possibly annotated) order and a flag indicating whether validation
    succeeded.
    """
    errors = {
        PARAM_ORGANIZATION_NAME: ERR_ORGANIZATION_NAME,
        PARAM_CURRENCY: ERR_CURRENCY,
        PARAM_ADMIN_CONTACT: ERR_ADMIN_CONTACT,
    }
    required = [
        PARAM_ORGANIZATION_NAME,
        PARAM_CURRENCY,
        PARAM_ADMIN_CONTACT,
    ]
    validation_succeeded = True
    for param_name in required:
        parameter = get_ordering_parameter(order, param_name)
        if not parameter.get("value"):
            order = set_ordering_parameter_error(order, param_name, errors[param_name])
            validation_succeeded = False
    return order, validation_succeeded


def get_parameter_updates(order, settings):
    """Build default fulfillment parameter values when they are missing in the order."""
    updates = {}
    due_date = get_due_date(order)

    if due_date:
        logger.info(
            f"Due date parameter was setup before {due_date.strftime('%Y-%m-%d')}: skip",
        )
    else:
        due_date = date.today() + timedelta(days=int(settings.due_date_days))
        updates[PARAM_DUE_DATE] = due_date.strftime("%Y-%m-%d")

    if not get_fulfillment_parameter(order, PARAM_BILLED_PERCENTAGE).get("value"):
        updates[PARAM_BILLED_PERCENTAGE] = str(settings.default_billed_percentage)

    trial_start_date = get_fulfillment_parameter(order, PARAM_TRIAL_START_DATE).get("value")
    if not trial_start_date:
        trial_start_date = datetime.now(UTC).date().strftime("%Y-%m-%d")
        updates[PARAM_TRIAL_START_DATE] = trial_start_date

    if not get_fulfillment_parameter(order, PARAM_TRIAL_END_DATE).get("value"):
        trial_end_date = datetime.strptime(trial_start_date, "%Y-%m-%d").date() + timedelta(
            days=int(settings.default_trial_period_duration_days)
        )
        updates[PARAM_TRIAL_END_DATE] = trial_end_date.strftime("%Y-%m-%d")

    return updates


async def create_employee(
    api_modifier_client: APIModifierClient,
    ext_client: MPTClient,
    optscale_auth_client: OptscaleAuthClient,
    order: dict,
) -> dict:
    logger.info(f"Creating employee for order {order['id']}")
    """Resolve or create the admin user and persist the `isNewUser` fulfillment flag."""
    administrator = get_ordering_parameter(order, PARAM_ADMIN_CONTACT)["value"]
    logger.info(f"ADMIN---- {administrator}")
    try:
        response = await optscale_auth_client.get_existing_user_info(administrator["email"])
        user_info = response.json().get("user_info", {})
        employee_id = user_info.get("id")
        if not employee_id:
            logger.warning("User info returned but missing id for email %s", administrator["email"])
        updated_order = set_is_new_user(order, is_new=False)
        order = await ext_client.update_order(
            order_id=order["id"],
            parameters=updated_order["parameters"],
        )
        logger.info("Employee exists with id %s for order %s", employee_id, order["id"])
    except UserDoesNotExist:
        employee = await api_modifier_client.create_user(
            email=administrator["email"],
            display_name=f"{administrator['firstName']} {administrator['lastName']}",
            password=secrets.token_urlsafe(128),
        )
        employee_id = employee.json().get("id")
        updated_order = set_is_new_user(order, is_new=True)
        order = await ext_client.update_order(
            order_id=order["id"],
            parameters=updated_order["parameters"],
        )
        logger.info("Employee created with id %s for order %s", employee_id, order["id"])
    return order


async def get_or_create_organization(
    ext_client: MPTClient, order: dict, organization_repo: OrganizationHandler
) -> Organization:
    """Get or create the organization and link it back to the marketplace agreement."""
    agreement_id = order["agreement"]["id"]
    agreement = await ext_client.get_agreement(agreement_id, select=["authorization"])

    org_name = get_ordering_parameter(order, PARAM_ORGANIZATION_NAME)["value"]
    org_currency = get_ordering_parameter(order, PARAM_CURRENCY)["value"]
    billing_currency = agreement["authorization"]["currency"]  # marketplace billing currency

    organization, created = await organization_repo.get_or_create(
        operations_external_id=agreement_id,
        defaults={
            "name": org_name,
            "currency": org_currency,
            "billing_currency": billing_currency,
        },
    )
    if created:
        logger.info(f"Organization created with id {organization.id}")
    else:
        logger.info(
            f"Organization with external_id {agreement_id} already exists with id {organization.id}"
        )

    # Update existing agreement vendor id with created FFC Organization Id
    await ext_client.update_agreement(
        agreement_id,
        externalIds={"vendor": organization.id},
    )
    logger.info(
        f"{order}: Updating agreement {agreement_id} external id to {organization.id}",
    )
    return organization
