"""How changes are captured: every row the session writes in the block, however it is written."""

import pytest
from sqlalchemy import delete, insert, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.activity import CAPTURE_OPTION, MASK, ActivityRecorderError, activity_recorder
from app.db.base import session_factory
from app.db.handlers import OrganizationHandler
from app.db.models import Actor, Organization, User
from tests.db.models import ChildForTests, ParentWithChildrenForTests
from tests.types import ActivityLogFetcher, ModelFactory


async def rename(session: AsyncSession, organization_id: str, name: str) -> None:
    """A helper that knows nothing about activity logs."""
    organization = await session.get_one(Organization, organization_id)
    organization.name = name
    await session.flush()


def select_statements(statements: list[str]) -> list[str]:
    """The `SELECT`s among the collected statements."""
    return [s for s in statements if s.lstrip().upper().startswith("SELECT")]


# ---------------------------------------------------------------------------
# Rows changed by code that knows nothing about the recorder
# ---------------------------------------------------------------------------


async def test_changes_made_by_a_called_function_are_captured(
    db_session: AsyncSession,
    organization_factory: ModelFactory[Organization],
    fetch_activity_logs: ActivityLogFetcher,
) -> None:
    """A function called in the block changes a row; the entry records it automatically."""
    organization = await organization_factory(name="Old", operations_external_id="AGR-1")

    async with activity_recorder(db_session, "organization.renamed", "Organization renamed"):
        await rename(db_session, organization.id, "New")

    (entry,) = await fetch_activity_logs()
    (change,) = entry.changes
    assert change.object_id == organization.id
    assert change.before is not None
    assert change.before["name"] == "Old"
    assert change.after is not None
    assert change.after["name"] == "New"


async def test_changes_in_a_nested_recorder_belong_to_the_single_root_entry(
    db_session: AsyncSession,
    organization_factory: ModelFactory[Organization],
    organization_handler: OrganizationHandler,
    fetch_activity_logs: ActivityLogFetcher,
) -> None:
    """Rows changed inside a child block are change records of the root entry."""
    first = await organization_factory(operations_external_id="AGR-2")
    second = await organization_factory(operations_external_id="AGR-3")

    async def terminate(organization: Organization) -> None:
        async with activity_recorder(
            db_session, "organization.terminated", f"{organization.name} terminated"
        ):
            await organization_handler.terminate(organization)

    async with activity_recorder(db_session, "organizations.terminated", "Bulk termination"):
        await terminate(first)
        await terminate(second)

    (entry,) = await fetch_activity_logs()
    assert entry.action == "organizations.terminated"
    assert {c.object_id for c in entry.changes} == {first.id, second.id}


async def test_swallowed_child_failure_keeps_its_changes(
    db_session: AsyncSession,
    organization_factory: ModelFactory[Organization],
    fetch_activity_logs: ActivityLogFetcher,
) -> None:
    """Rows a failed child changed are still in the transaction, so they are recorded."""
    organization = await organization_factory(name="Old", operations_external_id="AGR-17")

    async def failing_child() -> None:
        async with activity_recorder(db_session, "optscale.tag.deleted", "Tag T-1 deleted"):
            await rename(db_session, organization.id, "New")
            raise RuntimeError("API call failed")

    async with activity_recorder(db_session, "organization.renamed", "Organization renamed"):
        with pytest.raises(RuntimeError, match="API call failed"):
            await failing_child()

    (entry,) = await fetch_activity_logs()
    assert entry.message == "Organization renamed"
    assert [c.object_id for c in entry.changes] == [organization.id]


