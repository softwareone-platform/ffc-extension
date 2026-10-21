from datetime import UTC, datetime, timedelta, timezone

import pytest
import time_machine
from pytest_httpx import HTTPXMock
from pytest_mock import MockerFixture
from sqlalchemy.ext.asyncio import AsyncSession
from typer.testing import CliRunner

from app.cli import app
from app.commands import delete_terminated_orgs
from app.conf import Settings
from app.db.models import ClientAccount, Organization
from app.enums import OrganizationStatus
from app.notifications import NotificationDetails
from tests.types import ModelFactory

HEADER = (
    "Organization ID",
    "Operations external ID",
    "Client account external ID",
    "Termination date",
    "Result",
)

# Terminated on 2026-01-15 -> deletable_at 2026-03-01 -> +180 days = 2026-08-28T00:00:00Z
TERMINATED_AT = datetime(2026, 1, 15, 10, 0, tzinfo=UTC)
GRACE_PERIOD_END = "2026-08-28T00:00:00Z"


def mock_optscale_delete(
    httpx_mock: HTTPXMock, settings: Settings, linked_organization_id: str, status_code: int = 204
) -> None:
    httpx_mock.add_response(
        method="DELETE",
        url=f"{settings.optscale_rest_api_base_url}/organizations/{linked_organization_id}",
        status_code=status_code,
        is_reusable=True,
    )


def test_grace_period_defaults_to_180_days(monkeypatch: pytest.MonkeyPatch) -> None:
    """The organization deletion grace period defaults to 180 days."""
    monkeypatch.delenv("FFC_EXT_ORGANIZATION_DELETION_GRACE_PERIOD_DAYS", raising=False)
    assert Settings().organization_deletion_grace_period_days == 180


def test_grace_period_is_read_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """The organization deletion grace period is read from its environment variable."""
    monkeypatch.setenv("FFC_EXT_ORGANIZATION_DELETION_GRACE_PERIOD_DAYS", "30")
    assert Settings().organization_deletion_grace_period_days == 30


@time_machine.travel(GRACE_PERIOD_END, tick=False)
async def test_main_does_nothing_when_no_organization_is_deletable(
    mocker: MockerFixture,
    test_settings: Settings,
    db_session: AsyncSession,
    organization_factory: ModelFactory[Organization],
) -> None:
    """Non-terminated orgs and orgs still in their grace period are untouched and no
    notification is sent."""
    mocked_send_info = mocker.patch("app.commands.delete_terminated_orgs.send_info")
    mocked_send_warning = mocker.patch("app.commands.delete_terminated_orgs.send_warning")
    active = await organization_factory(operations_external_id="AGR-0001")
    in_grace_period = await organization_factory(
        operations_external_id="AGR-0002",
        status=OrganizationStatus.TERMINATED,
        terminated_at=datetime(2026, 2, 1, tzinfo=UTC),
    )

    await delete_terminated_orgs.main(test_settings)

    await db_session.refresh(active)
    await db_session.refresh(in_grace_period)
    assert active.status == OrganizationStatus.ACTIVE
    assert in_grace_period.status == OrganizationStatus.TERMINATED
    mocked_send_info.assert_not_awaited()
    mocked_send_warning.assert_not_awaited()


@pytest.mark.parametrize(
    ("now", "expected_status"),
    [
        ("2026-08-27T23:59:59Z", OrganizationStatus.TERMINATED),
        (GRACE_PERIOD_END, OrganizationStatus.DELETED),
    ],
)
async def test_main_deletes_only_after_deletable_at_plus_grace_period(
    mocker: MockerFixture,
    httpx_mock: HTTPXMock,
    test_settings: Settings,
    db_session: AsyncSession,
    organization_factory: ModelFactory[Organization],
    now: str,
    expected_status: OrganizationStatus,
) -> None:
    """An organization is deleted only once `deletable_at` plus the grace period has passed."""
    mocker.patch("app.commands.delete_terminated_orgs.send_info")
    org = await organization_factory(
        status=OrganizationStatus.TERMINATED,
        terminated_at=TERMINATED_AT,
        linked_organization_id="linked-org-1",
    )
    if expected_status == OrganizationStatus.DELETED:
        mock_optscale_delete(httpx_mock, test_settings, "linked-org-1")

    with time_machine.travel(now, tick=False):
        await delete_terminated_orgs.main(test_settings)

    await db_session.refresh(org)
    assert org.status == expected_status


