from datetime import UTC, datetime

from httpx import AsyncClient

from app.db.models import Account, ActivityLog, ChangeRecord, System
from tests.types import ModelFactory

# ==================
# List activity logs
# ==================


async def test_get_all_activity_logs_empty_db(admin_client: AsyncClient) -> None:
    """The list is empty when no activity has been recorded."""
    response = await admin_client.get("/activity-logs")

    assert response.status_code == 200
    assert response.json()["total"] == 0
    assert response.json()["items"] == []


async def test_get_all_activity_logs_returns_entries_without_changes(
    activity_log_factory: ModelFactory[ActivityLog],
    admin_client: AsyncClient,
    ffc_extension: System,
) -> None:
    """List items carry the entry fields and the actor, but not the change records."""
    activity_log = await activity_log_factory(
        actor=ffc_extension,
        action="organization.updated",
        message="Renamed",
        timestamp=datetime(2026, 1, 1, 12, 0, tzinfo=UTC),
        changes=[ChangeRecord(object_type="organizations", object_id="FORG-1234-5678")],
    )

    response = await admin_client.get("/activity-logs")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    item = data["items"][0]
    assert item == {
        "id": activity_log.id,
        "timestamp": "2026-01-01T12:00:00Z",
        "actor": {"id": ffc_extension.id, "type": "system", "name": ffc_extension.name},
        "action": "organization.updated",
        "message": "Renamed",
    }


