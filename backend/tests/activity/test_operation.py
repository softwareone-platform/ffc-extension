"""`ActivityOperation`: one entry for an activity made of several steps and attempts."""

import asyncio
import logging
from datetime import UTC, datetime

import pytest
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.activity import ActivityOperation, activity_recorder
from app.auth.context import AuthenticationContext
from app.db.base import session_factory
from app.db.constants import APP_ACTOR_ID
from app.db.handlers import OrganizationHandler
from app.db.models import Organization, System, User
from app.enums import ActivityStatus
from tests.types import ActivityLogFetcher, ModelFactory

KEY = "order:ORD-1234-5678-9012"
ACTION = "order.purchase"
MESSAGE = "Purchase order ORD-1234-5678-9012"


# ---------------------------------------------------------------------------
# The entry: found by key while in progress, created otherwise
# ---------------------------------------------------------------------------


async def test_one_attempt_with_two_steps_gives_one_entry_with_both_steps_records(
    db_session: AsyncSession,
    organization_factory: ModelFactory[Organization],
    organization_handler: OrganizationHandler,
    fetch_operation_entries: ActivityLogFetcher,
) -> None:
    """Both steps of one attempt append their records, in order, to one in-progress entry."""
    first = await organization_factory(name="First", operations_external_id="ORG-1")
    second = await organization_factory(name="Second", operations_external_id="ORG-2")
    operation = ActivityOperation(db_session, KEY, ACTION, MESSAGE)

    async with operation.attempt():
        async with operation.step():
            await organization_handler.update(first, {"name": "First renamed"})
        async with operation.step():
            await organization_handler.update(second, {"name": "Second renamed"})

    (entry,) = await fetch_operation_entries(KEY)
    assert entry.status == ActivityStatus.IN_PROGRESS
    assert entry.action == ACTION
    assert entry.message == MESSAGE
    assert [change.object_id for change in entry.changes] == [first.id, second.id]
    assert entry.changes[0].recorded_at < entry.changes[1].recorded_at
    assert entry.notes == []


async def test_two_attempts_in_two_transactions_share_one_entry(
    db_session: AsyncSession,
    organization_factory: ModelFactory[Organization],
    organization_handler: OrganizationHandler,
    fetch_operation_entries: ActivityLogFetcher,
) -> None:
    """A second attempt, in a later transaction, appends to the entry of the first one."""
    organization = await organization_factory(name="Old name")
    first_attempt = ActivityOperation(db_session, KEY, ACTION, MESSAGE)
    async with first_attempt.attempt(), first_attempt.step():
        await organization_handler.update(organization, {"name": "Interim name"})
    await db_session.commit()

    second_attempt = ActivityOperation(db_session, KEY, ACTION, MESSAGE)
    async with second_attempt.attempt():
        async with second_attempt.step():
            pass  # changes nothing
        async with second_attempt.step():
            await organization_handler.update(organization, {"name": "New name"})
    await db_session.commit()

    (entry,) = await fetch_operation_entries(KEY)
    assert [(change.before or {})["name"] for change in entry.changes] == [
        "Old name",
        "Interim name",
    ]
    assert [(change.after or {})["name"] for change in entry.changes] == [
        "Interim name",
        "New name",
    ]


async def test_complete_sets_status_message_actor_time_and_final_note(
    db_session: AsyncSession,
    ffc_extension: System,
    fetch_operation_entries: ActivityLogFetcher,
) -> None:
    """`complete()` closes the entry as the current actor and notes the completion."""
    operation = ActivityOperation(db_session, KEY, ACTION, MESSAGE)
    async with operation.attempt():
        pass
    (entry,) = await fetch_operation_entries(KEY)
    started_at = entry.recorded_at

    finisher = ActivityOperation(db_session, KEY, ACTION, MESSAGE, actor_id=ffc_extension.id)
    await finisher.complete("Order ORD-1234-5678-9012 completed")

    (entry,) = await fetch_operation_entries(KEY)
    assert entry.status == ActivityStatus.COMPLETED
    assert entry.message == "Order ORD-1234-5678-9012 completed"
    assert entry.recorded_by_id == ffc_extension.id
    assert entry.recorded_at > started_at
    assert [(note.message, note.recorded_by_id) for note in entry.notes] == [
        ("Completed.", ffc_extension.id)
    ]