@pytest.mark.parametrize(
    ("terminated_at", "expected_status"),
    [
        (datetime(2026, 1, 31, 23, 59, 59, tzinfo=UTC), OrganizationStatus.DELETED),
        (datetime(2026, 2, 1, tzinfo=UTC), OrganizationStatus.TERMINATED),
    ],
)
@time_machine.travel(GRACE_PERIOD_END, tick=False)
async def test_main_selects_organizations_by_exact_termination_cutoff(
    mocker: MockerFixture,
    httpx_mock: HTTPXMock,
    test_settings: Settings,
    db_session: AsyncSession,
    organization_factory: ModelFactory[Organization],
    terminated_at: datetime,
    expected_status: OrganizationStatus,
) -> None:
    """Only organizations terminated before the exact cutoff derived from the grace period
    are selected for deletion."""
    mocker.patch("app.commands.delete_terminated_orgs.send_info")
    org = await organization_factory(
        status=OrganizationStatus.TERMINATED,
        terminated_at=terminated_at,
        linked_organization_id="linked-org-1",
    )
    if expected_status == OrganizationStatus.DELETED:
        mock_optscale_delete(httpx_mock, test_settings, "linked-org-1")

    await delete_terminated_orgs.main(test_settings)

    await db_session.refresh(org)
    assert org.status == expected_status


@time_machine.travel(GRACE_PERIOD_END, tick=False)
async def test_main_uses_configured_grace_period(
    mocker: MockerFixture,
    monkeypatch: pytest.MonkeyPatch,
    httpx_mock: HTTPXMock,
    test_settings: Settings,
    db_session: AsyncSession,
    organization_factory: ModelFactory[Organization],
) -> None:
    """With a shorter grace period, organizations become deletable earlier."""
    mocker.patch("app.commands.delete_terminated_orgs.send_info")
    monkeypatch.setattr(test_settings, "organization_deletion_grace_period_days", 30)
    # deletable_at 2026-07-01 + 30 days = 2026-07-31, already passed
    org = await organization_factory(
        status=OrganizationStatus.TERMINATED,
        terminated_at=datetime(2026, 5, 20, tzinfo=UTC),
        linked_organization_id="linked-org-1",
    )
    mock_optscale_delete(httpx_mock, test_settings, "linked-org-1")

    await delete_terminated_orgs.main(test_settings)

    await db_session.refresh(org)
    assert org.status == OrganizationStatus.DELETED


@time_machine.travel(GRACE_PERIOD_END, tick=False)
async def test_main_sends_info_notification_with_deleted_organizations(
    mocker: MockerFixture,
    httpx_mock: HTTPXMock,
    test_settings: Settings,
    db_session: AsyncSession,
    organization_factory: ModelFactory[Organization],
    client_account_factory: ModelFactory[ClientAccount],
) -> None:
    """Deleted organizations are reported with a ✅ in an info notification."""
    mocked_send_info = mocker.patch("app.commands.delete_terminated_orgs.send_info")
    client_account = await client_account_factory(external_id="ACC-1111-2222")
    with_account = await organization_factory(
        operations_external_id="AGR-0001",
        status=OrganizationStatus.TERMINATED,
        terminated_at=TERMINATED_AT,
        linked_organization_id="linked-org-1",
        client_account=client_account,
    )
    not_linked = await organization_factory(
        operations_external_id="AGR-0002",
        status=OrganizationStatus.TERMINATED,
        terminated_at=datetime(2026, 1, 10, tzinfo=UTC),
    )
    mock_optscale_delete(httpx_mock, test_settings, "linked-org-1")

    await delete_terminated_orgs.main(test_settings)

    await db_session.refresh(with_account)
    await db_session.refresh(not_linked)
    assert with_account.status == OrganizationStatus.DELETED
    assert not_linked.status == OrganizationStatus.DELETED
    mocked_send_info.assert_awaited_once()
    title, text = mocked_send_info.await_args.args
    details: NotificationDetails = mocked_send_info.await_args.kwargs["details"]
    assert title == "Delete Terminated Organizations"
    assert text == (
        "2 of 2 terminated organizations past their 180 days grace period have been deleted."
    )
    assert details.header == HEADER
    assert details.rows == [
        (not_linked.id, "AGR-0002", "-", "2026-01-10", "✅"),
        (with_account.id, "AGR-0001", "ACC-1111-2222", "2026-01-15", "✅"),
    ]


