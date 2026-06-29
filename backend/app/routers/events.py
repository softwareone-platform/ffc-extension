import logging
from datetime import UTC, datetime
from typing import assert_never

from fastapi import APIRouter

from app.conf import get_settings
from app.dependencies.api_clients import (
    ExtensionClient,
)
from app.dependencies.core import ExtensionContext
from app.dependencies.fulfillment import OrderProcessorFactoryDep
from app.fulfilment.constants import ExceptionSeverity, ProcessResult
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
        result = await processor.handle_exception(exc, now=datetime.now(UTC).date())

        error_message = str(exc)
        logger.error("Process result %s for task %s with error: %s", result, task_id, error_message)
        match result:
            case ProcessResult.RESCHEDULE:
                await ext_client.log_task(
                    task_id,
                    severity=ExceptionSeverity.WARNING,
                    error_message=error_message,
                )
                await ext_client.reschedule_task(task_id)
                return EventResponse.reschedule(seconds=get_settings().reschedule_seconds)

            case ProcessResult.COMPLETE:
                await ext_client.log_task(
                    task_id,
                    severity=ExceptionSeverity.ERROR,
                    error_message=error_message,
                )
                await ext_client.complete_task(task_id)
                return EventResponse.ok()
            case ProcessResult.CANCEL:
                await ext_client.log_task(
                    task_id,
                    severity=ExceptionSeverity.ERROR,
                    error_message=error_message,
                )
                return EventResponse.cancel()
            case ProcessResult.SKIP:
                await ext_client.log_task(
                    task_id,
                    severity=ExceptionSeverity.INFO,
                    error_message=error_message,
                )
                await ext_client.complete_task(task_id)
                return EventResponse.ok()
            case _:
                assert_never(result)
