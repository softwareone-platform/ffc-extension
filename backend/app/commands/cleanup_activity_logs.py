import asyncio
import logging
from datetime import UTC, datetime, timedelta
from typing import cast

import typer
from sqlalchemy import CursorResult, delete, select

from app.conf import Settings
from app.db.base import session_factory
from app.db.models import ActivityLog
from app.telemetry import capture_telemetry_cli_command

logger = logging.getLogger(__name__)


async def delete_batch(cutoff: datetime, batch_size: int) -> int:
    # Each batch runs in its own short transaction to avoid holding long locks.
    # Change records are removed by the database-level ON DELETE CASCADE.
    batch_ids = (
        select(ActivityLog.id)
        .where(ActivityLog.timestamp < cutoff)
        .order_by(ActivityLog.timestamp)
        .limit(batch_size)
        .scalar_subquery()
    )
    async with session_factory.begin() as session:
        result = cast(
            CursorResult,
            await session.execute(
                delete(ActivityLog)
                .where(ActivityLog.id.in_(batch_ids))
                .execution_options(synchronize_session=False)
            ),
        )
    return result.rowcount


@capture_telemetry_cli_command(__name__, "Cleanup Activity Logs")
async def main(settings: Settings) -> None:
    retention_days = settings.activity_log_retention_days
    batch_size = settings.activity_log_cleanup_batch_size
    cutoff = datetime.now(UTC) - timedelta(days=retention_days)

    logger.info(
        "Deleting activity log entries older than %s (retention period: %d days)",
        cutoff.isoformat(),
        retention_days,
    )

    total_deleted = 0
    try:
        while True:
            deleted = await delete_batch(cutoff, batch_size)
            total_deleted += deleted
            if deleted:
                logger.debug("Deleted a batch of %d activity log entries", deleted)
            if deleted < batch_size:
                break
    except Exception:
        logger.exception(
            "Failed to delete activity log entries older than %s, "
            "%d entries were deleted before the failure",
            cutoff.isoformat(),
            total_deleted,
        )
        raise

    logger.info(
        "%d activity log entries older than %s have been deleted",
        total_deleted,
        cutoff.isoformat(),
    )


def command(ctx: typer.Context) -> None:
    """
    Delete activity log entries (and their change records) older than the
    configured retention period.
    """
    asyncio.run(main(ctx.obj))
