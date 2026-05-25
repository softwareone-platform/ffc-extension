import logging
from typing import Any

from fastapi import APIRouter

from app.dependencies.api_clients import (
    APIModifierClient,
    ExtensionClient,
    InstallationClient,
    OptscaleAuthClient,
)
from app.dependencies.core import AppSettings, ExtensionContext
from app.dependencies.db import OrganizationRepository
from app.fulfilment.constants import (
    MPT_ORDER_STATUS_PROCESSING,
)
from app.fulfilment.order import (
    apply_fulfillment_defaults_if_needed,
    fulfill_order,
    start_task_and_get_order,
    validate_and_move_to_querying_if_needed,
)
from app.fulfilment.recovery import handle_exception
from app.fulfilment.templates import initialize_templates
from app.schemas.core import Event, EventResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/events")


@router.post("/commerce/orders")
async def process_order(
    event: Event,
    settings: AppSettings,
    ext_ctx: ExtensionContext,
    client: InstallationClient,
    ext_client: ExtensionClient,
    organization_repo: OrganizationRepository,
    optscale_auth_client: OptscaleAuthClient,
    api_modifier_client: APIModifierClient,
) -> EventResponse:
    logger.info(f"--------PAYLOAD {event}")

    order_id = event.object.id
    if event.task is None:
        logger.error("Received order event %s without task information", event.id)
        return EventResponse.cancel()

    task_id = event.task.id
    product_id = settings.mpt_product_id
    order: dict[str, Any] = {}

    try:
        # 1. Fetch templates
        await initialize_templates(ext_client, product_id)
        # 2. Set task to Processing & fetch order
        order = await start_task_and_get_order(
            task_id=task_id,
            order_id=order_id,
            ext_client=ext_client,
            ext_ctx=ext_ctx,
            client=client,
        )

        # 3. Check status — skip if not processing
        if order["status"] != MPT_ORDER_STATUS_PROCESSING:
            await ext_client.complete_task(task_id)
            return EventResponse.ok()

        # 4. Setting fulfillment's parameters
        order = await apply_fulfillment_defaults_if_needed(
            ext_client=ext_client,
            order=order,
            settings=settings,
        )
        # 5. Check order parameters & move order to Query if parameters are invalid
        order, is_valid = await validate_and_move_to_querying_if_needed(
            order=order,
            ext_client=ext_client,
        )
        if not is_valid:
            await ext_client.complete_task(task_id)
            return EventResponse.ok()

        # 6. Start Order 'happy path' processing
        return await fulfill_order(
            api_modifier_client=api_modifier_client,
            ext_client=ext_client,
            optscale_auth_client=optscale_auth_client,
            order=order,
            order_id=order_id,
            organization_repo=organization_repo,
            task_id=task_id,
        )

    except Exception as exc:
        return await handle_exception(exc, ext_client, order, order_id, task_id)
