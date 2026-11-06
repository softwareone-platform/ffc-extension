from collections.abc import Generator

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.handlers import ClientAccountHandler, OrganizationHandler
from app.db.models import ActivityLog, Organization
from tests.types import ActivityLogFetcher


@pytest.fixture
def fetch_activity_logs(db_session: AsyncSession) -> ActivityLogFetcher:
    """Return a coroutine that loads every activity log with its change records."""

    async def _fetch(action: str | None = None) -> list[ActivityLog]:
        query = (
            select(ActivityLog)
            .options(selectinload(ActivityLog.changes))
            .order_by(ActivityLog.timestamp, ActivityLog.id)
        )
        if action is not None:
            query = query.where(ActivityLog.action == action)
        return list((await db_session.scalars(query)).all())

    return _fetch


@pytest.fixture
def organization_handler(db_session: AsyncSession) -> OrganizationHandler:
    """An `OrganizationHandler` bound to the test session."""
    return OrganizationHandler(db_session)


@pytest.fixture
def client_account_handler(db_session: AsyncSession) -> ClientAccountHandler:
    """A `ClientAccountHandler` bound to the test session."""
    return ClientAccountHandler(db_session)


@pytest.fixture
def sensitive_column() -> Generator[str]:
    """Flag `Organization.operations_external_id` as sensitive for one test; yield its key."""
    column = Organization.__table__.c.operations_external_id
    column.info["sensitive"] = True
    yield "operations_external_id"
    column.info.pop("sensitive", None)