async def test_recorder_rejoins_its_session_after_a_recorder_on_another_session(
    db_session: AsyncSession,
    organization_factory: ModelFactory[Organization],
    fetch_activity_logs: ActivityLogFetcher,
) -> None:
    """Session A -> session B -> session A: the innermost block joins the outer A entry."""
    organization = await organization_factory(name="Old", operations_external_id="AGR-18")

    async with activity_recorder(db_session, "outer", "Outer"):
        async with session_factory() as other, other.begin():
            async with activity_recorder(other, "other", "Other"):
                async with activity_recorder(db_session, "inner", "Inner"):
                    await rename(db_session, organization.id, "New")

    entries = {e.action: e for e in await fetch_activity_logs()}
    assert set(entries) == {"outer", "other"}
    assert entries["outer"].message == "Outer"
    assert [c.object_id for c in entries["outer"].changes] == [organization.id]


# ---------------------------------------------------------------------------
# The before image is the row as it was in the database when the block started
# ---------------------------------------------------------------------------


async def test_changes_pending_before_the_block_are_not_attributed_to_it(
    db_session: AsyncSession,
    organization_factory: ModelFactory[Organization],
    fetch_activity_logs: ActivityLogFetcher,
) -> None:
    """An unflushed change made before the block is written on enter, outside the entry."""
    organization = await organization_factory(name="Old", operations_external_id="AGR-19")
    organization.name = "Changed earlier"

    async with activity_recorder(db_session, "organization.checked", "Organization checked"):
        pass

    (entry,) = await fetch_activity_logs()
    assert entry.changes == []
    assert organization.name == "Changed earlier"


async def test_before_image_is_the_row_as_it_was_when_the_block_started(
    db_session: AsyncSession,
    organization_factory: ModelFactory[Organization],
    fetch_activity_logs: ActivityLogFetcher,
) -> None:
    """A change pending on enter is part of the before image, not of the recorded change."""
    organization = await organization_factory(name="Old", operations_external_id="AGR-20")
    organization.name = "Changed earlier"

    async with activity_recorder(db_session, "organization.renamed", "Organization renamed"):
        organization.name = "New"

    (change,) = (await fetch_activity_logs())[0].changes
    assert change.before is not None
    assert change.before["name"] == "Changed earlier"


async def test_unflushed_change_before_the_first_flush_keeps_the_database_before_image(
    db_session: AsyncSession,
    organization_factory: ModelFactory[Organization],
    fetch_activity_logs: ActivityLogFetcher,
) -> None:
    """An attribute set twice before any flush still yields the stored value as `before`."""
    organization = await organization_factory(name="Old", operations_external_id="AGR-4")

    async with activity_recorder(db_session, "organization.renamed", "Organization renamed"):
        organization.name = "Middle"
        organization.name = "New"

    (change,) = (await fetch_activity_logs())[0].changes
    assert change.before is not None
    assert change.before["name"] == "Old"
    assert change.after is not None
    assert change.after["name"] == "New"


async def test_expired_attributes_are_read_from_the_database_for_the_before_image(
    db_session: AsyncSession,
    organization_factory: ModelFactory[Organization],
    fetch_activity_logs: ActivityLogFetcher,
) -> None:
    """An attribute overwritten without being loaded is completed from the database."""
    organization = await organization_factory(name="Old", operations_external_id="AGR-5")
    db_session.expire(organization, ["name", "currency"])

    async with activity_recorder(db_session, "organization.renamed", "Organization renamed"):
        organization.name = "New"

    (change,) = (await fetch_activity_logs())[0].changes
    assert change.before is not None
    assert change.after is not None
    assert change.before["name"] == "Old"
    assert change.before["currency"] == "EUR"
    assert set(change.before) == set(change.after)


async def test_before_images_of_stale_rows_are_read_in_one_query(
    db_session: AsyncSession,
    organization_factory: ModelFactory[Organization],
    sql_statements: list[str],
) -> None:
    """Rows a previous flush left incomplete in memory are read together, not one by one."""
    organizations = [
        await organization_factory(operations_external_id=f"AGR-B{i}") for i in range(3)
    ]
    for organization in organizations:
        organization.name = "Flushed"
    await db_session.flush()  # a multi-row UPDATE expires the server-generated `updated_at`
    sql_statements.clear()

    async with activity_recorder(db_session, "organizations.renamed", "Organizations renamed"):
        for organization in organizations:
            organization.name = "Renamed"

    assert len(select_statements(sql_statements)) == 2  # the before images, then the after


