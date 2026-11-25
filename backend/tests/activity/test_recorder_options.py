"""Options of `ActivityRecorder`: `actor_id`, `skip_if_unchanged`, `atomic`, late description,
and the `system_activity_recorder` helper that combines them for events and jobs."""

from contextlib import suppress
from decimal import Decimal

import pytest
from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.activity import ActivityRecorder, activity_recorder, system_activity_recorder
from app.auth.context import AuthenticationContext
from app.db.constants import APP_ACTOR_ID
from app.db.handlers import OrganizationHandler
from app.db.models import DatasourceExpense, Organization, System
from app.enums import DatasourceType
from tests.types import ActivityLogFetcher, ModelFactory


def new_organization(external_id: str) -> Organization:
    return Organization(
        name=f"Org {external_id}",
        currency="EUR",
        billing_currency="USD",
        operations_external_id=external_id,
    )


async def count_organizations(db_session: AsyncSession) -> int:
    return await db_session.scalar(select(func.count()).select_from(Organization)) or 0


# ---------------------------------------------------------------------------
# actor_id: an explicit actor wins over the request's; a child's is ignored
# ---------------------------------------------------------------------------


async def test_actor_id_overrides_the_actor_of_the_current_request(
    db_session: AsyncSession,
    ffc_extension_auth_context: AuthenticationContext,
    fetch_activity_logs: ActivityLogFetcher,
) -> None:
    """A root recorder given `actor_id` records that actor even inside an authenticated request."""
    async with activity_recorder(
        db_session, "entitlement.terminated", "Entitlement terminated", actor_id=APP_ACTOR_ID
    ):
        pass

    (entry,) = await fetch_activity_logs()
    assert entry.recorded_by_id == APP_ACTOR_ID


async def test_actor_id_is_used_when_nobody_is_authenticated(
    db_session: AsyncSession, ffc_extension: System, fetch_activity_logs: ActivityLogFetcher
) -> None:
    """Outside a request, `actor_id` replaces the fallback to the application."""
    async with activity_recorder(
        db_session, "entitlement.terminated", "Entitlement terminated", actor_id=ffc_extension.id
    ):
        pass

    (entry,) = await fetch_activity_logs()
    assert entry.recorded_by_id == ffc_extension.id


async def test_actor_id_of_a_child_recorder_is_ignored(
    db_session: AsyncSession,
    ffc_extension_auth_context: AuthenticationContext,
    ffc_extension: System,
    fetch_activity_logs: ActivityLogFetcher,
) -> None:
    """Like its action and message, a child's `actor_id` does not reach the root's entry."""
    async with activity_recorder(db_session, "organization.terminated", "Organization terminated"):
        async with activity_recorder(
            db_session, "optscale.tag.deleted", "Tag T-1 deleted", actor_id=APP_ACTOR_ID
        ):
            pass

    (entry,) = await fetch_activity_logs()
    assert entry.recorded_by_id == ffc_extension.id


# ---------------------------------------------------------------------------
# skip_if_unchanged: no change records, no entry
# ---------------------------------------------------------------------------


async def test_skip_if_unchanged_writes_no_entry_when_the_block_changes_nothing(
    db_session: AsyncSession, fetch_activity_logs: ActivityLogFetcher
) -> None:
    """With `skip_if_unchanged`, a block that touches no row leaves the activity log untouched."""
    async with activity_recorder(
        db_session, "subscriptions.synced", "Subscriptions synced", skip_if_unchanged=True
    ):
        pass

    assert await fetch_activity_logs() == []


async def test_skip_if_unchanged_still_writes_an_entry_when_rows_changed(
    db_session: AsyncSession,
    organization_factory: ModelFactory[Organization],
    organization_handler: OrganizationHandler,
    fetch_activity_logs: ActivityLogFetcher,
) -> None:
    """With `skip_if_unchanged`, a block that changes a row writes one entry as usual."""
    organization = await organization_factory(name="Old name")

    async with activity_recorder(
        db_session, "organization.updated", "Organization renamed", skip_if_unchanged=True
    ):
        await organization_handler.update(organization, {"name": "New name"})

    (entry,) = await fetch_activity_logs()
    (change,) = entry.changes
    assert change.after is not None
    assert change.after["name"] == "New name"


