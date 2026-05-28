import logging
from typing import Any

from app import Settings
from app.api_clients.mpt import MPTClient
from app.db.handlers import OrganizationHandler
from app.dependencies.api_clients import (
    APIModifierClient,
    ExtensionClient,
    OptscaleAuthClient,
)
from app.dependencies.core import ExtensionContext
from app.fulfilment.constants import PURCHASE_EXISTING_TEMPLATE_NAME, PURCHASE_TEMPLATE_NAME
from app.fulfilment.parameters import check_order_parameters, get_parameter_updates
from app.fulfilment.provisioning import create_employee, get_or_create_organization
from app.fulfilment.subscriptions import create_order_subscription
from app.fulfilment.templates import get_product_template_id, start_processing_order_template
from app.parameters import PARAM_IS_NEW_USER, get_fulfillment_parameter, set_fulfillment_parameter
from app.schemas.core import EventResponse

logger = logging.getLogger(__name__)


async def apply_fulfillment_defaults_if_needed(
    ext_client: MPTClient, order: dict[str, Any], settings: Settings
) -> dict[str, Any]:
    updated_parameters = get_parameter_updates(order, settings)
    if updated_parameters:
        for param_name, param_value in updated_parameters.items():
            order = set_fulfillment_parameter(
                order=order,
                parameter=param_name,
                value=param_value,
            )
        order = await ext_client.update_order(order_id=order["id"], parameters=order["parameters"])
        logger.info("%s: updating fulfillment parameters", order["id"])
    return order


async def start_task_and_get_order(
    *,
    task_id: str,
    order_id: str,
    ext_ctx: ExtensionContext,
    ext_client: MPTClient,
    client: MPTClient,
) -> dict[str, Any]:
    """Start task execution and fetch the order payload."""
    logger.info("Changing task %s status to Processing", task_id)
    await ext_client.start_task(task_id, ext_ctx.instance_id)
    return await client.get_order(order_id)


async def validate_and_move_to_querying_if_needed(
    *,
    order: dict[str, Any],
    ext_client: ExtensionClient,
) -> tuple[dict[str, Any], bool]:
    """
    Validate ordering params and move order back to Querying if invalid.
    """
    order_with_validation_errors, validation_succeeded = check_order_parameters(order)
    order_id = order["id"]
    if not validation_succeeded:
        template_id = await get_product_template_id(ext_client, "OrderQuerying", None)
        await ext_client.update_order(
            order_id=order_id,
            parameters=order_with_validation_errors["parameters"],
        )
        querying_order = await ext_client.set_status_to_querying(
            order_id=order_id, payload={"template": {"id": template_id}}
        )
        logger.info("%s: ordering parameters are invalid, move to querying", querying_order["id"])
        return order_with_validation_errors, False
    return order, True


async def fulfill_order(
    *,
    api_modifier_client: APIModifierClient,
    ext_client: MPTClient,
    optscale_auth_client: OptscaleAuthClient,
    order: dict[str, Any],
    order_id: str,
    organization_repo: OrganizationHandler,
    task_id: str,
) -> EventResponse:
    order = await start_processing_order_template(ext_client, order)
    order, employee_id = await create_employee(
        ext_client, api_modifier_client, optscale_auth_client, order
    )

    organization = await get_or_create_organization(
        ext_client, api_modifier_client, order, organization_repo, employee_id
    )

    await create_order_subscription(ext_client, order, organization)
    is_new_user_param = get_fulfillment_parameter(order, PARAM_IS_NEW_USER)

    if is_new_user_param.get("value") == ["Yes"]:
        template_name = PURCHASE_TEMPLATE_NAME
    else:
        template_name = PURCHASE_EXISTING_TEMPLATE_NAME

    template_id = await get_product_template_id(ext_client, "OrderCompleted", template_name)

    await ext_client.complete_order(order_id=order_id, payload={"template": {"id": template_id}})

    await ext_client.complete_task(task_id)

    return EventResponse.ok()
