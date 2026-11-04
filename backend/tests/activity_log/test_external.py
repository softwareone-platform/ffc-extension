import httpx
import pytest
from pytest_httpx import HTTPXMock
from pytest_mock import MockerFixture
from sqlalchemy.ext.asyncio import AsyncSession

from app.activity_log.constants import APP_ACTOR_ID
from app.api_clients.ffc_api import FFCAPIClient
from app.conf import Settings
from app.db.models import Organization
from tests.types import ActivityLogFetcher, ModelFactory


async def test_instrumented_call_inside_a_session_commits_with_the_transaction(
    db_session: AsyncSession,
    ffc_api_client: FFCAPIClient,
    httpx_mock: HTTPXMock,
    test_settings: Settings,
    fetch_activity_logs: ActivityLogFetcher,
) -> None:
    """A tracked call made while a session is open is written when that session commits."""
    httpx_mock.add_response(
        method="DELETE", url=f"{test_settings.optscale_ffc_api_base_url}/admin/tags/tag-1"
    )

    await ffc_api_client.delete_tag("tag-1")
    assert await fetch_activity_logs("optscale.tag.deleted") == []

    await db_session.commit()
    (entry,) = await fetch_activity_logs("optscale.tag.deleted")
    assert entry.message == "Tag tag-1 deleted on FinOps for Cloud"
    assert entry.actor_id == APP_ACTOR_ID
    assert entry.changes == []


async def test_instrumented_call_is_appended_to_the_entry_of_the_db_change(
    db_session: AsyncSession,
    organization_factory: ModelFactory[Organization],
    ffc_api_client: FFCAPIClient,
    httpx_mock: HTTPXMock,
    test_settings: Settings,
    fetch_activity_logs: ActivityLogFetcher,
) -> None:
    """With a DB change in the transaction, that change names the entry and the call is appended."""
    httpx_mock.add_response(
        method="DELETE", url=f"{test_settings.optscale_ffc_api_base_url}/admin/tags/tag-1"
    )
    organization = await organization_factory(name="Apple")
    organization.name = "Apple Inc."

    await ffc_api_client.delete_tag("tag-1")
    await db_session.commit()

    (entry,) = await fetch_activity_logs("organization.updated")
    assert entry.message == "Organization Apple Inc. updated; Tag tag-1 deleted on FinOps for Cloud"
    assert len(entry.changes) == 1


async def test_instrumented_call_without_a_session_writes_an_entry_at_once(
    no_current_session: None,
    ffc_api_client: FFCAPIClient,
    httpx_mock: HTTPXMock,
    test_settings: Settings,
    fetch_activity_logs: ActivityLogFetcher,
) -> None:
    """With no session open in the task, a successful tracked call is logged immediately."""
    httpx_mock.add_response(
        method="DELETE", url=f"{test_settings.optscale_ffc_api_base_url}/admin/tags/tag-2"
    )

    await ffc_api_client.delete_tag("tag-2")

    (entry,) = await fetch_activity_logs("optscale.tag.deleted")
    assert entry.message == "Tag tag-2 deleted on FinOps for Cloud"
    assert entry.actor_id == APP_ACTOR_ID


async def test_failed_call_records_nothing(
    db_session: AsyncSession,
    ffc_api_client: FFCAPIClient,
    httpx_mock: HTTPXMock,
    test_settings: Settings,
    fetch_activity_logs: ActivityLogFetcher,
) -> None:
    """A tracked call that raises is not recorded."""
    httpx_mock.add_response(
        method="DELETE",
        url=f"{test_settings.optscale_ffc_api_base_url}/admin/tags/tag-3",
        status_code=500,
    )

    with pytest.raises(httpx.HTTPStatusError, match="500"):
        await ffc_api_client.delete_tag("tag-3")
    await db_session.commit()

    assert await fetch_activity_logs("optscale.tag.deleted") == []


async def test_masked_arguments_never_reach_the_message(
    db_session: AsyncSession,
    ffc_api_client: FFCAPIClient,
    httpx_mock: HTTPXMock,
    test_settings: Settings,
    fetch_activity_logs: ActivityLogFetcher,
) -> None:
    """Arguments listed in the tracker's mask are not rendered into the message."""
    httpx_mock.add_response(
        method="POST", url=f"{test_settings.optscale_ffc_api_base_url}/admin/users", status_code=201
    )

    await ffc_api_client.create_user(
        email="peter.parker@spiderman.com", display_name="Peter Parker", password="s3cret"
    )
    await db_session.commit()

    (entry,) = await fetch_activity_logs("optscale.user.created")
    assert entry.message == "User peter.parker@spiderman.com created on FinOps for Cloud"
    assert "s3cret" not in entry.message


async def test_recording_failure_does_not_break_the_call(
    mocker: MockerFixture,
    db_session: AsyncSession,
    ffc_api_client: FFCAPIClient,
    httpx_mock: HTTPXMock,
    test_settings: Settings,
) -> None:
    """An error while recording is logged and the business result is still returned."""
    mocker.patch(
        "app.activity_log.external.record_external_call",
        new_callable=mocker.AsyncMock,
        side_effect=RuntimeError("boom"),
    )
    httpx_mock.add_response(
        method="DELETE",
        url=f"{test_settings.optscale_ffc_api_base_url}/admin/tags/tag-4",
        status_code=204,
    )

    response = await ffc_api_client.delete_tag("tag-4")

    assert response.status_code == 204