# ---------------------------------------------------------------------------
# atomic: a failing block leaves neither rows nor entry behind
# ---------------------------------------------------------------------------


async def test_atomic_block_that_raises_rolls_back_its_rows_and_propagates(
    db_session: AsyncSession,
    organization_factory: ModelFactory[Organization],
    organization_handler: OrganizationHandler,
    fetch_activity_logs: ActivityLogFetcher,
) -> None:
    """Rows flushed inside a failing atomic block are discarded with the entry."""
    organization = await organization_factory(name="Old name")
    organizations_before = await count_organizations(db_session)

    async def failing_activity() -> None:
        async with activity_recorder(
            db_session, "organization.updated", "Organization updated", atomic=True
        ):
            await organization_handler.update(organization, {"name": "New name"})
            await organization_handler.create(new_organization("AGR-NEW"))
            raise RuntimeError("external call failed")

    with pytest.raises(RuntimeError, match="external call failed"):
        await failing_activity()

    assert await fetch_activity_logs() == []
    await db_session.refresh(organization)
    assert organization.name == "Old name"
    assert await count_organizations(db_session) == organizations_before


async def test_outer_transaction_stays_usable_after_a_failed_atomic_block(
    db_session: AsyncSession,
    organization_factory: ModelFactory[Organization],
    organization_handler: OrganizationHandler,
    fetch_activity_logs: ActivityLogFetcher,
) -> None:
    """After the savepoint is rolled back, the transaction accepts further work and entries."""
    organization = await organization_factory(name="Old name")

    with suppress(RuntimeError):
        async with activity_recorder(
            db_session, "organization.updated", "Organization updated", atomic=True
        ):
            await organization_handler.update(organization, {"name": "Lost"})
            raise RuntimeError("step failed")

    async with activity_recorder(db_session, "organization.updated", "Organization renamed"):
        await organization_handler.update(organization, {"name": "New name"})

    (entry,) = await fetch_activity_logs()
    (change,) = entry.changes
    assert entry.message == "Organization renamed"
    assert change.before is not None
    assert change.before["name"] == "Old name"
    assert change.after is not None
    assert change.after["name"] == "New name"


async def test_atomic_block_survives_a_database_error_raised_by_a_flush(
    db_session: AsyncSession,
    organization_factory: ModelFactory[Organization],
    organization_handler: OrganizationHandler,
    fetch_activity_logs: ActivityLogFetcher,
) -> None:
    """A flush failing inside the block already rolled the savepoint back; the recorder copes
    and the transaction can go on."""
    organization = await organization_factory(name="Old name")

    async def failing_activity() -> None:
        async with activity_recorder(
            db_session, "organization.created", "Organization created", atomic=True
        ):
            await organization_handler.update(organization, {"name": "Lost"})
            # Violates the unique index on `operations_external_id` of active organizations.
            db_session.add(new_organization(organization.operations_external_id))
            await db_session.flush()

    with pytest.raises(IntegrityError):
        await failing_activity()

    assert await fetch_activity_logs() == []
    await db_session.refresh(organization)
    assert organization.name == "Old name"
    await organization_handler.update(organization, {"name": "New name"})
    await db_session.refresh(organization)
    assert organization.name == "New name"


async def test_atomic_block_that_succeeds_keeps_its_rows_and_entry(
    db_session: AsyncSession,
    organization_factory: ModelFactory[Organization],
    organization_handler: OrganizationHandler,
    fetch_activity_logs: ActivityLogFetcher,
) -> None:
    """On success the savepoint is released: rows and entry are part of the transaction."""
    organization = await organization_factory(name="Old name")

    async with activity_recorder(
        db_session, "organization.updated", "Organization renamed", atomic=True
    ):
        await organization_handler.update(organization, {"name": "New name"})

    (entry,) = await fetch_activity_logs()
    (change,) = entry.changes
    assert change.after is not None
    assert change.after["name"] == "New name"
    assert not db_session.in_nested_transaction()
    await db_session.refresh(organization)
    assert organization.name == "New name"