async def test_rows_written_through_a_relationship_collection_are_captured(
    db_session: AsyncSession,
    parent_factory: ModelFactory[ParentWithChildrenForTests],
    child_factory: ModelFactory[ChildForTests],
    fetch_activity_logs: ActivityLogFetcher,
    sql_statements: list[str],
) -> None:
    """Children whose foreign key the flush sets, without them being dirty, are all recorded."""
    parent = await parent_factory()
    children = [await child_factory(name=f"Child {i}") for i in range(50)]
    sql_statements.clear()

    async with activity_recorder(db_session, "parent.children_added", "50 children added"):
        parent.children.extend(children)
    selects_in_block = len(select_statements(sql_statements))

    (entry,) = await fetch_activity_logs()
    assert {c.object_id for c in entry.changes} == {child.id for child in children}
    assert all(c.before and c.before["parent_id"] is None for c in entry.changes)
    assert all(c.after and c.after["parent_id"] == parent.id for c in entry.changes)
    assert selects_in_block == 0  # every image came from memory


async def test_relationship_written_row_with_expired_attributes_is_completed_from_the_database(
    db_session: AsyncSession,
    parent_factory: ModelFactory[ParentWithChildrenForTests],
    child_factory: ModelFactory[ChildForTests],
    fetch_activity_logs: ActivityLogFetcher,
) -> None:
    """A child whose memory image is incomplete when the flush writes it is read from the DB."""
    parent = await parent_factory()
    child = await child_factory(name="Expired")
    db_session.expire(child, ["name"])

    async with activity_recorder(db_session, "parent.children_added", "1 child added"):
        parent.children.append(child)

    (change,) = (await fetch_activity_logs())[0].changes
    assert change.before is not None
    assert change.before["name"] == "Expired"
    assert change.before["parent_id"] is None
    assert change.after is not None
    assert change.after["parent_id"] == parent.id


# ---------------------------------------------------------------------------
# Inserts, hard deletes and no-ops
# ---------------------------------------------------------------------------


async def test_created_object_is_detected_without_a_flag(
    db_session: AsyncSession, fetch_activity_logs: ActivityLogFetcher
) -> None:
    """A row inserted in the block has a null `before` and server defaults in `after`."""
    async with activity_recorder(db_session, "organization.created", "Organization created"):
        organization = Organization(
            name="Acme", currency="EUR", billing_currency="USD", operations_external_id="AGR-1"
        )
        db_session.add(organization)

    (change,) = (await fetch_activity_logs())[0].changes
    assert change.before is None
    assert change.after is not None
    assert change.after["id"] == organization.id
    assert change.after["created_at"] is not None


async def test_row_created_and_then_updated_in_the_block_has_no_before_image(
    db_session: AsyncSession, fetch_activity_logs: ActivityLogFetcher
) -> None:
    """A row inserted in one flush and updated in the next is still a creation."""
    async with activity_recorder(db_session, "organization.created", "Organization created"):
        organization = Organization(
            name="Draft", currency="EUR", billing_currency="USD", operations_external_id="AGR-1"
        )
        db_session.add(organization)
        await db_session.flush()
        organization.name = "Final"

    (change,) = (await fetch_activity_logs())[0].changes
    assert change.before is None
    assert change.after is not None
    assert change.after["name"] == "Final"


async def test_hard_delete_records_no_after_image(
    db_session: AsyncSession,
    organization_factory: ModelFactory[Organization],
    fetch_activity_logs: ActivityLogFetcher,
) -> None:
    """A row removed with `session.delete()` has a `before` and a null `after`."""
    organization = await organization_factory(name="Gone", operations_external_id="AGR-6")

    async with activity_recorder(db_session, "organization.purged", "Organization purged"):
        await db_session.delete(organization)

    (change,) = (await fetch_activity_logs())[0].changes
    assert change.before is not None
    assert change.before["name"] == "Gone"
    assert change.after is None