@pytest.mark.parametrize("close", ["complete", "abandon"])
async def test_a_closed_operation_key_starts_a_new_entry(
    db_session: AsyncSession, fetch_operation_entries: ActivityLogFetcher, close: str
) -> None:
    """After `complete()` or `abandon()`, a new operation with the same key gets a new entry."""
    finished = ActivityOperation(db_session, KEY, ACTION, MESSAGE)
    await getattr(finished, close)("Closed")

    restarted = ActivityOperation(db_session, KEY, ACTION, MESSAGE)
    async with restarted.attempt():
        pass

    older, newer = await fetch_operation_entries(KEY)
    assert older.status != ActivityStatus.IN_PROGRESS
    assert newer.status == ActivityStatus.IN_PROGRESS
    assert older.id != newer.id


async def test_abandon_without_a_prior_entry_creates_an_abandoned_one(
    db_session: AsyncSession, fetch_operation_entries: ActivityLogFetcher
) -> None:
    """`abandon()` on an operation that never started still leaves an abandoned entry."""
    operation = ActivityOperation(db_session, KEY, ACTION, MESSAGE)

    await operation.abandon("Order cancelled by the client")

    (entry,) = await fetch_operation_entries(KEY)
    assert entry.status == ActivityStatus.ABANDONED
    assert entry.message == MESSAGE
    assert [note.message for note in entry.notes] == ["Order cancelled by the client"]


@pytest.mark.parametrize("close_again", ["complete", "abandon"])
async def test_closing_an_entry_that_is_already_final_does_nothing(
    db_session: AsyncSession,
    ffc_extension: System,
    fetch_operation_entries: ActivityLogFetcher,
    close_again: str,
) -> None:
    """`complete()` and `abandon()` leave a completed entry and its notes untouched."""
    operation = ActivityOperation(db_session, KEY, ACTION, MESSAGE)
    await operation.complete("Done")

    operation.actor_id = ffc_extension.id
    await getattr(operation, close_again)("Too late")

    (entry,) = await fetch_operation_entries(KEY)
    assert entry.status == ActivityStatus.COMPLETED
    assert entry.message == "Done"
    assert entry.recorded_by_id == APP_ACTOR_ID
    assert [note.message for note in entry.notes] == ["Completed."]


async def test_operation_requires_a_message(db_session: AsyncSession) -> None:
    """An operation cannot be created with a blank message."""
    with pytest.raises(ValueError, match="needs a message"):
        ActivityOperation(db_session, KEY, ACTION, "  ")


async def test_entry_that_cannot_be_created_raises(
    db_session: AsyncSession, fetch_operation_entries: ActivityLogFetcher
) -> None:
    """A failed insert that is not a concurrent attempt (here an unknown actor) is raised."""
    operation = ActivityOperation(db_session, KEY, ACTION, MESSAGE, actor_id="FUSR-0000-0000")

    with pytest.raises(IntegrityError):
        await operation.note("Never written")

    assert await fetch_operation_entries(KEY) == []


# ---------------------------------------------------------------------------
# Actor rule: the entry follows its latest update, notes keep their author
# ---------------------------------------------------------------------------


