import asyncio

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.activity_log import APP_ACTOR_ID, MASK, ActivityRecorder
from app.auth.context import AuthenticationContext
from app.db.base import session_factory
from app.db.handlers import ClientAccountHandler, OrganizationHandler
from app.db.models import ClientAccount, Organization, System, User
from app.enums import OrganizationStatus
from tests.types import ActivityLogFetcher, ModelFactory


async def test_creating_an_object_records_a_change_with_no_before_image(
    db_session: AsyncSession,
    organization_handler: OrganizationHandler,
    fetch_activity_logs: ActivityLogFetcher,
) -> None:
    """An object tracked with `created=True` yields a change record whose `before` is null."""
    async with ActivityRecorder(db_session, "organization.created") as rec:
        organization = await organization_handler.create(
            Organization(
                name="Acme",
                currency="EUR",
                billing_currency="USD",
                operations_external_id="AGR-1",
            )
        )
        rec.track(organization, created=True)
        rec.message = f"Organization {organization.name} created"

    (entry,) = await fetch_activity_logs()
    (change,) = entry.changes
    assert entry.action == "organization.created"
    assert entry.message == "Organization Acme created"
    assert change.object_type == "organizations"
    assert change.object_id == organization.id
    assert change.before is None
    assert change.after is not None
    assert change.after["id"] == organization.id
    assert change.after["name"] == "Acme"


async def test_updating_an_object_records_the_values_before_and_after(
    db_session: AsyncSession,
    organization_factory: ModelFactory[Organization],
    organization_handler: OrganizationHandler,
    fetch_activity_logs: ActivityLogFetcher,
) -> None:
    """A tracked update stores the column values before and after the change."""
    organization = await organization_factory(name="Old name")

    async with ActivityRecorder(
        db_session,
        "organization.updated",
        f"Organization {organization.name} renamed to New name",
    ) as rec:
        rec.track(organization)
        await organization_handler.update(organization, {"name": "New name"})

    (entry,) = await fetch_activity_logs()
    (change,) = entry.changes
    assert entry.message == "Organization Old name renamed to New name"
    assert change.before is not None
    assert change.after is not None
    assert change.before["name"] == "Old name"
    assert change.after["name"] == "New name"
    assert change.before["id"] == change.after["id"] == organization.id


async def test_logically_deleting_an_object_records_the_status_before_and_after(
    db_session: AsyncSession,
    organization_factory: ModelFactory[Organization],
    organization_handler: OrganizationHandler,
    fetch_activity_logs: ActivityLogFetcher,
) -> None:
    """A soft delete keeps the row, so both images are present and differ only in `status`."""
    organization = await organization_factory()

    async with ActivityRecorder(
        db_session, "organization.deleted", f"Organization {organization.name} deleted"
    ) as rec:
        rec.track(organization)
        await organization_handler.delete(organization)

    (entry,) = await fetch_activity_logs()
    (change,) = entry.changes
    assert entry.message == f"Organization {organization.name} deleted"
    assert change.before is not None
    assert change.after is not None
    assert change.before["status"] == OrganizationStatus.ACTIVE.value
    assert change.after["status"] == OrganizationStatus.DELETED.value


async def test_an_activity_that_tracks_nothing_records_an_entry_without_changes(
    db_session: AsyncSession, fetch_activity_logs: ActivityLogFetcher
) -> None:
    """A block that only talks to an external system records an entry with no change records."""
    order_id = "ORD-1234-5678"

    async with ActivityRecorder(
        db_session, "mpt.order.completed", f"Order {order_id} completed on MPT"
    ):
        pass

    (entry,) = await fetch_activity_logs()
    assert entry.action == "mpt.order.completed"
    assert entry.message == "Order ORD-1234-5678 completed on MPT"
    assert entry.changes == []


async def test_tracking_several_objects_records_one_entry_with_one_change_each(
    db_session: AsyncSession,
    organization_factory: ModelFactory[Organization],
    organization_handler: OrganizationHandler,
    fetch_activity_logs: ActivityLogFetcher,
) -> None:
    """One activity touching two objects produces one entry with two change records."""
    first = await organization_factory(operations_external_id="AGR-1")
    second = await organization_factory(operations_external_id="AGR-2")

    async with ActivityRecorder(
        db_session,
        "organization.terminated",
        f"Organizations {first.name} and {second.name} terminated",
    ) as rec:
        rec.track(first)
        rec.track(second)
        await organization_handler.terminate(first)
        await organization_handler.terminate(second)

    (entry,) = await fetch_activity_logs()
    assert entry.message == f"Organizations {first.name} and {second.name} terminated"
    assert {c.object_id for c in entry.changes} == {first.id, second.id}
    assert all(c.after and c.after["status"] == "terminated" for c in entry.changes)


