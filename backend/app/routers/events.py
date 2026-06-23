import logging
from datetime import UTC, datetime
from typing import assert_never

from fastapi import APIRouter

from app.api_clients.mpt import MPTClient
from app.conf import get_settings
from app.dependencies.api_clients import (
    ExtensionClient,
)
from app.dependencies.core import ExtensionContext
from app.dependencies.fulfillment import OrderProcessorFactoryDep
from app.fulfilment.processing import ExceptionProcessResult
from app.schemas.core import Event, EventResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/events")


@router.post("/commerce/orders")
async def process_order(
    event: Event,
    ext_ctx: ExtensionContext,
    ext_client: ExtensionClient,
    factory: OrderProcessorFactoryDep,
) -> EventResponse:
    logger.info("Event: %s", event)
    order_id = event.object.id
    task_id = event.task.id
    logger.info("Changing task %s status to Processing", task_id)
    await ext_client.start_task(task_id, ext_ctx.instance_id)
    processor = await factory.get_order_type_processor(order_id)
    try:
        await processor.process()
        await ext_client.complete_task(task_id)
        logger.info("Task %s has been completed", task_id)
        return EventResponse.ok()

    except Exception as exc:
        # order = getattr(exc, "order", None) or order
        action = await processor.handle_exception(exc, now=datetime.now(UTC).date())
        return await _process_error_and_send_response(action, exc, ext_client, order_id, task_id)


async def _process_error_and_send_response(
    action, exc: Exception, ext_client: MPTClient, order_id: str, task_id: str
) -> EventResponse:
    now = datetime.now(UTC).date()
    error_message = str(exc)
    logger.error(f"ACTION {action} occurred")

    async def _description() -> str:
        task = await ext_client.get_task(task_id)
        return f"{task.get('description', '')} - {now.isoformat()} - {error_message}"

    match action:
        case ExceptionProcessResult.RESCHEDULE:
            await ext_client.reschedule_task(task_id, payload={"description": await _description()})
            return EventResponse.reschedule(seconds=get_settings().reschedule_seconds)

        case ExceptionProcessResult.COMPLETE:
            await ext_client.complete_task(task_id)
            return EventResponse.ok()
        case ExceptionProcessResult.CANCEL:
            return EventResponse.cancel()
        case ExceptionProcessResult.SKIP:
            await ext_client.complete_task(task_id)
            return EventResponse.ok()
        case _:
            assert_never(action)