async def test_rows_pending_before_an_atomic_block_are_not_rolled_back_with_it(
    db_session: AsyncSession,
    organization_factory: ModelFactory[Organization],
    fetch_activity_logs: ActivityLogFetcher,
) -> None:
    """Work left pending before the block is flushed first, so the savepoint does not cover it."""
    organization = await organization_factory(name="Old name")
    organization.name = "Before the block"

    with suppress(RuntimeError):
        async with activity_recorder(
            db_session, "organization.updated", "Organization updated", atomic=True
        ):
            raise RuntimeError("step failed")

    await db_session.refresh(organization)
    assert organization.name == "Before the block"
    assert await fetch_activity_logs() == []


async def test_failing_atomic_child_drops_its_rows_and_the_root_records_its_own(
    db_session: AsyncSession,
    organization_factory: ModelFactory[Organization],
    organization_handler: OrganizationHandler,
    fetch_activity_logs: ActivityLogFetcher,
) -> None:
    """A child's savepoint rolls back only the child's rows; the root entry has the rest."""
    first = await organization_factory(name="First", operations_external_id="AGR-1")
    second = await organization_factory(name="Second", operations_external_id="AGR-2")
    organizations_before = await count_organizations(db_session)

    async with activity_recorder(db_session, "organization.updated", "Organization renamed"):
        await organization_handler.update(first, {"name": "First renamed"})
        with suppress(RuntimeError):
            async with activity_recorder(
                db_session, "optscale.tag.deleted", "Tag T-1 deleted", atomic=True
            ):
                await organization_handler.update(second, {"name": "Lost"})
                await organization_handler.create(new_organization("AGR-LOST"))
                raise RuntimeError("tag deletion failed")

    (entry,) = await fetch_activity_logs()
    (change,) = entry.changes
    assert change.object_id == first.id
    assert change.after is not None
    assert change.after["name"] == "First renamed"
    await db_session.refresh(second)
    assert second.name == "Second"
    assert await count_organizations(db_session) == organizations_before


async def test_succeeding_atomic_child_adds_its_rows_to_the_root_entry(
    db_session: AsyncSession,
    organization_factory: ModelFactory[Organization],
    organization_handler: OrganizationHandler,
    fetch_activity_logs: ActivityLogFetcher,
) -> None:
    """An atomic child that completes behaves like any child: its changes join the root's entry."""
    first = await organization_factory(operations_external_id="AGR-1")
    second = await organization_factory(operations_external_id="AGR-2")

    async with activity_recorder(db_session, "organization.updated", "Organizations renamed"):
        await organization_handler.update(first, {"name": "First renamed"})
        async with activity_recorder(
            db_session, "organization.updated", "Organization renamed", atomic=True
        ):
            await organization_handler.update(second, {"name": "Second renamed"})

    (entry,) = await fetch_activity_logs()
    assert {c.object_id for c in entry.changes} == {first.id, second.id}


# ---------------------------------------------------------------------------
# Late description: action and message can be decided inside the block
# ---------------------------------------------------------------------------


async def test_action_and_message_set_inside_the_block_are_recorded(
    db_session: AsyncSession,
    organization_factory: ModelFactory[Organization],
    organization_handler: OrganizationHandler,
    fetch_activity_logs: ActivityLogFetcher,
) -> None:
    """The values of `action` and `message` at the end of the block describe the entry."""
    organization = await organization_factory(name="Acme")

    async with activity_recorder(
        db_session, "organization.updated", "Organization updated"
    ) as recorder:
        await organization_handler.terminate(organization)
        recorder.action = "organization.terminated"
        recorder.message = f"Organization '{organization.name}' ({organization.id}) terminated."

    (entry,) = await fetch_activity_logs()
    assert entry.action == "organization.terminated"
    assert entry.message == f"Organization 'Acme' ({organization.id}) terminated."


@pytest.mark.parametrize("message", ["", "  "])
async def test_a_message_blanked_inside_the_block_is_rejected_at_exit(
    db_session: AsyncSession, fetch_activity_logs: ActivityLogFetcher, message: str
) -> None:
    """A block that ends with a blank message raises, as a blank message does at creation."""

    async def blanked_activity() -> None:
        async with activity_recorder(
            db_session, "organization.updated", "Organization updated"
        ) as recorder:
            recorder.message = message

    with pytest.raises(ValueError, match="needs a message"):
        await blanked_activity()

    assert await fetch_activity_logs() == []


