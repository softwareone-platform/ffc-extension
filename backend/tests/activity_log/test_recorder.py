import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.activity_log import record_activity
from app.db.models import Organization, System
from tests.types import ActivityLogFetcher, ModelFactory


async def test_record_activity_replaces_the_automatic_action_and_message(
    db_session: AsyncSession,
    organization_factory: ModelFactory[Organization],
    fetch_activity_logs: ActivityLogFetcher,
) -> None:
    """An explicit `record_activity()` names the entry but keeps the automatic change records."""
    organization = await organization_factory(name="Apple")
    organization.name = "Apple Inc."

    record_activity("organization.renamed", "Organization renamed on request of the client")
    await db_session.commit()

    (entry,) = await fetch_activity_logs("organization.renamed")
    assert entry.message == "Organization renamed on request of the client"
    (change,) = entry.changes
    assert change.object_id == organization.id
    assert change.before is not None
    assert change.after is not None
    assert change.before["name"] == "Apple"
    assert change.after["name"] == "Apple Inc."


async def test_record_activity_puts_explicit_change_records_first(
    db_session: AsyncSession,
    organization_factory: ModelFactory[Organization],
    fetch_activity_logs: ActivityLogFetcher,
) -> None:
    """Explicitly listed changes come first with their own before image; the rest are appended."""
    automatic = await organization_factory(operations_external_id="AGR-0000-0000-0001")
    explicit = await organization_factory(operations_external_id="AGR-0000-0000-0002")
    automatic.name = "Automatic"
    explicit.name = "Explicit"

    record_activity("bulk.rename", "Bulk rename", changes=[(explicit, {"name": "Custom before"})])
    await db_session.commit()

    (entry,) = await fetch_activity_logs("bulk.rename")
    assert [change.object_id for change in entry.changes] == [explicit.id, automatic.id]
    assert entry.changes[0].before == {"name": "Custom before"}


async def test_record_activity_overrides_the_actor(
    db_session: AsyncSession,
    organization_factory: ModelFactory[Organization],
    system_factory: ModelFactory[System],
    fetch_activity_logs: ActivityLogFetcher,
) -> None:
    """An actor passed to `record_activity()` wins over the resolved one."""
    system = await system_factory()
    organization = await organization_factory()
    organization.name = "Renamed"

    record_activity("organization.renamed", "Renamed", actor_id=system.id)
    await db_session.commit()

    (entry,) = await fetch_activity_logs("organization.renamed")
    assert entry.actor_id == system.id


async def test_record_activity_alone_records_an_entry_without_change_records(
    db_session: AsyncSession, fetch_activity_logs: ActivityLogFetcher
) -> None:
    """`record_activity()` with no DB change still commits an entry, with no change records."""
    record_activity("support.note", "Manual note")
    await db_session.commit()

    (entry,) = await fetch_activity_logs("support.note")
    assert entry.changes == []


async def test_record_activity_requires_an_open_session(no_current_session: None) -> None:
    """`record_activity()` refuses to run when no session is open in the current task."""
    with pytest.raises(RuntimeError, match="requires an open database session"):
        record_activity("support.note", "Manual note")
