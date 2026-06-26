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
from app.parameters import set_is_new_user

logger = logging.getLogger(__name__)


async def get_or_create_organization(
    ext_client: MPTClient,
    api_modifier_client: APIModifierClient,
    order: dict,
    organization_repo: OrganizationHandler,
    employee_id: str,
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

    if created or not organization.linked_organization_id:
        organization_on_optscale = await api_modifier_client.create_organization(
            org_name=org_name, user_id=employee_id, currency=org_currency
        )
        optscale_org = organization_on_optscale.json()
        logger.info("Organization on OptScale created with id %s ", optscale_org["id"])
        await ext_client.update_agreement(
            agreement_id,
            externalIds={"vendor": organization.id},
        )
        await organization_repo.update(
            organization.id,
            {
                "linked_organization_id": optscale_org["id"],
            },
        )
        logger.info(
            "%s: Updating organization %s with external id to %s ",
            order["id"],
            organization.id,
            optscale_org["id"],
        )
        logger.info("Organization created with id %s ", organization.id)
    else:
        logger.info("Organization already exists with id %s ", organization.id)

    return organization


async def create_employee(
    ext_client: MPTClient,
    api_modifier_client: APIModifierClient,
    optscale_auth_client: OptscaleAuthClient,
    order: dict,
) -> tuple[dict, str, str]:
    """Resolve or create the admin user and persist the `isNewUser` fulfillment flag."""
    administrator = get_ordering_parameter(order, PARAM_ADMIN_CONTACT)["value"]
    email = administrator["email"]

    try:
        response = await optscale_auth_client.get_existing_user_info(email)
        response_json = response.json()
        employee_id = response_json["user_info"]["id"]
        is_new = False
        logger.info("Employee exists with id %s for order %s", employee_id, order["id"])
    except UserDoesNotExist:
        response = await api_modifier_client.create_user(
            email=email,
            display_name=f"{administrator['firstName']} {administrator['lastName']}",
            password=secrets.token_urlsafe(128),
        )
        response_json = response.json()
        employee_id = response_json["id"]
        # await optscale_client.reset_password(email)
        is_new = True
        logger.info("Employee created with id %s for order %s", employee_id, order["id"])
    updated_order = set_is_new_user(order, is_new=is_new)
    order = await ext_client.update_order(
        order["id"],
        parameters=updated_order["parameters"],
    )
    logger.debug("Updated orders %s %s ", updated_order["parameters"], order["parameters"])
    return order, employee_id, email
