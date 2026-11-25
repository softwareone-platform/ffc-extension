from datetime import UTC, datetime

from httpx import AsyncClient

from app.db.models import (
    Account,
    ActivityLog,
    ActivityNote,
    App,
    ChangeRecord,
    System,
    User,
)
from app.enums import ActivityStatus
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
        recorded_by=ffc_extension,
        action="organization.updated",
        message="Renamed",
        recorded_at=datetime(2026, 1, 1, 12, 0, tzinfo=UTC),
        changes=[ChangeRecord(object_type="organizations", object_id="FORG-1234-5678")],
    )

    response = await admin_client.get("/activity-logs")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    item = data["items"][0]
    assert item == {
        "id": activity_log.id,
        "events": {
            "recorded": {
                "at": "2026-01-01T12:00:00Z",
                "by": {
                    "id": ffc_extension.id,
                    "type": "system",
                    "name": ffc_extension.name,
                    "icon": None,
                },
            },
        },
        "action": "organization.updated",
        "message": "Renamed",
        "status": "completed",
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
    """`eq(events.recorded.by.id,...)` returns only the entries recorded by that actor."""
    by_ffc = await activity_log_factory(recorded_by=ffc_extension)
    await activity_log_factory(recorded_by=gcp_extension)

    response = await admin_client.get(
        f"/activity-logs?eq(events.recorded.by.id,{ffc_extension.id})"
    )

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


async def test_get_activity_logs_with_changes_object_id_filter(
    activity_log_factory: ModelFactory[ActivityLog],
    admin_client: AsyncClient,
) -> None:
    """`any(changes,eq(changes.object_id,...))` returns only the entries that touched that id."""
    matching = await activity_log_factory(
        changes=[ChangeRecord(object_type="organizations", object_id="FORG-1111-1111")]
    )
    await activity_log_factory(
        changes=[ChangeRecord(object_type="organizations", object_id="FORG-2222-2222")]
    )
    await activity_log_factory()

    response = await admin_client.get(
        "/activity-logs?any(changes,eq(changes.object_id,FORG-1111-1111))"
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["id"] == matching.id


async def test_get_activity_logs_with_actor_type_filter(
    activity_log_factory: ModelFactory[ActivityLog],
    app_factory: ModelFactory[App],
    admin_client: AsyncClient,
    ffc_extension: System,
) -> None:
    """`eq(events.recorded.by.type,app)` returns only the entries recorded by an app actor."""
    by_app = await activity_log_factory(recorded_by=await app_factory())
    await activity_log_factory(recorded_by=ffc_extension)

    response = await admin_client.get("/activity-logs?eq(events.recorded.by.type,app)")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["id"] == by_app.id
    assert data["items"][0]["events"]["recorded"]["by"]["type"] == "app"


async def test_get_activity_logs_with_status_filter(
    activity_log_factory: ModelFactory[ActivityLog],
    admin_client: AsyncClient,
) -> None:
    """`eq(status,in_progress)` returns only the entries that are still in progress."""
    in_progress = await activity_log_factory(status=ActivityStatus.IN_PROGRESS)
    await activity_log_factory(status=ActivityStatus.COMPLETED)
    await activity_log_factory(status=ActivityStatus.ABANDONED)

    response = await admin_client.get("/activity-logs?eq(status,in_progress)")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["id"] == in_progress.id
    assert data["items"][0]["status"] == "in_progress"


async def test_get_activity_logs_with_operation_key_filter(
    activity_log_factory: ModelFactory[ActivityLog],
    admin_client: AsyncClient,
) -> None:
    """`eq(operation_key,...)` returns every entry of that operation and no other."""
    abandoned = await activity_log_factory(
        operation_key="order:ORD-1111", status=ActivityStatus.ABANDONED
    )
    in_progress = await activity_log_factory(
        operation_key="order:ORD-1111", status=ActivityStatus.IN_PROGRESS
    )
    await activity_log_factory(operation_key="order:ORD-2222")
    await activity_log_factory()

    response = await admin_client.get("/activity-logs?eq(operation_key,order:ORD-1111)")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert sorted(item["id"] for item in data["items"]) == sorted([abandoned.id, in_progress.id])
    assert "operation_key" not in data["items"][0]
    assert "notes" not in data["items"][0]


async def test_get_activity_logs_with_note_actor_id_filter(
    activity_log_factory: ModelFactory[ActivityLog],
    activity_note_factory: ModelFactory[ActivityNote],
    user_factory: ModelFactory[User],
    admin_client: AsyncClient,
) -> None:
    """Filtering notes on `events.recorded.by.id` returns the entries with a note by that actor."""
    jane = await user_factory()
    joe = await user_factory()
    by_jane = await activity_log_factory()
    await activity_note_factory(activity_log=by_jane, recorded_by=jane)
    by_joe = await activity_log_factory()
    await activity_note_factory(activity_log=by_joe, recorded_by=joe)
    await activity_log_factory()

    response = await admin_client.get(
        f"/activity-logs?any(notes,eq(notes.events.recorded.by.id,{jane.id}))"
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["id"] == by_jane.id
    assert "notes" not in data["items"][0]


async def test_get_activity_logs_with_note_actor_type_filter(
    activity_log_factory: ModelFactory[ActivityLog],
    activity_note_factory: ModelFactory[ActivityNote],
    user_factory: ModelFactory[User],
    admin_client: AsyncClient,
    ffc_extension: System,
) -> None:
    """Filtering notes on `events.recorded.by.type` returns the entries with a note by a user."""
    by_user = await activity_log_factory()
    await activity_note_factory(activity_log=by_user, recorded_by=await user_factory())
    by_system = await activity_log_factory()
    await activity_note_factory(activity_log=by_system, recorded_by=ffc_extension)

    response = await admin_client.get(
        "/activity-logs?any(notes,eq(notes.events.recorded.by.type,user))"
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["id"] == by_user.id


async def test_get_activity_logs_with_note_message_filter(
    activity_log_factory: ModelFactory[ActivityLog],
    activity_note_factory: ModelFactory[ActivityNote],
    admin_client: AsyncClient,
) -> None:
    """`any(notes,ilike(notes.message,*502*))` returns the entries with a note containing 502."""
    failed = await activity_log_factory()
    await activity_note_factory(activity_log=failed, message="Attempt failed with 502 Bad Gateway")
    succeeded = await activity_log_factory()
    await activity_note_factory(activity_log=succeeded, message="Attempt succeeded")

    response = await admin_client.get("/activity-logs?any(notes,ilike(notes.message,*502*))")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["id"] == failed.id


async def test_get_activity_logs_with_note_at_filter(
    activity_log_factory: ModelFactory[ActivityLog],
    activity_note_factory: ModelFactory[ActivityNote],
    admin_client: AsyncClient,
) -> None:
    """Filtering notes on `events.recorded.at` returns the entries with a note from that time."""
    recent = await activity_log_factory()
    await activity_note_factory(
        activity_log=recent, recorded_at=datetime(2026, 1, 3, 12, 0, tzinfo=UTC)
    )
    old = await activity_log_factory()
    await activity_note_factory(
        activity_log=old, recorded_at=datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
    )

    response = await admin_client.get(
        "/activity-logs?any(notes,gte(notes.events.recorded.at,2026-01-02T00:00:00Z))"
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["id"] == recent.id


async def test_get_activity_logs_with_several_matching_notes_returns_the_entry_once(
    activity_log_factory: ModelFactory[ActivityLog],
    activity_note_factory: ModelFactory[ActivityNote],
    user_factory: ModelFactory[User],
    admin_client: AsyncClient,
) -> None:
    """An entry with several notes matching the filter appears once in the list."""
    jane = await user_factory()
    activity_log = await activity_log_factory()
    await activity_note_factory(activity_log=activity_log, recorded_by=jane)
    await activity_note_factory(activity_log=activity_log, recorded_by=jane)
    await activity_note_factory(activity_log=activity_log, recorded_by=jane)

    response = await admin_client.get(
        f"/activity-logs?any(notes,eq(notes.events.recorded.by.id,{jane.id}))"
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert [item["id"] for item in data["items"]] == [activity_log.id]


async def test_get_activity_logs_with_recorded_at_range_filter(
    activity_log_factory: ModelFactory[ActivityLog],
    admin_client: AsyncClient,
) -> None:
    """`gte`/`lte` on `events.recorded.at` return only the entries inside the range."""
    await activity_log_factory(recorded_at=datetime(2026, 1, 1, 12, 0, tzinfo=UTC))
    inside = await activity_log_factory(recorded_at=datetime(2026, 1, 2, 12, 0, tzinfo=UTC))
    await activity_log_factory(recorded_at=datetime(2026, 1, 3, 12, 0, tzinfo=UTC))

    response = await admin_client.get(
        "/activity-logs?and(gte(events.recorded.at,2026-01-02T00:00:00Z),lte(events.recorded.at,2026-01-02T23:59:59Z))"
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["id"] == inside.id


async def test_get_activity_logs_ordered_by_recorded_at_desc(
    activity_log_factory: ModelFactory[ActivityLog],
    admin_client: AsyncClient,
) -> None:
    """`order_by(-events.recorded.at)` returns the newest entry first."""
    oldest = await activity_log_factory(recorded_at=datetime(2026, 1, 1, 12, 0, tzinfo=UTC))
    newest = await activity_log_factory(recorded_at=datetime(2026, 1, 3, 12, 0, tzinfo=UTC))
    middle = await activity_log_factory(recorded_at=datetime(2026, 1, 2, 12, 0, tzinfo=UTC))

    response = await admin_client.get("/activity-logs?order_by(-events.recorded.at)")

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
        recorded_by=ffc_extension,
        action="organization.updated",
        message="Renamed",
        recorded_at=datetime(2026, 1, 1, 12, 0, tzinfo=UTC),
        changes=[
            ChangeRecord(
                object_type="organizations",
                object_id="FORG-1234-5678",
                before={"name": "Old"},
                after={"name": "New"},
                recorded_at=datetime(2026, 1, 1, 12, 0, tzinfo=UTC),
            )
        ],
    )

    response = await admin_client.get(f"/activity-logs/{activity_log.id}")

    assert response.status_code == 200
    assert response.json() == {
        "id": activity_log.id,
        "events": {
            "recorded": {
                "at": "2026-01-01T12:00:00Z",
                "by": {
                    "id": ffc_extension.id,
                    "type": "system",
                    "name": ffc_extension.name,
                    "icon": None,
                },
            },
        },
        "action": "organization.updated",
        "message": "Renamed",
        "status": "completed",
        "operation_key": None,
        "notes": [],
        "changes": [
            {
                "object_type": "organizations",
                "object_id": "FORG-1234-5678",
                "before": {"name": "Old"},
                "after": {"name": "New"},
                "recorded_at": "2026-01-01T12:00:00Z",
            }
        ],
    }


async def test_get_activity_log_by_id_includes_operation_fields(
    activity_log_factory: ModelFactory[ActivityLog],
    activity_note_factory: ModelFactory[ActivityNote],
    user_factory: ModelFactory[User],
    admin_client: AsyncClient,
    ffc_extension: System,
) -> None:
    """The detail response carries the status, the operation key and the notes with their actor."""
    jane = await user_factory(name="Jane Doe", icon="https://example.com/jane.png")
    activity_log = await activity_log_factory(
        status=ActivityStatus.IN_PROGRESS, operation_key="order:ORD-1111"
    )
    await activity_note_factory(
        activity_log=activity_log,
        recorded_by=ffc_extension,
        message="Waiting for the datasource.",
        recorded_at=datetime(2026, 1, 1, 12, 0, tzinfo=UTC),
    )
    await activity_note_factory(
        activity_log=activity_log,
        recorded_by=jane,
        message="Retried by hand.",
        recorded_at=datetime(2026, 1, 1, 13, 0, tzinfo=UTC),
    )

    response = await admin_client.get(f"/activity-logs/{activity_log.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "in_progress"
    assert data["operation_key"] == "order:ORD-1111"
    assert data["notes"] == [
        {
            "events": {
                "recorded": {
                    "at": "2026-01-01T12:00:00Z",
                    "by": {
                        "id": ffc_extension.id,
                        "type": "system",
                        "name": ffc_extension.name,
                        "icon": None,
                    },
                },
            },
            "message": "Waiting for the datasource.",
        },
        {
            "events": {
                "recorded": {
                    "at": "2026-01-01T13:00:00Z",
                    "by": {
                        "id": jane.id,
                        "type": "user",
                        "name": "Jane Doe",
                        "icon": "https://example.com/jane.png",
                    },
                },
            },
            "message": "Retried by hand.",
        },
    ]


async def test_get_activity_log_by_id_orders_notes_by_at_then_id(
    activity_log_factory: ModelFactory[ActivityLog],
    activity_note_factory: ModelFactory[ActivityNote],
    admin_client: AsyncClient,
) -> None:
    """The notes are returned oldest first, with the id breaking ties."""
    activity_log = await activity_log_factory()
    later = datetime(2026, 1, 2, 12, 0, tzinfo=UTC)
    earlier = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
    await activity_note_factory(activity_log=activity_log, message="third", recorded_at=later)
    await activity_note_factory(activity_log=activity_log, message="first", recorded_at=earlier)
    await activity_note_factory(activity_log=activity_log, message="second", recorded_at=earlier)

    response = await admin_client.get(f"/activity-logs/{activity_log.id}")

    assert response.status_code == 200
    notes = response.json()["notes"]
    assert [note["message"] for note in notes] == ["first", "second", "third"]


async def test_get_activity_log_by_id_orders_changes_by_recorded_at_then_id(
    activity_log_factory: ModelFactory[ActivityLog],
    change_record_factory: ModelFactory[ChangeRecord],
    admin_client: AsyncClient,
) -> None:
    """The change records are returned oldest first, with the id breaking ties."""
    activity_log = await activity_log_factory()
    later = datetime(2026, 1, 2, 12, 0, tzinfo=UTC)
    earlier = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
    await change_record_factory(activity_log=activity_log, object_id="FORG-3", recorded_at=later)
    await change_record_factory(activity_log=activity_log, object_id="FORG-1", recorded_at=earlier)
    await change_record_factory(activity_log=activity_log, object_id="FORG-2", recorded_at=earlier)

    response = await admin_client.get(f"/activity-logs/{activity_log.id}")

    assert response.status_code == 200
    changes = response.json()["changes"]
    assert [change["object_id"] for change in changes] == ["FORG-1", "FORG-2", "FORG-3"]
    assert [change["recorded_at"] for change in changes] == [
        "2026-01-01T12:00:00Z",
        "2026-01-01T12:00:00Z",
        "2026-01-02T12:00:00Z",
    ]


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