async def test_object_type_is_the_table_name_of_the_tracked_model(
    db_session: AsyncSession,
    client_account_factory: ModelFactory[ClientAccount],
    client_account_handler: ClientAccountHandler,
    fetch_activity_logs: ActivityLogFetcher,
) -> None:
    """`object_type` is the model's `__tablename__`, e.g. `client_accounts`."""
    client_account = await client_account_factory()

    async with ActivityRecorder(
        db_session,
        "client_account.updated",
        f"Client account {client_account.name} renamed to Renamed",
    ) as rec:
        rec.track(client_account)
        await client_account_handler.update(client_account, {"name": "Renamed"})

    (entry,) = await fetch_activity_logs()
    assert entry.changes[0].object_type == ClientAccount.__tablename__


async def test_an_empty_message_does_not_prevent_recording(
    db_session: AsyncSession, fetch_activity_logs: ActivityLogFetcher
) -> None:
    """An activity opened without a message is still recorded, with `message` empty."""
    async with ActivityRecorder(db_session, "organization.created"):
        pass

    (entry,) = await fetch_activity_logs()
    assert entry.message == ""


async def test_sensitive_columns_are_masked_in_both_images(
    db_session: AsyncSession,
    organization_factory: ModelFactory[Organization],
    organization_handler: OrganizationHandler,
    fetch_activity_logs: ActivityLogFetcher,
    sensitive_column: str,
) -> None:
    """A column marked sensitive never reaches the stored `before` or `after` JSON."""
    organization = await organization_factory(operations_external_id="AGR-OLD")

    async with ActivityRecorder(
        db_session,
        "organization.updated",
        f"Organization {organization.name} linked to a new agreement",
    ) as rec:
        rec.track(organization)
        await organization_handler.update(organization, {sensitive_column: "AGR-NEW"})

    (entry,) = await fetch_activity_logs()
    (change,) = entry.changes
    assert change.before is not None
    assert change.after is not None
    assert change.before[sensitive_column] == MASK
    assert change.after[sensitive_column] == MASK


# ---------------------------------------------------------------------------
# Failures: nothing is recorded when the business action does not succeed
# ---------------------------------------------------------------------------


async def test_an_exception_inside_the_block_records_nothing_and_propagates(
    db_session: AsyncSession,
    organization_factory: ModelFactory[Organization],
    fetch_activity_logs: ActivityLogFetcher,
) -> None:
    """When the block raises, the exception propagates and no entry is added."""
    organization = await organization_factory()

    async def failing_activity() -> None:
        async with ActivityRecorder(
            db_session,
            "organization.updated",
            f"Organization {organization.name} updated",
        ) as rec:
            rec.track(organization)
            raise RuntimeError("external call failed")

    with pytest.raises(RuntimeError, match="external call failed"):
        await failing_activity()

    assert await fetch_activity_logs() == []


async def test_rolling_back_the_transaction_removes_the_entry_with_the_change(
    db_session: AsyncSession,
    organization_factory: ModelFactory[Organization],
    organization_handler: OrganizationHandler,
    fetch_activity_logs: ActivityLogFetcher,
) -> None:
    """The entry lives in the same transaction as the change, so a rollback removes both."""
    organization = await organization_factory(name="Old name")

    async with ActivityRecorder(
        db_session,
        "organization.updated",
        f"Organization {organization.name} renamed to New name",
    ) as rec:
        rec.track(organization)
        await organization_handler.update(organization, {"name": "New name"})
    await db_session.rollback()

    assert await fetch_activity_logs() == []
    await db_session.refresh(organization)
    assert organization.name == "Old name"


# ---------------------------------------------------------------------------
# Who did it: explicit actor, else the authenticated request, else the application
# ---------------------------------------------------------------------------


async def test_actor_falls_back_to_the_application_when_nobody_is_authenticated(
    db_session: AsyncSession, fetch_activity_logs: ActivityLogFetcher
) -> None:
    """Without an explicit actor or an authenticated request, the entry belongs to the app."""
    async with ActivityRecorder(
        db_session, "mpt.order.completed", "Order ORD-1234-5678 completed on MPT"
    ):
        pass

    (entry,) = await fetch_activity_logs()
    assert entry.actor_id == APP_ACTOR_ID


