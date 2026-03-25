import asyncio
import logging
from datetime import UTC, datetime

import typer
from dateutil.relativedelta import relativedelta  # type: ignore[import-untyped]
from sqlalchemy import delete, func, select

from app.conf import Settings
from app.db.base import session_factory
from app.db.models import DatasourceExpense
from app.notifications import send_info
from app.telemetry import capture_telemetry_cli_command

logger = logging.getLogger(__name__)


@capture_telemetry_cli_command(__name__, "Cleanup Obsolete Datasource Expenses")
async def main(settings: Settings) -> None:
    async with session_factory.begin() as session:
        logger.info("Fetching obsolete datasource expenses from the database")

        threshold_date = datetime.now(UTC) - relativedelta(
            months=settings.datasources_expenses_obsolete_after_months
        )
        where_cond = DatasourceExpense.created_at < threshold_date

        num_obsolete_expenses = await session.scalar(
            select(func.count(DatasourceExpense.id)).where(where_cond)
        )

        logger.info("Found %d obsolete datasource expenses to delete", num_obsolete_expenses)

        if num_obsolete_expenses == 0:
            logger.info("No obsolete datasource expenses to delete")
            return

        logger.info(
            "Deleting %s obsolete datasource expenses from the database", num_obsolete_expenses
        )

        result = await session.execute(delete(DatasourceExpense).where(where_cond))

        message = (
            f"{result.rowcount} obsolete (older than "
            f"{threshold_date.isoformat()}) datasource expenses have been deleted."
        )

        logger.info(message)
        if result.rowcount > 0:
            await send_info("Cleanup Obsolete Datasource Expenses Success", message)


def command(ctx: typer.Context) -> None:
    """
    Delete all datasource expenses older than 6 months from the database.
    """
    logger.info("Starting command function")
    asyncio.run(main(ctx.obj))
    logger.info("Completed command function")