async def test_row_created_and_deleted_in_the_block_is_not_recorded(
    db_session: AsyncSession, fetch_activity_logs: ActivityLogFetcher
) -> None:
    """A row that exists neither before nor after the block leaves no change record."""
    async with activity_recorder(db_session, "organization.noop", "Organization noop"):
        organization = Organization(
            name="Tmp", currency="EUR", billing_currency="USD", operations_external_id="AGR-1"
        )
        db_session.add(organization)
        await db_session.flush()
        await db_session.delete(organization)

    assert (await fetch_activity_logs())[0].changes == []


async def test_object_set_to_its_current_value_is_not_recorded(
    db_session: AsyncSession,
    organization_factory: ModelFactory[Organization],
    fetch_activity_logs: ActivityLogFetcher,
) -> None:
    """Assigning the value an attribute already has produces no change record."""
    organization = await organization_factory(name="Same", operations_external_id="AGR-7")

    async with activity_recorder(db_session, "organization.updated", "Organization updated"):
        organization.name = "Same"

    assert (await fetch_activity_logs())[0].changes == []


async def test_before_from_memory_and_after_from_the_database_compare_equal(
    db_session: AsyncSession,
    child_factory: ModelFactory[ChildForTests],
    fetch_activity_logs: ActivityLogFetcher,
) -> None:
    """A row changed and then changed back by a bulk statement is not recorded as changed."""
    child = await child_factory(name="Old")

    async with activity_recorder(db_session, "child.renamed", "Child renamed"):
        child.name = "New"  # before image taken from memory at the flush
        await db_session.flush()
        await db_session.execute(  # after image read from the database
            update(ChildForTests).where(ChildForTests.id == child.id).values(name="Old")
        )

    assert (await fetch_activity_logs())[0].changes == []


async def test_change_to_a_sensitive_column_only_is_recorded_masked(
    db_session: AsyncSession,
    organization_factory: ModelFactory[Organization],
    fetch_activity_logs: ActivityLogFetcher,
    sensitive_column: str,
) -> None:
    """Masking happens after diffing, so a sensitive-only change is not dropped as a no-op."""
    organization = await organization_factory(operations_external_id="AGR-OLD")

    async with activity_recorder(db_session, "organization.updated", "Organization updated"):
        organization.operations_external_id = "AGR-NEW"

    (change,) = (await fetch_activity_logs())[0].changes
    assert change.before is not None
    assert change.after is not None
    assert change.before[sensitive_column] == change.after[sensitive_column] == MASK


# ---------------------------------------------------------------------------
# Bulk statements
# ---------------------------------------------------------------------------


async def test_bulk_update_statement_is_captured(
    db_session: AsyncSession,
    organization_factory: ModelFactory[Organization],
    fetch_activity_logs: ActivityLogFetcher,
) -> None:
    """An ORM-enabled `update()` records one change per affected row."""
    first = await organization_factory(currency="EUR", operations_external_id="AGR-9")
    second = await organization_factory(currency="EUR", operations_external_id="AGR-10")
    untouched = await organization_factory(currency="GBP", operations_external_id="AGR-11")

    async with activity_recorder(
        db_session, "organizations.currency_changed", "Organizations currency changed"
    ):
        await db_session.execute(
            update(Organization).where(Organization.currency == "EUR").values(currency="USD")
        )

    changes = (await fetch_activity_logs())[0].changes
    assert {c.object_id for c in changes} == {first.id, second.id}
    assert untouched.id not in {c.object_id for c in changes}
    assert all(c.before and c.before["currency"] == "EUR" for c in changes)
    assert all(c.after and c.after["currency"] == "USD" for c in changes)


