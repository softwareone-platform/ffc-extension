import logging

from fastapi import APIRouter

from app.conf import get_settings
from app.dependencies.api_clients import (
    ExtensionClient,
)
from app.dependencies.core import ExtensionContext
from app.dependencies.fulfillment import OrderProcessorFactory
from app.fulfilment.exceptions import UnsupportedOrderTypeError
from app.fulfilment.processing import ProcessingStatus
from app.schemas.core import Event, EventResponse

logger = logging.getLogger(__name__)
router = APIRouter()

#
# @router.post("/orders/validate")
# async def validate_order(order: dict):
#     # Webhook of Change Order
#     order["error"] = ERR_ORDER_TYPE_NOT_SUPPORTED.to_dict(order_type=order["type"])
#     return order
#


@router.post("/orders")
async def process_order(
    event: Event,
    ext_ctx: ExtensionContext,
    ext_client: ExtensionClient,
    factory: OrderProcessorFactory,
) -> EventResponse:
    logger.info("Event: %s", event)
    order_id = event.object.id
    task_id = event.task.id  # type: ignore
    logger.info("Changing task %s status to Processing", task_id)
    await ext_client.start_task(task_id, ext_ctx.instance_id)
    try:
        processor = await factory.get_order_type_processor(order_id)
        result = await processor.process()

        match result.status:
            case ProcessingStatus.RESCHEDULE:
                await ext_client.log_task(
                    task_id,
                    severity=result.severity,
                    error_message=result.message,
                )
                await ext_client.reschedule_task(task_id)
                return EventResponse.reschedule(seconds=get_settings().reschedule_seconds)

            case ProcessingStatus.COMPLETE:
                await ext_client.log_task(
                    task_id,
                    severity=result.severity,
                    error_message=result.message,
                )
                await ext_client.complete_task(task_id)
                return EventResponse.ok()
            case ProcessingStatus.CANCEL:
                await ext_client.log_task(
                    task_id,
                    severity=result.severity,
                    error_message=result.message,
                )
                return EventResponse.cancel()
            case ProcessingStatus.SKIP:
                await ext_client.log_task(
                    task_id,
                    severity=result.severity,
                    error_message=result.message,
                )
                return EventResponse.ok()
    except UnsupportedOrderTypeError as exception:
        await ext_client.log_task(
            task_id,
            severity="Warning",
            error_message=str(exception),
        )
        return EventResponse.cancel()
