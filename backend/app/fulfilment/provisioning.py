import logging
import secrets

from app.api_clients.api_modifier import APIModifierClient
from app.api_clients.mpt import MPTClient
from app.api_clients.optscale import OptscaleAuthClient, UserDoesNotExist
from app.db.handlers import OrganizationHandler
from app.db.models import Organization
from app.fulfilment.parameters import (
    PARAM_ADMIN_CONTACT,
    PARAM_CURRENCY,
    PARAM_ORGANIZATION_NAME,
    get_ordering_parameter,
)
from app.parameters import (
    set_is_new_user,
)

logger = logging.getLogger(__name__)


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
        logger.info("Organization created with id %s ", organization.id)
    else:
        logger.info("Organization already exists with id %s ", organization.id)

    # Update existing agreement vendor id with created FFC Organization Id
    await ext_client.update_agreement(
        agreement_id,
        externalIds={"vendor": organization.id},
    )
    logger.info(
        "%s: Updating agreement %s with external id to %s ", order, agreement_id, organization.id
    )

    return organization


async def create_employee(
    api_modifier_client: APIModifierClient,
    ext_client: MPTClient,
    optscale_auth_client: OptscaleAuthClient,
    order: dict,
) -> dict:
    """Resolve or create the admin user and persist the `isNewUser` fulfillment flag."""
    administrator = get_ordering_parameter(order, PARAM_ADMIN_CONTACT)["value"]
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