async def test_bulk_delete_without_a_where_clause_records_every_row(
    db_session: AsyncSession,
    child_factory: ModelFactory[ChildForTests],
    fetch_activity_logs: ActivityLogFetcher,
) -> None:
    """An ORM-enabled `delete()` with no filter records every row it removes, `after` null."""
    children = [await child_factory(name=f"Child {i}") for i in range(3)]

    async with activity_recorder(db_session, "children.purged", "Children purged"):
        await db_session.execute(delete(ChildForTests))

    changes = (await fetch_activity_logs())[0].changes
    assert {c.object_id for c in changes} == {child.id for child in children}
    assert all(c.before is not None and c.after is None for c in changes)


async def test_bulk_update_by_primary_key_is_captured(
    db_session: AsyncSession,
    organization_factory: ModelFactory[Organization],
    fetch_activity_logs: ActivityLogFetcher,
) -> None:
    """`session.execute(update(Model), [{"id": ..., ...}])` records the listed rows only."""
    organization = await organization_factory(name="Old", operations_external_id="AGR-12")
    await organization_factory(operations_external_id="AGR-13")

    async with activity_recorder(db_session, "organization.renamed", "Organization renamed"):
        await db_session.execute(update(Organization), [{"id": organization.id, "name": "New"}])

    (change,) = (await fetch_activity_logs())[0].changes
    assert change.object_id == organization.id
    assert change.after is not None
    assert change.after["name"] == "New"


async def test_bulk_statement_can_opt_out_of_capture(
    db_session: AsyncSession,
    organization_factory: ModelFactory[Organization],
    fetch_activity_logs: ActivityLogFetcher,
) -> None:
    """`execution_options(activity_log=False)` skips recording one statement."""
    await organization_factory(currency="EUR", operations_external_id="AGR-14")

    async with activity_recorder(db_session, "organizations.cleanup", "Organizations cleanup"):
        await db_session.execute(
            update(Organization).values(currency="USD").execution_options(**{CAPTURE_OPTION: False})
        )

    assert (await fetch_activity_logs())[0].changes == []


async def test_model_opted_out_with_activity_log_false_is_not_recorded(
    db_session: AsyncSession,
    opted_out_model: type[ChildForTests],
    child_factory: ModelFactory[ChildForTests],
    fetch_activity_logs: ActivityLogFetcher,
) -> None:
    """A model declaring `__activity_log__ = False` leaves no change record when written."""
    child = await child_factory(name="Old")

    async with activity_recorder(db_session, "child.renamed", "Child renamed"):
        child.name = "New"

    assert (await fetch_activity_logs())[0].changes == []


async def test_bulk_statement_on_an_opted_out_model_is_not_recorded(
    db_session: AsyncSession,
    opted_out_model: type[ChildForTests],
    child_factory: ModelFactory[ChildForTests],
    fetch_activity_logs: ActivityLogFetcher,
) -> None:
    """A bulk statement on a model declaring `__activity_log__ = False` is not inspected."""
    await child_factory(name="Old")

    async with activity_recorder(db_session, "children.renamed", "Children renamed"):
        await db_session.execute(update(opted_out_model).values(name="New"))

    assert (await fetch_activity_logs())[0].changes == []


async def test_bulk_insert_statement_is_refused(db_session: AsyncSession) -> None:
    """A statement whose rows cannot be captured raises instead of being silently missed."""
    with pytest.raises(ActivityRecorderError, match="only ORM-enabled"):
        async with activity_recorder(db_session, "organization.created", "Organization created"):
            await db_session.execute(
                insert(Organization).values(
                    name="X", currency="EUR", billing_currency="USD", operations_external_id="A"
                )
            )


async def test_textual_sql_inside_the_block_is_allowed(
    db_session: AsyncSession, fetch_activity_logs: ActivityLogFetcher
) -> None:
    """Reads and other textual SQL run normally; only DML statements are inspected."""
    async with activity_recorder(db_session, "organization.checked", "Organization checked"):
        assert (await db_session.execute(text("SELECT 1"))).scalar_one() == 1

    assert (await fetch_activity_logs())[0].changes == []


# ---------------------------------------------------------------------------
# Transactions: commits, savepoints
# ---------------------------------------------------------------------------


