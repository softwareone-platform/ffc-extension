from datetime import UTC, datetime

from httpx import AsyncClient
from pytest_httpx import HTTPXMock
from sqlalchemy.ext.asyncio import AsyncSession

from app.activity_log.constants import APP_ACTOR_ID
from app.auth.context import AuthenticationContext
from app.conf import Settings
from app.db.handlers import EntitlementHandler
from app.db.models import ActivityLog, Entitlement, Organization, System, User
from app.enums import EntitlementStatus, OrganizationStatus
from tests.types import ActivityLogFetcher, ModelFactory


async def test_creating_a_tracked_model_records_its_create_action(
    organization_factory: ModelFactory[Organization], fetch_activity_logs: ActivityLogFetcher
) -> None:
    """Committing a new tracked row produces one entry with a before-less change record."""
    organization = await organization_factory(name="Apple Inc.")

    (entry,) = await fetch_activity_logs("organization.created")

    assert entry.message == "Organization Apple Inc. created"
    (change,) = entry.changes
    assert change.object_type == "organization"
    assert change.object_id == organization.id
    assert change.before is None
    assert change.after is not None
    assert change.after["name"] == "Apple Inc."


async def test_entry_falls_back_to_the_app_actor(
    organization_factory: ModelFactory[Organization], fetch_activity_logs: ActivityLogFetcher
) -> None:
    """Without an authenticated or declared actor the entry is attributed to the app actor."""
    await organization_factory()

    (entry,) = await fetch_activity_logs("organization.created")

    assert entry.actor_id == APP_ACTOR_ID


async def test_status_transition_records_the_registered_action(
    db_session: AsyncSession,
    organization_factory: ModelFactory[Organization],
    fetch_activity_logs: ActivityLogFetcher,
) -> None:
    """A registered status transition names the entry and keeps both images."""
    organization = await organization_factory(name="Apple Inc.", status=OrganizationStatus.ACTIVE)

    organization.status = OrganizationStatus.TERMINATED
    await db_session.commit()

    (entry,) = await fetch_activity_logs("organization.terminated")
    assert entry.message == "Organization Apple Inc. terminated"
    (change,) = entry.changes
    assert change.before is not None
    assert change.after is not None
    assert change.before["status"] == "active"
    assert change.after["status"] == "terminated"


async def test_logical_delete_through_the_handler_records_a_delete_action(
    db_session: AsyncSession,
    entitlement_factory: ModelFactory[Entitlement],
    fetch_activity_logs: ActivityLogFetcher,
) -> None:
    """A handler delete (status = deleted) is recorded with the delete action and both images."""
    entitlement = await entitlement_factory(status=EntitlementStatus.NEW)

    await EntitlementHandler(db_session).delete(entitlement)
    await db_session.commit()

    (entry,) = await fetch_activity_logs("entitlement.deleted")
    (change,) = entry.changes
    assert change.object_id == entitlement.id
    assert change.before is not None
    assert change.after is not None
    assert change.before["status"] == "new"
    assert change.after["status"] == "deleted"


async def test_changes_in_one_transaction_share_one_entry(
    db_session: AsyncSession,
    organization_factory: ModelFactory[Organization],
    fetch_activity_logs: ActivityLogFetcher,
) -> None:
    """Every tracked change committed together ends up in the same entry."""
    first = await organization_factory(operations_external_id="AGR-0000-0000-0001")
    second = await organization_factory(operations_external_id="AGR-0000-0000-0002")

    first.name = "First"
    second.name = "Second"
    await db_session.commit()

    (entry,) = await fetch_activity_logs("organization.updated")
    assert {change.object_id for change in entry.changes} == {first.id, second.id}


async def test_update_touching_only_ignored_columns_records_nothing(
    db_session: AsyncSession,
    organization_factory: ModelFactory[Organization],
    system_factory: ModelFactory[System],
    fetch_activity_logs: ActivityLogFetcher,
) -> None:
    """Changing only audit columns such as `updated_by` produces no entry."""
    organization = await organization_factory()
    system = await system_factory()
    entries_before = len(await fetch_activity_logs())

    organization.updated_by_id = system.id
    await db_session.commit()

    assert len(await fetch_activity_logs()) == entries_before