async def test_entry_actor_is_the_one_of_the_latest_update(
    db_session: AsyncSession,
    user_factory: ModelFactory[User],
    fetch_operation_entries: ActivityLogFetcher,
) -> None:
    """Started and failed by A, then completed by B: the entry is B's, each note its author's."""
    jane = await user_factory(name="Jane Doe")
    joe = await user_factory(name="Joe Bloggs")
    by_jane = ActivityOperation(db_session, KEY, ACTION, MESSAGE, actor_id=jane.id)
    with pytest.raises(RuntimeError):
        async with by_jane.attempt():
            raise RuntimeError("datasource not ready")
    (entry,) = await fetch_operation_entries(KEY)
    assert entry.recorded_by_id == jane.id

    by_joe = ActivityOperation(db_session, KEY, ACTION, MESSAGE, actor_id=joe.id)
    async with by_joe.attempt():
        (entry,) = await fetch_operation_entries(KEY)
        assert entry.recorded_by_id == joe.id
        await by_joe.complete("Order completed")

    (entry,) = await fetch_operation_entries(KEY)
    assert entry.recorded_by_id == joe.id
    assert entry.action == ACTION
    assert [(note.message, note.recorded_by_id) for note in entry.notes] == [
        ("Attempt failed: RuntimeError: datasource not ready", jane.id),
        ("Completed.", joe.id),
    ]


async def test_actor_defaults_to_the_one_of_the_current_request(
    db_session: AsyncSession,
    ffc_extension_auth_context: AuthenticationContext,
    ffc_extension: System,
    fetch_operation_entries: ActivityLogFetcher,
) -> None:
    """Without `actor_id`, the entry and its notes belong to the authenticated actor."""
    operation = ActivityOperation(db_session, KEY, ACTION, MESSAGE)

    await operation.note("Waiting for the datasource")

    (entry,) = await fetch_operation_entries(KEY)
    assert entry.recorded_by_id == ffc_extension.id
    assert [note.recorded_by_id for note in entry.notes] == [ffc_extension.id]


# ---------------------------------------------------------------------------
# attempt(): a failure is noted and re-raised, and never changes the status
# ---------------------------------------------------------------------------


async def test_failing_attempt_adds_a_note_and_reraises_the_same_exception(
    db_session: AsyncSession, fetch_operation_entries: ActivityLogFetcher
) -> None:
    """A failed attempt leaves a failure note and the entry in progress."""
    operation = ActivityOperation(db_session, KEY, ACTION, MESSAGE)
    failure = RuntimeError("502 Bad Gateway")

    with pytest.raises(RuntimeError) as raised:
        async with operation.attempt():
            raise failure

    assert raised.value is failure
    (entry,) = await fetch_operation_entries(KEY)
    assert entry.status == ActivityStatus.IN_PROGRESS
    (note,) = entry.notes
    assert note.message == "Attempt failed: RuntimeError: 502 Bad Gateway"
    assert note.recorded_by_id == APP_ACTOR_ID
    assert note.recorded_at.tzinfo == UTC


async def test_failure_note_of_an_http_exception_carries_its_detail(
    db_session: AsyncSession, fetch_operation_entries: ActivityLogFetcher
) -> None:
    """For an `HTTPException` the note holds the detail returned to the client."""
    operation = ActivityOperation(db_session, KEY, ACTION, MESSAGE)

    with pytest.raises(HTTPException):
        async with operation.attempt():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="The user is already an admin."
            )

    (entry,) = await fetch_operation_entries(KEY)
    assert [note.message for note in entry.notes] == [
        "Attempt failed: The user is already an admin."
    ]


async def test_failure_detail_is_cut_to_500_characters(
    db_session: AsyncSession, fetch_operation_entries: ActivityLogFetcher
) -> None:
    """A long failure detail is truncated, so a note never carries a whole payload."""
    operation = ActivityOperation(db_session, KEY, ACTION, MESSAGE)

    with pytest.raises(HTTPException):
        async with operation.attempt():
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="x" * 600)

    (entry,) = await fetch_operation_entries(KEY)
    assert [note.message for note in entry.notes] == ["Attempt failed: " + "x" * 500]


async def test_failure_after_complete_is_noted_without_changing_the_status(
    db_session: AsyncSession, fetch_operation_entries: ActivityLogFetcher
) -> None:
    """A failure is noted whatever the status, and the status stays as it was."""
    operation = ActivityOperation(db_session, KEY, ACTION, MESSAGE)

    async def complete_then_fail() -> None:
        async with operation.attempt():
            await operation.complete("Done")
            raise RuntimeError("notification not sent")

    with pytest.raises(RuntimeError):
        await complete_then_fail()

    (entry,) = await fetch_operation_entries(KEY)
    assert entry.status == ActivityStatus.COMPLETED
    assert [note.message for note in entry.notes] == [
        "Completed.",
        "Attempt failed: RuntimeError: notification not sent",
    ]


