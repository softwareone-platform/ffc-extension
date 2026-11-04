from collections.abc import AsyncGenerator, Generator

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.activity_log.context import activity_actor, current_session
from app.db.models import ActivityLog, Organization, System
from tests.types import ActivityLogFetcher, ModelFactory


@pytest.fixture
def fetch_activity_logs(db_session: AsyncSession) -> ActivityLogFetcher:
    """Return the activity logs visible to the test session, oldest first, with their changes."""

    async def _fetch(action: str | None = None) -> list[ActivityLog]:
        query = (
            select(ActivityLog)
            .options(selectinload(ActivityLog.changes))
            .order_by(ActivityLog.timestamp, ActivityLog.id)
        )
        if action is not None:
            query = query.where(ActivityLog.action == action)
        result = await db_session.scalars(query)
        return list(result.all())

    return _fetch


@pytest.fixture
def sensitive_column() -> Generator[str]:
    """Flag `Organization.operations_external_id` as sensitive for the duration of the test."""
    column = Organization.__table__.c.operations_external_id
    column.info["sensitive"] = True
    yield "operations_external_id"
    column.info.pop("sensitive", None)


@pytest.fixture
async def acting_system(system_factory: ModelFactory[System]) -> AsyncGenerator[System]:
    """A System declared as the activity actor through the `activity_actor` context variable."""
    system = await system_factory()
    token = activity_actor.set(system.id)
    yield system
    activity_actor.reset(token)


@pytest.fixture
def no_current_session(db_session: AsyncSession) -> Generator[None]:
    """Hide the test session from the activity log, like a task that opened no session.

    Depends on `db_session` so it runs after the session has published itself.
    """
    token = current_session.set(None)
    yield
    current_session.reset(token)