async def test_actor_is_the_one_authenticated_in_the_current_request(
    db_session: AsyncSession,
    ffc_extension_auth_context: AuthenticationContext,
    ffc_extension: System,
    fetch_activity_logs: ActivityLogFetcher,
) -> None:
    """Inside an authenticated request the entry's actor is the request's actor."""
    async with ActivityRecorder(
        db_session, "mpt.order.completed", "Order ORD-1234-5678 completed on MPT"
    ):
        pass

    (entry,) = await fetch_activity_logs()
    assert entry.actor_id == ffc_extension.id


async def test_explicit_actor_model_wins_over_the_authenticated_request(
    db_session: AsyncSession,
    ffc_extension_auth_context: AuthenticationContext,
    organization_factory: ModelFactory[Organization],
    organization_handler: OrganizationHandler,
    user_factory: ModelFactory[User],
    fetch_activity_logs: ActivityLogFetcher,
) -> None:
    """An `actor=` passed as a model is recorded instead of the authentication context's actor."""
    user = await user_factory(name="Peter Parker")
    organization = await organization_factory(name="Acme")

    async with ActivityRecorder(
        db_session,
        "organization.terminated",
        f"Organization {organization.name} terminated by {user.name}",
        actor=user,
    ) as rec:
        rec.track(organization)
        await organization_handler.terminate(organization)

    (entry,) = await fetch_activity_logs()
    assert entry.actor_id == user.id
    assert entry.message == "Organization Acme terminated by Peter Parker"


async def test_explicit_actor_id_wins_over_the_authenticated_request(
    db_session: AsyncSession,
    ffc_extension_auth_context: AuthenticationContext,
    system_factory: ModelFactory[System],
    fetch_activity_logs: ActivityLogFetcher,
) -> None:
    """An `actor=` passed as an id string is recorded instead of the request's actor."""
    system = await system_factory(name="Billing job")

    async with ActivityRecorder(
        db_session,
        "mpt.order.completed",
        f"Order ORD-1234-5678 completed on MPT by {system.name}",
        actor=system.id,
    ):
        pass

    (entry,) = await fetch_activity_logs()
    assert entry.actor_id == system.id
    assert entry.message == "Order ORD-1234-5678 completed on MPT by Billing job"


async def test_explicit_actor_replaces_the_application_fallback_outside_a_request(
    db_session: AsyncSession,
    system_factory: ModelFactory[System],
    fetch_activity_logs: ActivityLogFetcher,
) -> None:
    """Outside any request, e.g. in a command, an explicit actor is used instead of the app."""
    system = await system_factory(name="Nightly sync")

    async with ActivityRecorder(
        db_session,
        "client_account.synced",
        f"Client accounts synced by {system.name}",
        actor=system,
    ):
        pass

    (entry,) = await fetch_activity_logs()
    assert entry.actor_id == system.id
    assert entry.actor_id != APP_ACTOR_ID


# ---------------------------------------------------------------------------
# Nesting: a recorder opened inside another one merges into the parent's entry
# ---------------------------------------------------------------------------


async def test_nested_recorder_appends_its_message_to_the_parent_entry(
    db_session: AsyncSession,
    organization_factory: ModelFactory[Organization],
    organization_handler: OrganizationHandler,
    fetch_activity_logs: ActivityLogFetcher,
) -> None:
    """A recorder opened inside another one adds its message to the parent's single entry."""
    organization = await organization_factory(name="Acme")

    async with ActivityRecorder(
        db_session,
        "organization.terminated",
        f"Organization {organization.name} terminated",
    ) as rec:
        rec.track(organization)
        await organization_handler.terminate(organization)
        async with ActivityRecorder(db_session, "optscale.tag.deleted", "Tag T-1 deleted"):
            pass

    (entry,) = await fetch_activity_logs()
    assert entry.action == "organization.terminated"
    assert entry.message == "Organization Acme terminated; Tag T-1 deleted"
    assert len(entry.changes) == 1


async def test_nested_recorder_with_an_empty_message_leaves_the_parent_message_untouched(
    db_session: AsyncSession, fetch_activity_logs: ActivityLogFetcher
) -> None:
    """A child that has nothing to say does not add a separator to the parent's message."""
    async with ActivityRecorder(
        db_session, "organization.terminated", "Organization Acme terminated"
    ):
        async with ActivityRecorder(db_session, "optscale.tag.deleted"):
            pass

    (entry,) = await fetch_activity_logs()
    assert entry.message == "Organization Acme terminated"