async def test_rolled_back_transaction_records_nothing(
    db_session: AsyncSession,
    organization_factory: ModelFactory[Organization],
    fetch_activity_logs: ActivityLogFetcher,
) -> None:
    """A rollback discards the tracked changes and leaves nothing for the next transaction."""
    organization = await organization_factory(name="Kept", operations_external_id="AGR-0000-0001")
    organization.name = "Rolled back"
    await db_session.flush()
    await db_session.rollback()

    await organization_factory(name="Next", operations_external_id="AGR-0000-0002")

    assert await fetch_activity_logs("organization.updated") == []
    entries = await fetch_activity_logs("organization.created")
    assert [entry.message for entry in entries] == [
        "Organization Kept created",
        "Organization Next created",
    ]
    assert len(entries[-1].changes) == 1


async def test_entry_is_attributed_to_the_authenticated_actor(
    ffc_extension_auth_context: AuthenticationContext,
    ffc_extension: System,
    organization_factory: ModelFactory[Organization],
    fetch_activity_logs: ActivityLogFetcher,
) -> None:
    """With an authentication context the entry is attributed to its actor."""
    await organization_factory()

    (entry,) = await fetch_activity_logs("organization.created")

    assert entry.actor_id == ffc_extension.id


async def test_entry_is_attributed_to_the_declared_activity_actor(
    acting_system: System,
    organization_factory: ModelFactory[Organization],
    fetch_activity_logs: ActivityLogFetcher,
) -> None:
    """A task that declared its actor through `activity_actor` gets it on the entry."""
    await organization_factory()

    (entry,) = await fetch_activity_logs("organization.created")

    assert entry.actor_id == acting_system.id


async def test_writing_activity_logs_does_not_record_activity(
    db_session: AsyncSession,
    system_factory: ModelFactory[System],
    fetch_activity_logs: ActivityLogFetcher,
) -> None:
    """Activity log rows written directly are never themselves tracked."""
    system = await system_factory()
    entries_before = len(await fetch_activity_logs())

    db_session.add(ActivityLog(actor_id=system.id, action="manual", message="Written by hand"))
    await db_session.commit()

    assert len(await fetch_activity_logs()) == entries_before + 1


async def test_api_request_is_attributed_to_the_user_and_appends_external_calls(
    entitlement_gcp: Entitlement,
    admin_client: AsyncClient,
    admin_user_token: str,
    admin_user: User,
    db_session: AsyncSession,
    httpx_mock: HTTPXMock,
    test_settings: Settings,
    fetch_activity_logs: ActivityLogFetcher,
) -> None:
    """A request commits one entry named by the DB change, owned by the user, calls appended."""
    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.optscale_ffc_api_base_url}/admin/datasources/{entitlement_gcp.linked_datasource_id}/tags/entitlement",
        json={"id": "tag_id"},
    )
    httpx_mock.add_response(
        method="DELETE",
        url=f"{test_settings.optscale_ffc_api_base_url}/admin/tags/tag_id",
        status_code=204,
    )
    entitlement_gcp.status = EntitlementStatus.ACTIVE
    await db_session.commit()

    request_start = datetime.now(UTC)
    response = await admin_client.post(
        f"/entitlements/{entitlement_gcp.id}/terminate",
        headers={"Authorization": f"Bearer {admin_user_token}"},
    )

    assert response.status_code == 200
    (entry,) = await fetch_activity_logs("entitlement.terminated")
    assert entry.actor_id == admin_user.id
    assert entry.message == "Entitlement GCP terminated; Tag tag_id deleted on FinOps for Cloud"
    assert entry.timestamp >= request_start
    (change,) = entry.changes
    assert change.object_type == "entitlement"
    assert change.object_id == entitlement_gcp.id
    assert change.before is not None
    assert change.after is not None
    assert change.before["status"] == "active"
    assert change.after["status"] == "terminated"
