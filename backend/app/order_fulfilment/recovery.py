import logging
from datetime import UTC, date, datetime
from typing import Any

from app.api_clients.mpt import MPTClient
from app.order_fulfilment.error import ERR_DUE_DATE_IS_REACHED
from app.parameters import (
    get_due_date,
)
from app.schemas.core import EventResponse

logger = logging.getLogger(__name__)


async def handle_exception(
    exc: Exception, ext_client: MPTClient, order: dict[str, Any], order_id: str, task_id: str
) -> EventResponse:
    logger.exception("Unexpected error processing order %s: %s", order_id, exc)
    due_date: date | None = get_due_date(order) if order else None
    if due_date is None:
        try:
            await ext_client.fail_order(
                order_id=order_id, payload={"description": "due date is not set"}
            )

            return EventResponse.cancel()
        except Exception as inn_exc:
            logger.exception(
                "Failed to fail order %s after missing due date: %s", order_id, inn_exc
            )
            return EventResponse.cancel()
    task = await ext_client.get_task(task_id)
    description = task.get("description", "")
    now = datetime.now(UTC).date()
    error_message = str(exc)
    if due_date and now < due_date:
        await ext_client.reschedule_task(
            task_id,
            payload={"description": f"{description} - {now.isoformat()} - {error_message}"},
        )
        return EventResponse.reschedule(seconds=300)
    logger.info(
        f"Switch order {order_id} to failed status. "
        f"Reason: due date is reached {due_date.strftime('%Y-%m-%d')}"
    )
    await ext_client.fail_order(
        order_id=order_id,
        payload=ERR_DUE_DATE_IS_REACHED.to_dict(due_date=due_date.strftime("%Y-%m-%d")),
    )

    await ext_client.complete_task(
        task_id,
        payload={"description": f"{description} - {now.isoformat()} - {error_message}"},
    )
    return EventResponse.ok()
