import logging
import traceback

from app.events.core import EventHandler
from app.events.exceptions import ProcessError
from app.notifications import NotificationDetails, send_exception
from app.schemas.core import Event, EventResponse, ExtensionContext

logger = logging.getLogger(__name__)


async def process_event(
    ext_ctx: ExtensionContext,
    event: Event,
    handler: EventHandler,
) -> EventResponse | None:
    """Run the task lifecycle of one event: claim the task, process the object, close the task."""
    object_id = event.object.id
    task_id = event.task.id  # type: ignore
    logger.info("Processing event: %s", event)

    try:
        try:
            await handler.claim_task(ext_ctx, task_id, object_id)
            processor = await handler.get_processor(object_id)
            result = await processor.process()

        except ProcessError as exc:
            logger.warning("%s: %s", object_id, exc)
            result = exc.to_result()

        return await handler.apply_result(task_id, result)
    except Exception:
        logger.exception("%s: task %s failed unexpectedly.", object_id, task_id)
        await _notify_exception(event, ext_ctx.instance_id)
        raise


async def _notify_exception(event: Event, instance_id: str):
    """Post a Teams card about an unexpected failure in `process_event`."""
    try:
        await send_exception(
            "Process Event Error",
            traceback.format_exc(),
            details=NotificationDetails(
                header=("Field", "Value"),
                rows=[
                    ("Event", event.id),
                    ("Event type", event.details.event_type),
                    ("Task", event.task.id),  # ty: ignore[unresolved-attribute]
                    ("Object id", event.object.id),
                    ("Object type", event.object.object_type),
                    ("Instance", instance_id),
                ],
            ),
        )
    except Exception:
        logger.exception(
            "Cound not sent the notification for the task %s",
            event.task.id,  # ty: ignore[unresolved-attribute]
        )