async def test_get_activity_logs_with_action_in_filter(
    activity_log_factory: ModelFactory[ActivityLog],
    admin_client: AsyncClient,
) -> None:
    """`in(action,(...))` returns only the entries whose action is in the list."""
    await activity_log_factory(action="organization.updated")
    terminated = await activity_log_factory(action="organization.terminated")
    deleted = await activity_log_factory(action="organization.deleted")

    response = await admin_client.get(
        "/activity-logs?in(action,(organization.terminated,organization.deleted))"
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert sorted(item["id"] for item in data["items"]) == sorted([terminated.id, deleted.id])


async def test_get_activity_logs_with_actor_filter(
    activity_log_factory: ModelFactory[ActivityLog],
    admin_client: AsyncClient,
    ffc_extension: System,
    gcp_extension: System,
) -> None:
    """`eq(actor.id,...)` returns only the entries recorded by that actor."""
    by_ffc = await activity_log_factory(actor=ffc_extension)
    await activity_log_factory(actor=gcp_extension)

    response = await admin_client.get(f"/activity-logs?eq(actor.id,{ffc_extension.id})")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["id"] == by_ffc.id


async def test_get_activity_logs_with_object_filter(
    activity_log_factory: ModelFactory[ActivityLog],
    admin_client: AsyncClient,
) -> None:
    """`any(changes,...)` on object type and id returns the entries that touched that object."""
    matching = await activity_log_factory(
        changes=[ChangeRecord(object_type="organizations", object_id="FORG-1111-1111")]
    )
    await activity_log_factory(
        changes=[ChangeRecord(object_type="organizations", object_id="FORG-2222-2222")]
    )
    await activity_log_factory(
        changes=[ChangeRecord(object_type="entitlements", object_id="FORG-1111-1111")]
    )

    response = await admin_client.get(
        "/activity-logs?any(changes,and(eq(changes.object_type,organizations),"
        "eq(changes.object_id,FORG-1111-1111)))"
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["id"] == matching.id
    assert "changes" not in data["items"][0]


async def test_get_activity_logs_with_timestamp_range_filter(
    activity_log_factory: ModelFactory[ActivityLog],
    admin_client: AsyncClient,
) -> None:
    """`gte`/`lte` on `timestamp` return only the entries inside the range."""
    await activity_log_factory(timestamp=datetime(2026, 1, 1, 12, 0, tzinfo=UTC))
    inside = await activity_log_factory(timestamp=datetime(2026, 1, 2, 12, 0, tzinfo=UTC))
    await activity_log_factory(timestamp=datetime(2026, 1, 3, 12, 0, tzinfo=UTC))

    response = await admin_client.get(
        "/activity-logs?and(gte(timestamp,2026-01-02T00:00:00Z),lte(timestamp,2026-01-02T23:59:59Z))"
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["id"] == inside.id


async def test_get_activity_logs_ordered_by_timestamp_desc(
    activity_log_factory: ModelFactory[ActivityLog],
    admin_client: AsyncClient,
) -> None:
    """`order_by(-timestamp)` returns the newest entry first."""
    oldest = await activity_log_factory(timestamp=datetime(2026, 1, 1, 12, 0, tzinfo=UTC))
    newest = await activity_log_factory(timestamp=datetime(2026, 1, 3, 12, 0, tzinfo=UTC))
    middle = await activity_log_factory(timestamp=datetime(2026, 1, 2, 12, 0, tzinfo=UTC))

    response = await admin_client.get("/activity-logs?order_by(-timestamp)")

    assert response.status_code == 200
    assert [item["id"] for item in response.json()["items"]] == [newest.id, middle.id, oldest.id]


async def test_get_activity_logs_with_invalid_filter(admin_client: AsyncClient) -> None:
    """A filter on an unknown field is rejected with 400."""
    response = await admin_client.get("/activity-logs?eq(unknown,1)")

    assert response.status_code == 400


async def test_get_activity_logs_forbidden_for_affiliate(
    affiliate_account: Account,
    affiliate_client: AsyncClient,
) -> None:
    """Affiliate accounts cannot list activity logs."""
    response = await affiliate_client.get("/activity-logs")

    assert response.status_code == 403
    assert response.json()["detail"] == "You've found the door, but you don't have the key."


async def test_get_activity_logs_unauthenticated(api_client: AsyncClient) -> None:
    """Listing activity logs without a token is rejected with 401."""
    response = await api_client.get("/activity-logs")

    assert response.status_code == 401


# ====================
# Get activity log by id
# ====================


async def test_get_activity_log_by_id_includes_changes(
    activity_log_factory: ModelFactory[ActivityLog],
    admin_client: AsyncClient,
    ffc_extension: System,
) -> None:
    """The detail response carries the entry fields and the full change records."""
    activity_log = await activity_log_factory(
        actor=ffc_extension,
        action="organization.updated",
        message="Renamed",
        timestamp=datetime(2026, 1, 1, 12, 0, tzinfo=UTC),
        changes=[
            ChangeRecord(
                object_type="organizations",
                object_id="FORG-1234-5678",
                before={"name": "Old"},
                after={"name": "New"},
            )
        ],
    )

    response = await admin_client.get(f"/activity-logs/{activity_log.id}")

    assert response.status_code == 200
    assert response.json() == {
        "id": activity_log.id,
        "timestamp": "2026-01-01T12:00:00Z",
        "actor": {"id": ffc_extension.id, "type": "system", "name": ffc_extension.name},
        "action": "organization.updated",
        "message": "Renamed",
        "changes": [
            {
                "object_type": "organizations",
                "object_id": "FORG-1234-5678",
                "before": {"name": "Old"},
                "after": {"name": "New"},
            }
        ],
    }


async def test_get_activity_log_by_id_without_changes(
    activity_log_factory: ModelFactory[ActivityLog],
    admin_client: AsyncClient,
) -> None:
    """An entry that changed nothing is returned with an empty `changes` list."""
    activity_log = await activity_log_factory()

    response = await admin_client.get(f"/activity-logs/{activity_log.id}")

    assert response.status_code == 200
    assert response.json()["changes"] == []


async def test_get_activity_log_by_id_not_found(admin_client: AsyncClient) -> None:
    """An unknown but well-formed id is answered with 404."""
    id = "FLOG-0000-0000-0000"
    response = await admin_client.get(f"/activity-logs/{id}")

    assert response.status_code == 404
    assert response.json()["detail"] == f"ActivityLog with id {id} not found"


async def test_get_activity_log_by_id_invalid_id(admin_client: AsyncClient) -> None:
    """An id that does not match the `FLOG-` pattern is rejected with 422."""
    response = await admin_client.get("/activity-logs/not-an-id")

    assert response.status_code == 422


async def test_get_activity_log_by_id_forbidden_for_affiliate(
    activity_log_factory: ModelFactory[ActivityLog],
    affiliate_account: Account,
    affiliate_client: AsyncClient,
) -> None:
    """Affiliate accounts cannot read an activity log entry."""
    activity_log = await activity_log_factory()

    response = await affiliate_client.get(f"/activity-logs/{activity_log.id}")

    assert response.status_code == 403