# ---------------------------------------------------------------------------
# system_activity_recorder: app actor, skip no-change blocks, atomic
# ---------------------------------------------------------------------------


async def test_system_recorder_records_the_application_as_actor_even_in_a_request(
    db_session: AsyncSession,
    ffc_extension_auth_context: AuthenticationContext,
    organization_factory: ModelFactory[Organization],
    organization_handler: OrganizationHandler,
    fetch_activity_logs: ActivityLogFetcher,
) -> None:
    """An activity of the system belongs to the application, whoever is authenticated."""
    organization = await organization_factory()

    async with system_activity_recorder(
        db_session, "organization.terminated", "Organization terminated"
    ):
        await organization_handler.terminate(organization)

    (entry,) = await fetch_activity_logs()
    assert entry.recorded_by_id == APP_ACTOR_ID
    assert len(entry.changes) == 1


async def test_system_recorder_writes_no_entry_when_nothing_changed(
    db_session: AsyncSession, fetch_activity_logs: ActivityLogFetcher
) -> None:
    """A job that finds nothing to do leaves no trace in the activity log."""
    async with system_activity_recorder(db_session, "subscriptions.synced", "Subscriptions synced"):
        pass

    assert await fetch_activity_logs() == []


async def test_system_recorder_block_that_raises_leaves_no_rows_and_no_entry(
    db_session: AsyncSession,
    organization_factory: ModelFactory[Organization],
    organization_handler: OrganizationHandler,
    fetch_activity_logs: ActivityLogFetcher,
) -> None:
    """A failing system activity is atomic: its rows are rolled back and nothing is recorded."""
    organization = await organization_factory(name="Old name")

    async def failing_activity() -> None:
        async with system_activity_recorder(
            db_session, "organization.updated", "Organization updated"
        ):
            await organization_handler.update(organization, {"name": "Lost"})
            raise RuntimeError("step failed")

    with pytest.raises(RuntimeError, match="step failed"):
        await failing_activity()

    assert await fetch_activity_logs() == []
    await db_session.refresh(organization)
    assert organization.name == "Old name"


# ---------------------------------------------------------------------------
# Opt-out: datasource expenses are never captured
# ---------------------------------------------------------------------------


async def test_datasource_expenses_written_in_a_block_create_no_change_records(
    db_session: AsyncSession,
    organization_factory: ModelFactory[Organization],
    fetch_activity_logs: ActivityLogFetcher,
) -> None:
    """`DatasourceExpense` opts out of the activity log: inserting one yields no change record."""
    organization = await organization_factory()

    async with activity_recorder(db_session, "expenses.imported", "Expenses imported"):
        db_session.add(
            DatasourceExpense(
                organization_id=organization.id,
                datasource_id="ds-1",
                linked_datasource_id="linked-ds-1",
                linked_datasource_type=DatasourceType.AWS_CNR,
                datasource_name="Datasource",
                year=2025,
                month=3,
                day=1,
                total_expenses=Decimal("10.0000"),
            )
        )
        await db_session.flush()

    (entry,) = await fetch_activity_logs()
    assert entry.changes == []


async def test_bulk_update_of_datasource_expenses_in_a_block_is_not_inspected(
    db_session: AsyncSession,
    datasource_expense_factory: ModelFactory[DatasourceExpense],
    fetch_activity_logs: ActivityLogFetcher,
) -> None:
    """A bulk statement on `DatasourceExpense` is neither captured nor rejected."""
    expense = await datasource_expense_factory()

    async with activity_recorder(db_session, "expenses.imported", "Expenses imported"):
        await db_session.execute(
            update(DatasourceExpense)
            .where(DatasourceExpense.id == expense.id)
            .values(total_expenses=Decimal("99.0000"))
        )

    (entry,) = await fetch_activity_logs()
    assert entry.changes == []
    await db_session.refresh(expense)
    assert expense.total_expenses == Decimal("99.0000")


# ---------------------------------------------------------------------------
# Edge cases: option plumbing, options combined, nesting, session rolled back
# ---------------------------------------------------------------------------