async def test_commit_inside_the_block_is_refused(
    db_session: AsyncSession, fetch_activity_logs: ActivityLogFetcher
) -> None:
    """Committing in the block would split the entry from the changes it describes."""
    with pytest.raises(ActivityRecorderError, match="Cannot commit"):
        async with activity_recorder(db_session, "organization.updated", "Organization updated"):
            await db_session.commit()

    assert await fetch_activity_logs() == []


async def test_savepoint_committed_inside_the_block_is_allowed_and_recorded(
    db_session: AsyncSession,
    organization_factory: ModelFactory[Organization],
    fetch_activity_logs: ActivityLogFetcher,
) -> None:
    """Releasing a savepoint is not a commit: the block goes on and its changes are recorded."""
    organization = await organization_factory(name="Old", operations_external_id="AGR-21")

    async with activity_recorder(db_session, "organization.renamed", "Organization renamed"):
        async with db_session.begin_nested():
            organization.name = "New"

    (change,) = (await fetch_activity_logs())[0].changes
    assert change.before is not None
    assert change.before["name"] == "Old"
    assert change.after is not None
    assert change.after["name"] == "New"


async def test_rolled_back_savepoint_changes_are_not_recorded(
    db_session: AsyncSession,
    organization_factory: ModelFactory[Organization],
    fetch_activity_logs: ActivityLogFetcher,
) -> None:
    """Only what is in the database when the block ends is recorded."""
    kept = await organization_factory(name="Kept", operations_external_id="AGR-15")
    reverted = await organization_factory(name="Reverted", operations_external_id="AGR-16")

    async with activity_recorder(db_session, "organization.renamed", "Organization renamed"):
        kept.name = "Kept 2"
        savepoint = await db_session.begin_nested()
        reverted.name = "Reverted 2"
        await db_session.flush()
        await savepoint.rollback()

    (change,) = (await fetch_activity_logs())[0].changes
    assert change.object_id == kept.id


async def test_insert_rolled_back_with_a_savepoint_is_not_recorded(
    db_session: AsyncSession, fetch_activity_logs: ActivityLogFetcher
) -> None:
    """A row inserted and rolled back inside the block leaves no change record."""
    async with activity_recorder(db_session, "organization.created", "Organization created"):
        savepoint = await db_session.begin_nested()
        db_session.add(
            Organization(
                name="Tmp", currency="EUR", billing_currency="USD", operations_external_id="AGR-R"
            )
        )
        await db_session.flush()
        await savepoint.rollback()

    assert (await fetch_activity_logs())[0].changes == []


# ---------------------------------------------------------------------------
# Inheritance
# ---------------------------------------------------------------------------


async def test_joined_inheritance_row_records_columns_of_both_tables(
    db_session: AsyncSession,
    user_factory: ModelFactory[User],
    fetch_activity_logs: ActivityLogFetcher,
) -> None:
    """A `User` change is keyed by its own table and holds `actors` and `users` columns."""
    user = await user_factory(name="Peter")

    async with activity_recorder(db_session, "user.renamed", "User renamed"):
        user.name = "Spider-Man"

    (change,) = (await fetch_activity_logs())[0].changes
    assert change.object_type == User.__tablename__
    assert change.before is not None
    assert change.after is not None
    assert change.before["name"] == "Peter"
    assert change.after["name"] == "Spider-Man"
    assert "email" in change.after


async def test_polymorphically_loaded_actor_is_recorded_as_its_own_table(
    db_session: AsyncSession,
    user_factory: ModelFactory[User],
    fetch_activity_logs: ActivityLogFetcher,
) -> None:
    """An actor loaded through the base class is still recorded under its specific table."""
    user = await user_factory(name="Peter")
    db_session.expunge(user)
    actor = (await db_session.scalars(select(Actor).where(Actor.id == user.id))).one()

    async with activity_recorder(db_session, "user.renamed", "User renamed"):
        actor.name = "Spider-Man"

    (change,) = (await fetch_activity_logs())[0].changes
    assert change.object_type == User.__tablename__
    assert change.object_id == user.id