@time_machine.travel(GRACE_PERIOD_END, tick=False)
async def test_main_continues_after_a_failed_deletion(
    mocker: MockerFixture,
    httpx_mock: HTTPXMock,
    test_settings: Settings,
    db_session: AsyncSession,
    organization_factory: ModelFactory[Organization],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A failed deletion is logged and reported with ❌ in a warning notification, while the
    other organizations are still deleted."""
    mocked_send_warning = mocker.patch("app.commands.delete_terminated_orgs.send_warning")
    failing = await organization_factory(
        operations_external_id="AGR-0001",
        status=OrganizationStatus.TERMINATED,
        terminated_at=datetime(2026, 1, 10, tzinfo=UTC),
        linked_organization_id="linked-org-fail",
    )
    succeeding = await organization_factory(
        operations_external_id="AGR-0002",
        status=OrganizationStatus.TERMINATED,
        terminated_at=TERMINATED_AT,
        linked_organization_id="linked-org-ok",
    )
    mock_optscale_delete(httpx_mock, test_settings, "linked-org-fail", status_code=400)
    mock_optscale_delete(httpx_mock, test_settings, "linked-org-ok")

    await delete_terminated_orgs.main(test_settings)

    await db_session.refresh(failing)
    await db_session.refresh(succeeding)
    assert failing.status == OrganizationStatus.TERMINATED
    assert succeeding.status == OrganizationStatus.DELETED
    assert f"Failed to delete organization {failing.id}" in caplog.messages
    mocked_send_warning.assert_awaited_once()
    text = mocked_send_warning.await_args.args[1]
    details: NotificationDetails = mocked_send_warning.await_args.kwargs["details"]
    assert text == (
        "1 of 2 terminated organizations past their 180 days grace period have been deleted."
    )
    failed_row, succeeded_row = details.rows
    assert failed_row[0] == failing.id
    assert failed_row[4].startswith("❌ HTTPStatusError: Client error '400 Bad Request'")
    assert len(failed_row[4]) <= delete_terminated_orgs.MAX_ERROR_LENGTH + 2
    assert succeeded_row == (succeeding.id, "AGR-0002", "-", "2026-01-15", "✅")


@time_machine.travel(GRACE_PERIOD_END, tick=False)
async def test_main_deletes_from_db_when_linked_organization_is_not_found(
    mocker: MockerFixture,
    httpx_mock: HTTPXMock,
    test_settings: Settings,
    db_session: AsyncSession,
    organization_factory: ModelFactory[Organization],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """When Optscale returns 404 for the linked organization, a warning is logged and the
    organization is still deleted from the database and reported as deleted."""
    mocked_send_info = mocker.patch("app.commands.delete_terminated_orgs.send_info")
    org = await organization_factory(
        operations_external_id="AGR-0001",
        status=OrganizationStatus.TERMINATED,
        terminated_at=TERMINATED_AT,
        linked_organization_id="linked-org-missing",
    )
    mock_optscale_delete(httpx_mock, test_settings, "linked-org-missing", status_code=404)

    await delete_terminated_orgs.main(test_settings)

    await db_session.refresh(org)
    assert org.status == OrganizationStatus.DELETED
    assert (
        f"Linked organization linked-org-missing of organization {org.id} not found in "
        "Optscale, deleting it only from the database"
    ) in caplog.messages
    mocked_send_info.assert_awaited_once()
    details: NotificationDetails = mocked_send_info.await_args.kwargs["details"]
    assert details.rows == [(org.id, "AGR-0001", "-", "2026-01-15", "✅")]


@time_machine.travel(GRACE_PERIOD_END, tick=False)
async def test_main_second_run_does_not_notify_again(
    mocker: MockerFixture,
    httpx_mock: HTTPXMock,
    test_settings: Settings,
    organization_factory: ModelFactory[Organization],
) -> None:
    """Running the job twice in a row doesn't fail or notify about already deleted orgs."""
    mocked_send_info = mocker.patch("app.commands.delete_terminated_orgs.send_info")
    await organization_factory(
        status=OrganizationStatus.TERMINATED,
        terminated_at=TERMINATED_AT,
        linked_organization_id="linked-org-1",
    )
    mock_optscale_delete(httpx_mock, test_settings, "linked-org-1")

    await delete_terminated_orgs.main(test_settings)
    await delete_terminated_orgs.main(test_settings)

    mocked_send_info.assert_awaited_once()
    assert len(httpx_mock.get_requests()) == 1


def test_command(mocker: MockerFixture, test_settings: Settings) -> None:
    """The `delete-terminated-orgs` CLI command runs `main` with the settings."""
    mock_main_coro = mocker.MagicMock()
    mock_main = mocker.MagicMock(return_value=mock_main_coro)
    mocker.patch("app.commands.delete_terminated_orgs.main", mock_main)
    mock_run = mocker.patch("app.commands.delete_terminated_orgs.asyncio.run")

    result = CliRunner().invoke(app, ["delete-terminated-orgs"])

    assert result.exit_code == 0
    mock_run.assert_called_once_with(mock_main_coro)
    mock_main.assert_called_once_with(test_settings)


@time_machine.travel(GRACE_PERIOD_END, tick=False)
async def test_main_reports_termination_date_in_utc(
    mocker: MockerFixture,
    test_settings: Settings,
    organization_factory: ModelFactory[Organization],
) -> None:
    """The termination date in the notification is the UTC date of `terminated_at`."""
    mocked_send_info = mocker.patch("app.commands.delete_terminated_orgs.send_info")
    # 2026-01-10 22:30 UTC-3 is 2026-01-11 01:30 UTC
    org = await organization_factory(
        operations_external_id="AGR-0001",
        status=OrganizationStatus.TERMINATED,
        terminated_at=datetime(2026, 1, 10, 22, 30, tzinfo=timezone(-timedelta(hours=3))),
    )

    await delete_terminated_orgs.main(test_settings)

    details: NotificationDetails = mocked_send_info.await_args.kwargs["details"]
    assert details.rows == [(org.id, "AGR-0001", "-", "2026-01-11", "✅")]