async def test_options_are_passed_through_to_the_recorder(db_session: AsyncSession) -> None:
    """`activity_recorder()` hands every option to the `ActivityRecorder` it builds."""
    recorder = activity_recorder(
        db_session,
        "organization.updated",
        "Organization updated",
        actor_id="FUSR-0001",
        skip_if_unchanged=True,
        atomic=True,
    )

    assert recorder.session is db_session
    assert recorder.actor_id == "FUSR-0001"
    assert recorder.skip_if_unchanged is True
    assert recorder.atomic is True


async def test_options_default_to_the_previous_behaviour(db_session: AsyncSession) -> None:
    """Without options the recorder resolves the actor, always writes, and is not atomic."""
    recorder = activity_recorder(db_session, "organization.updated", "Organization updated")

    assert recorder.actor_id is None
    assert recorder.skip_if_unchanged is False
    assert recorder.atomic is False


async def test_system_recorder_is_configured_for_jobs(db_session: AsyncSession) -> None:
    """`system_activity_recorder()` is an `ActivityRecorder` with the app actor, skip and atomic."""
    recorder = system_activity_recorder(db_session, "subscriptions.synced", "Subscriptions synced")

    assert isinstance(recorder, ActivityRecorder)
    assert recorder.action == "subscriptions.synced"
    assert recorder.message == "Subscriptions synced"
    assert recorder.actor_id == APP_ACTOR_ID
    assert recorder.skip_if_unchanged is True
    assert recorder.atomic is True


async def test_skip_if_unchanged_of_a_child_recorder_is_ignored(
    db_session: AsyncSession, fetch_activity_logs: ActivityLogFetcher
) -> None:
    """Only the root decides whether an entry is written; a child's `skip_if_unchanged` is moot."""
    async with activity_recorder(db_session, "mpt.order.completed", "Order completed"):
        async with activity_recorder(
            db_session, "optscale.tag.deleted", "Tag T-1 deleted", skip_if_unchanged=True
        ):
            pass

    (entry,) = await fetch_activity_logs()
    assert entry.action == "mpt.order.completed"
    assert entry.changes == []


async def test_atomic_block_that_is_skipped_still_releases_its_savepoint(
    db_session: AsyncSession,
    organization_factory: ModelFactory[Organization],
    organization_handler: OrganizationHandler,
    fetch_activity_logs: ActivityLogFetcher,
) -> None:
    """`atomic` with `skip_if_unchanged`: no entry, no savepoint left open, work goes on."""
    organization = await organization_factory(name="Old name")

    async with activity_recorder(
        db_session,
        "subscriptions.synced",
        "Subscriptions synced",
        skip_if_unchanged=True,
        atomic=True,
    ):
        pass

    assert not db_session.in_nested_transaction()
    await organization_handler.update(organization, {"name": "New name"})
    assert await fetch_activity_logs() == []
    await db_session.refresh(organization)
    assert organization.name == "New name"


async def test_blank_message_at_exit_of_an_atomic_block_rolls_back_its_rows(
    db_session: AsyncSession,
    organization_factory: ModelFactory[Organization],
    organization_handler: OrganizationHandler,
    fetch_activity_logs: ActivityLogFetcher,
) -> None:
    """The `ValueError` raised at exit fails the block: an atomic one discards its rows."""
    organization = await organization_factory(name="Old name")

    async def blanked_activity() -> None:
        async with activity_recorder(
            db_session, "organization.updated", "Organization updated", atomic=True
        ) as recorder:
            await organization_handler.update(organization, {"name": "Lost"})
            recorder.message = ""

    with pytest.raises(ValueError, match="needs a message"):
        await blanked_activity()

    assert await fetch_activity_logs() == []
    assert not db_session.in_nested_transaction()
    await db_session.refresh(organization)
    assert organization.name == "Old name"


async def test_bulk_update_in_a_failing_atomic_block_is_rolled_back(
    db_session: AsyncSession,
    organization_factory: ModelFactory[Organization],
    fetch_activity_logs: ActivityLogFetcher,
) -> None:
    """Rows changed by an ORM bulk statement inside the block are discarded with the savepoint."""
    organization = await organization_factory(name="Old name")

    async def failing_activity() -> None:
        async with activity_recorder(
            db_session, "organization.updated", "Organizations renamed", atomic=True
        ):
            await db_session.execute(
                update(Organization).where(Organization.id == organization.id).values(name="Lost")
            )
            raise RuntimeError("step failed")

    with pytest.raises(RuntimeError, match="step failed"):
        await failing_activity()

    assert await fetch_activity_logs() == []
    await db_session.refresh(organization)
    assert organization.name == "Old name"


