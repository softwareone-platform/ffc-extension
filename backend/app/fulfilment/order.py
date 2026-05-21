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
from app.fulfilment.constants import (
    MPT_ORDER_STATUS_QUERYING,
)
from app.fulfilment.helpers import (
    check_order_parameters,
    create_employee,
    get_or_create_organization,
    get_parameter_updates,
)
from app.fulfilment.subscriptions import create_order_subscription
from app.fulfilment.templates import start_processing_order_template
from app.parameters import set_fulfillment_parameter
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
    product_id: str,
    ext_client: ExtensionClient,
) -> tuple[dict[str, Any], bool]:
    """
    Validate ordering params and move order back to Querying if invalid.
    """
    order_with_validation_errors, validation_succeeded = check_order_parameters(order)
    order_id = order["id"]
    if not validation_succeeded:
        template = await ext_client.get_product_template_or_default(
            product_id=product_id,
            status=MPT_ORDER_STATUS_QUERYING,
        )
        # Persist validation errors before moving the order back to Query.
        await ext_client.update_order(
            order_id=order_id,
            parameters=order_with_validation_errors["parameters"],
        )
        querying_order = await ext_client.set_status_to_querying(
            order_id=order_id, payload=template
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
    product_id: str,
    task_id: str,
) -> EventResponse:
    order = await start_processing_order_template(ext_client, order, product_id)
    logger.info(f"-------------Processing order {order_id}")
    # 8 create employee
    order = await create_employee(api_modifier_client, ext_client, optscale_auth_client, order)

    # 9 get or create organization

    organization = await get_or_create_organization(ext_client, order, organization_repo)

    # Create subscription
    await create_order_subscription(ext_client, order, organization)

    # Complete order
    await ext_client.complete_order(order_id=order_id)
    # 7. Complete task
    await ext_client.complete_task(task_id)
    return EventResponse.ok()