async def test_original_exception_is_raised_when_the_failure_note_cannot_be_written(
    db_session: AsyncSession,
    fetch_operation_entries: ActivityLogFetcher,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A failure note that cannot be written is logged; the attempt's own error still wins."""
    operation = ActivityOperation(db_session, KEY, ACTION, MESSAGE, durable=True)
    failure = RuntimeError("502 Bad Gateway")

    async def fail_with_an_unknown_actor() -> None:
        async with operation.attempt():
            operation.actor_id = "FUSR-0000-0000"  # unknown actor: the note violates its FK
            raise failure

    with caplog.at_level(logging.ERROR), pytest.raises(RuntimeError) as raised:
        await fail_with_an_unknown_actor()

    assert raised.value is failure
    assert "Could not add the failure note" in caplog.text
    (entry,) = await fetch_operation_entries(KEY)
    assert entry.notes == []


async def test_clean_attempt_leaves_the_entry_in_progress(
    db_session: AsyncSession, fetch_operation_entries: ActivityLogFetcher
) -> None:
    """Leaving an attempt without error does not complete the operation."""
    operation = ActivityOperation(db_session, KEY, ACTION, MESSAGE)

    async with operation.attempt():
        pass

    (entry,) = await fetch_operation_entries(KEY)
    assert entry.status == ActivityStatus.IN_PROGRESS
    assert entry.notes == []


# ---------------------------------------------------------------------------
# step(): an atomic recorder block that appends to the entry
# ---------------------------------------------------------------------------


async def test_step_without_a_prior_attempt_creates_the_entry(
    db_session: AsyncSession,
    organization_factory: ModelFactory[Organization],
    organization_handler: OrganizationHandler,
    fetch_operation_entries: ActivityLogFetcher,
) -> None:
    """A step used on its own creates the entry its records belong to."""
    organization = await organization_factory(name="Old name")
    operation = ActivityOperation(db_session, KEY, ACTION, MESSAGE)

    async with operation.step():
        await organization_handler.update(organization, {"name": "New name"})

    (entry,) = await fetch_operation_entries(KEY)
    (change,) = entry.changes
    assert change.object_id == organization.id


async def test_step_that_changes_nothing_adds_nothing(
    db_session: AsyncSession, fetch_operation_entries: ActivityLogFetcher
) -> None:
    """A step with no change writes no record, and does not even create the entry."""
    operation = ActivityOperation(db_session, KEY, ACTION, MESSAGE)

    async with operation.step():
        pass

    assert await fetch_operation_entries(KEY) == []


async def test_step_that_raises_rolls_back_its_rows_and_records(
    db_session: AsyncSession,
    organization_factory: ModelFactory[Organization],
    organization_handler: OrganizationHandler,
    fetch_operation_entries: ActivityLogFetcher,
) -> None:
    """A failing step leaves neither its rows nor change records; earlier steps are kept."""
    kept = await organization_factory(name="Kept", operations_external_id="ORG-1")
    dropped = await organization_factory(name="Dropped", operations_external_id="ORG-2")
    operation = ActivityOperation(db_session, KEY, ACTION, MESSAGE)

    async def second_step_fails() -> None:
        async with operation.attempt():
            async with operation.step():
                await organization_handler.update(kept, {"name": "Kept renamed"})
            async with operation.step():
                await organization_handler.update(dropped, {"name": "Dropped renamed"})
                raise RuntimeError("boom")

    with pytest.raises(RuntimeError):
        await second_step_fails()

    await db_session.refresh(dropped)
    assert dropped.name == "Dropped"
    (entry,) = await fetch_operation_entries(KEY)
    assert [change.object_id for change in entry.changes] == [kept.id]


async def test_step_inside_an_open_recorder_gives_its_changes_to_that_recorder(
    db_session: AsyncSession,
    organization_factory: ModelFactory[Organization],
    organization_handler: OrganizationHandler,
    fetch_activity_logs: ActivityLogFetcher,
    fetch_operation_entries: ActivityLogFetcher,
) -> None:
    """A step opened in another recorder block is a child: the outer entry gets its changes."""
    organization = await organization_factory(name="Old name")
    operation = ActivityOperation(db_session, KEY, ACTION, MESSAGE)

    async with activity_recorder(db_session, "organization.updated", "Organization renamed"):
        async with operation.step():
            await organization_handler.update(organization, {"name": "New name"})

    (outer,) = await fetch_activity_logs("organization.updated")
    assert [change.object_id for change in outer.changes] == [organization.id]
    assert await fetch_operation_entries(KEY) == []


# ---------------------------------------------------------------------------
# note()
# ---------------------------------------------------------------------------


async def test_note_is_added_to_the_entry_by_the_current_actor(
    db_session: AsyncSession,
    ffc_extension: System,
    fetch_operation_entries: ActivityLogFetcher,
) -> None:
    """`note()` appends a remark, stamped with the actor and the current UTC time."""
    operation = ActivityOperation(db_session, KEY, ACTION, MESSAGE, actor_id=ffc_extension.id)
    before = datetime.now(UTC)

    async with operation.attempt():
        await operation.note("Waiting for the datasource")
        await operation.note("Datasource created")

    (entry,) = await fetch_operation_entries(KEY)
    assert [note.message for note in entry.notes] == [
        "Waiting for the datasource",
        "Datasource created",
    ]
    assert all(note.recorded_by_id == ffc_extension.id for note in entry.notes)
    assert all(before <= note.recorded_at <= datetime.now(UTC) for note in entry.notes)


# ---------------------------------------------------------------------------
# Durable mode: entry, attempt update and notes are committed on their own
# ---------------------------------------------------------------------------


async def test_durable_operation_records_like_a_plain_one(
    db_session: AsyncSession,
    organization_factory: ModelFactory[Organization],
    organization_handler: OrganizationHandler,
    user_factory: ModelFactory[User],
    fetch_operation_entries: ActivityLogFetcher,
) -> None:
    """In durable mode two attempts still give one entry, owned by the latest actor."""
    organization = await organization_factory(name="Old name")
    jane = await user_factory(name="Jane Doe")
    joe = await user_factory(name="Joe Bloggs")
    by_jane = ActivityOperation(db_session, KEY, ACTION, MESSAGE, actor_id=jane.id, durable=True)
    async with by_jane.attempt():
        await by_jane.note("Waiting for the datasource")

    by_joe = ActivityOperation(db_session, KEY, ACTION, MESSAGE, actor_id=joe.id, durable=True)
    async with by_joe.attempt():
        async with by_joe.step():
            await organization_handler.update(organization, {"name": "New name"})
        await by_joe.complete("Order completed")

    (entry,) = await fetch_operation_entries(KEY)
    assert entry.status == ActivityStatus.COMPLETED
    assert entry.recorded_by_id == joe.id
    assert [change.object_id for change in entry.changes] == [organization.id]
    assert [(note.message, note.recorded_by_id) for note in entry.notes] == [
        ("Waiting for the datasource", jane.id),
        ("Completed.", joe.id),
    ]


async def test_durable_attempt_raises_database_errors_other_than_a_locked_entry(
    db_session: AsyncSession, fetch_operation_entries: ActivityLogFetcher
) -> None:
    """Only a locked entry is skipped at attempt start; any other database error is raised."""
    starter = ActivityOperation(db_session, KEY, ACTION, MESSAGE, durable=True)
    async with starter.attempt():
        pass

    unknown_actor = ActivityOperation(
        db_session, KEY, ACTION, MESSAGE, actor_id="FUSR-0000-0000", durable=True
    )
    with pytest.raises(IntegrityError):
        async with unknown_actor.attempt():
            pass

    (entry,) = await fetch_operation_entries(KEY)
    assert entry.recorded_by_id == APP_ACTOR_ID


@pytest.mark.transactional_db
async def test_durable_entry_and_notes_survive_a_rollback_of_the_request(
    db_session: AsyncSession,
    organization_factory: ModelFactory[Organization],
    organization_handler: OrganizationHandler,
    fetch_operation_entries: ActivityLogFetcher,
) -> None:
    """When the request rolls back, the entry and notes stay; records and completion do not."""
    organization = await organization_factory(name="Old name")
    operation = ActivityOperation(db_session, KEY, ACTION, MESSAGE, durable=True)

    async def request_that_fails() -> None:
        async with operation.attempt():
            async with operation.step():
                await organization_handler.update(organization, {"name": "New name"})
            await operation.note("Datasource created in FinOps for Cloud")
            await operation.complete("Order completed")
            raise RuntimeError("502 Bad Gateway")

    with pytest.raises(RuntimeError):
        await request_that_fails()
    await db_session.rollback()

    (entry,) = await fetch_operation_entries(KEY)
    assert entry.status == ActivityStatus.IN_PROGRESS
    assert entry.message == MESSAGE
    assert entry.changes == []
    assert [note.message for note in entry.notes] == [
        "Datasource created in FinOps for Cloud",
        "Attempt failed: RuntimeError: 502 Bad Gateway",
    ]
    await db_session.refresh(organization)
    assert organization.name == "Old name"


@pytest.mark.transactional_db
async def test_durable_note_does_not_wait_for_the_request_that_updated_the_entry(
    db_session: AsyncSession, fetch_operation_entries: ActivityLogFetcher
) -> None:
    """A durable note is committed at once even while the request holds the entry's row."""
    operation = ActivityOperation(db_session, KEY, ACTION, MESSAGE, durable=True)
    await operation.complete("Order completed")  # not committed: the entry's row is locked

    await asyncio.wait_for(operation.note("Notification sent"), timeout=5)
    await db_session.rollback()

    (entry,) = await fetch_operation_entries(KEY)
    assert entry.status == ActivityStatus.IN_PROGRESS
    assert [note.message for note in entry.notes] == ["Notification sent"]


@pytest.mark.transactional_db
async def test_durable_attempt_goes_ahead_when_the_entry_is_locked(
    db_session: AsyncSession,
    fetch_operation_entries: ActivityLogFetcher,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """An attempt that finds the entry locked skips the actor update, warns, and still runs."""
    holder = ActivityOperation(db_session, KEY, ACTION, MESSAGE, durable=True)
    await holder.complete("Order completed")  # not committed: the entry's row is locked
    ran = False

    async with session_factory() as other_session:
        retry = ActivityOperation(other_session, KEY, ACTION, MESSAGE, durable=True)
        with caplog.at_level(logging.WARNING):
            async with asyncio.timeout(5), retry.attempt():
                ran = True
    await db_session.rollback()

    assert ran
    assert "is locked" in caplog.text
    (entry,) = await fetch_operation_entries(KEY)
    assert entry.status == ActivityStatus.IN_PROGRESS


@pytest.mark.transactional_db
async def test_concurrent_attempts_with_the_same_key_share_one_entry(
    db_session: AsyncSession, fetch_operation_entries: ActivityLogFetcher
) -> None:
    """The attempt that loses the race to create the entry reuses the winner's."""
    winner = ActivityOperation(db_session, KEY, ACTION, MESSAGE)
    await winner.note("First attempt")  # entry inserted, not committed yet

    async def second_attempt() -> None:
        async with session_factory() as other_session:
            loser = ActivityOperation(other_session, KEY, ACTION, MESSAGE)
            async with loser.attempt():
                await loser.note("Second attempt")
            await other_session.commit()

    # The second attempt does not see the entry, tries to create it, and waits on the
    # unique index until the first one commits.
    task = asyncio.create_task(second_attempt())
    await asyncio.sleep(0.5)
    await db_session.commit()
    await asyncio.wait_for(task, timeout=5)

    (entry,) = await fetch_operation_entries(KEY)
    assert [note.message for note in entry.notes] == ["First attempt", "Second attempt"]