async def test_object_tracked_by_parent_and_child_keeps_the_earliest_before_image(
    db_session: AsyncSession,
    organization_factory: ModelFactory[Organization],
    organization_handler: OrganizationHandler,
    fetch_activity_logs: ActivityLogFetcher,
) -> None:
    """An object tracked at both levels appears once, with `before` from the first `track()`."""
    organization = await organization_factory(name="First")

    async with ActivityRecorder(
        db_session,
        "organization.updated",
        f"Organization {organization.name} renamed to Second",
    ) as rec:
        rec.track(organization)
        await organization_handler.update(organization, {"name": "Second"})
        async with ActivityRecorder(
            db_session,
            "organization.updated",
            f"Organization {organization.name} renamed to Third",
        ) as child:
            child.track(organization)
            await organization_handler.update(organization, {"name": "Third"})

    (entry,) = await fetch_activity_logs()
    (change,) = entry.changes
    assert entry.message == (
        "Organization First renamed to Second; Organization Second renamed to Third"
    )
    assert change.before is not None
    assert change.after is not None
    assert change.before["name"] == "First"
    assert change.after["name"] == "Third"


async def test_an_exception_in_the_child_records_nothing_at_either_level(
    db_session: AsyncSession,
    organization_factory: ModelFactory[Organization],
    fetch_activity_logs: ActivityLogFetcher,
) -> None:
    """A failure inside the child propagates through the parent and no entry is written."""
    organization = await organization_factory()

    async def failing_nested_activity() -> None:
        async with ActivityRecorder(
            db_session,
            "organization.terminated",
            f"Organization {organization.name} terminated",
        ) as rec:
            rec.track(organization)
            async with ActivityRecorder(db_session, "optscale.tag.deleted", "Tag T-1 deleted"):
                raise RuntimeError("tag deletion failed")

    with pytest.raises(RuntimeError, match="tag deletion failed"):
        await failing_nested_activity()

    assert await fetch_activity_logs() == []


async def test_recorder_opened_after_the_parent_closed_writes_its_own_entry(
    db_session: AsyncSession, fetch_activity_logs: ActivityLogFetcher
) -> None:
    """Once the parent block has exited, a new recorder is a root again and writes its own entry."""
    async with ActivityRecorder(
        db_session, "organization.terminated", "Organization Acme terminated"
    ):
        async with ActivityRecorder(db_session, "optscale.tag.deleted", "Tag T-1 deleted"):
            pass
    async with ActivityRecorder(db_session, "optscale.tag.deleted", "Tag T-2 deleted"):
        pass

    entries = await fetch_activity_logs()
    assert [(e.action, e.message) for e in entries] == [
        ("organization.terminated", "Organization Acme terminated; Tag T-1 deleted"),
        ("optscale.tag.deleted", "Tag T-2 deleted"),
    ]


async def test_recorder_on_a_different_session_is_not_merged_into_the_parent(
    db_session: AsyncSession, fetch_activity_logs: ActivityLogFetcher
) -> None:
    """A nested recorder bound to another session is a separate transaction with its own entry."""
    async with ActivityRecorder(
        db_session, "organization.terminated", "Organization Acme terminated"
    ):
        async with session_factory() as other_session, other_session.begin():
            async with ActivityRecorder(
                other_session, "mpt.order.completed", "Order ORD-1234-5678 completed on MPT"
            ):
                pass

    actions = {e.action for e in await fetch_activity_logs()}
    assert actions == {"organization.terminated", "mpt.order.completed"}


async def test_task_that_outlives_the_parent_block_writes_its_own_entry(
    db_session: AsyncSession, fetch_activity_logs: ActivityLogFetcher
) -> None:
    """A task spawned in the block that finishes after it does not push into the closed parent."""
    started = asyncio.Event()
    release = asyncio.Event()

    async def late_activity() -> None:
        started.set()
        await release.wait()
        async with ActivityRecorder(
            db_session, "mpt.order.completed", "Order ORD-1234-5678 completed on MPT"
        ):
            pass

    async with ActivityRecorder(
        db_session, "organization.terminated", "Organization Acme terminated"
    ):
        task = asyncio.create_task(late_activity())
        await started.wait()
    release.set()
    await task

    entries = await fetch_activity_logs()
    assert [(e.action, e.message) for e in entries] == [
        ("organization.terminated", "Organization Acme terminated"),
        ("mpt.order.completed", "Order ORD-1234-5678 completed on MPT"),
    ]


def test_current_is_none_when_no_recorder_is_open() -> None:
    """`ActivityRecorder.current()` reports no open recorder outside any block."""
    assert ActivityRecorder.current() is None


async def test_current_returns_the_root_recorder_while_its_block_is_open(
    db_session: AsyncSession,
) -> None:
    """`ActivityRecorder.current()` returns the root recorder inside its block and `None` after."""
    async with ActivityRecorder(
        db_session, "organization.updated", "Organization Acme updated"
    ) as rec:
        assert ActivityRecorder.current() is rec
    assert ActivityRecorder.current() is None
