import logging

from app.api_clients.mpt import MPTClient
from app.conf import get_settings
from app.events.core import EventHandler
from app.events.exceptions import EventError
from app.events.processing import ProcessingResult, ProcessingStatus
from app.schemas.core import Event, EventResponse, ExtensionContext

logger = logging.getLogger(__name__)


async def apply_result(
    ext_client: MPTClient, task_id: str, result: ProcessingResult
) -> EventResponse | None:
    """
    Log the result and move the task to the state it calls for.

    There is deliberately no `case _`: an unhandled status falls out of the `match` and
    returns `None`, which fails response validation instead of silently acknowledging the
    event. Add a `case` arm here when a new `ProcessingStatus` lands.
    """
    match result.status:
        case ProcessingStatus.RESCHEDULE:
            await ext_client.log_task(
                task_id, severity=result.severity, error_message=result.message
            )
            await ext_client.reschedule_task(task_id)
            return EventResponse.reschedule(seconds=get_settings().reschedule_seconds)
        case ProcessingStatus.COMPLETE:
            await ext_client.log_task(
                task_id, severity=result.severity, error_message=result.message
            )
            await ext_client.complete_task(task_id)
            return EventResponse.ok()
        case ProcessingStatus.CANCEL:
            await ext_client.log_task(
                task_id, severity=result.severity, error_message=result.message
            )
            return EventResponse.cancel()
        case ProcessingStatus.SKIP:
            await ext_client.log_task(
                task_id, severity=result.severity, error_message=result.message
            )
            return EventResponse.ok()


async def process_event(
    ext_ctx: ExtensionContext,
    event: Event,
    handler: EventHandler,
) -> EventResponse | None:
    """Run the task lifecycle of one event: claim the task, process the object, close the task."""
    logger.info("Event: %s", event)
    object_id = event.object.id
    task_id = event.task.id  # type: ignore
    if not await handler.claim_task(ext_ctx, task_id, object_id):
        return EventResponse.ok()

    try:
        processor = await handler.get_processor(object_id)
        result = await processor.process()
    except EventError as exc:
        logger.warning("%s: %s", object_id, exc)
        result = exc.to_result()

    return await apply_result(handler.ext_client, task_id, result)