async def test_failing_atomic_child_reverts_a_row_the_root_changed_to_the_root_value(
    db_session: AsyncSession,
    organization_factory: ModelFactory[Organization],
    organization_handler: OrganizationHandler,
    fetch_activity_logs: ActivityLogFetcher,
) -> None:
    """A row changed by the root and then by a failing child is recorded with the root's value."""
    organization = await organization_factory(name="First")

    async with activity_recorder(db_session, "organization.updated", "Organization renamed"):
        await organization_handler.update(organization, {"name": "Second"})
        with suppress(RuntimeError):
            async with activity_recorder(
                db_session, "organization.updated", "Organization renamed", atomic=True
            ):
                await organization_handler.update(organization, {"name": "Third"})
                raise RuntimeError("step failed")

    (entry,) = await fetch_activity_logs()
    (change,) = entry.changes
    assert change.before is not None
    assert change.after is not None
    assert change.before["name"] == "First"
    assert change.after["name"] == "Second"
    await db_session.refresh(organization)
    assert organization.name == "Second"


async def test_failing_atomic_child_inside_an_atomic_root_leaves_the_root_intact(
    db_session: AsyncSession,
    organization_factory: ModelFactory[Organization],
    organization_handler: OrganizationHandler,
    fetch_activity_logs: ActivityLogFetcher,
) -> None:
    """Nested savepoints unwind in order: the child's rollback does not disturb the root's."""
    first = await organization_factory(name="First", operations_external_id="AGR-1")
    second = await organization_factory(name="Second", operations_external_id="AGR-2")

    async with system_activity_recorder(db_session, "subscriptions.synced", "Subscriptions synced"):
        await organization_handler.update(first, {"name": "First renamed"})
        with suppress(RuntimeError):
            async with system_activity_recorder(
                db_session, "entitlement.terminated", "Entitlement terminated"
            ):
                await organization_handler.update(second, {"name": "Lost"})
                raise RuntimeError("step failed")

    (entry,) = await fetch_activity_logs()
    (change,) = entry.changes
    assert change.object_id == first.id
    assert not db_session.in_nested_transaction()
    await db_session.refresh(first)
    await db_session.refresh(second)
    assert first.name == "First renamed"
    assert second.name == "Second"


async def test_system_recorder_nested_in_a_request_recorder_keeps_the_request_actor(
    db_session: AsyncSession,
    ffc_extension_auth_context: AuthenticationContext,
    ffc_extension: System,
    organization_factory: ModelFactory[Organization],
    organization_handler: OrganizationHandler,
    fetch_activity_logs: ActivityLogFetcher,
) -> None:
    """A system step run inside an API action is part of that action: the request's actor stays."""
    organization = await organization_factory()

    async with activity_recorder(db_session, "organization.terminated", "Organization terminated"):
        async with system_activity_recorder(db_session, "optscale.tag.deleted", "Tag T-1 deleted"):
            await organization_handler.terminate(organization)

    (entry,) = await fetch_activity_logs()
    assert entry.recorded_by_id == ffc_extension.id
    assert entry.action == "organization.terminated"
    assert len(entry.changes) == 1


async def test_atomic_block_copes_with_the_session_rolled_back_inside_it(
    db_session: AsyncSession,
    organization_factory: ModelFactory[Organization],
    organization_handler: OrganizationHandler,
    fetch_activity_logs: ActivityLogFetcher,
) -> None:
    """When the block itself rolled the session back, its savepoint is gone; the recorder does
    not try to roll it back again and the block's own exception is the one that propagates."""
    organization = await organization_factory(name="Old name")

    async def failing_activity() -> None:
        async with activity_recorder(
            db_session, "organization.updated", "Organization updated", atomic=True
        ):
            await organization_handler.update(organization, {"name": "Lost"})
            await db_session.rollback()
            raise RuntimeError("step failed")

    with pytest.raises(RuntimeError, match="step failed"):
        await failing_activity()

    assert await fetch_activity_logs() == []
    assert not db_session.in_nested_transaction()
    await db_session.refresh(organization)
    assert organization.name == "Old name"
