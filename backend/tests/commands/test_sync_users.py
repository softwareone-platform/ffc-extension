import pytest
import typer
from pytest_httpx import HTTPXMock
from pytest_mock import MockerFixture, MockType
from sqlalchemy.ext.asyncio import AsyncSession
from typer.testing import CliRunner

from app.cli import app
from app.commands import sync_users
from app.conf import Settings
from app.db.models import Account, User
from app.enums import UserStatus
from tests.types import ModelFactory

pytestmark = pytest.mark.usefixtures("mock_sync_users_installation_client")


async def test_main_uses_operations_account_installation(
    test_settings: Settings,
    operations_account: Account,
    mock_sync_users_installation_client: MockType,
) -> None:
    """The installation client is built from the Operations account's external ID."""
    await sync_users.main(test_settings)

    mock_sync_users_installation_client.assert_called_once_with(operations_account.external_id)


async def test_main_updates_changed_user_fields(
    test_settings: Settings,
    db_session: AsyncSession,
    operations_account: Account,
    user_factory: ModelFactory[User],
    httpx_mock: HTTPXMock,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Name, email and icon of an active user are replaced with the values from MPT."""
    user = await user_factory(
        external_id="USR-0000-0001", name="Old Name", email="old@example.com", icon=None
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.mpt_api_base_url}/accounts/users/USR-0000-0001",
        json={
            "id": "USR-0000-0001",
            "name": "New Name",
            "email": "new@example.com",
            "icon": "/v1/accounts/users/USR-0000-0001/icon",
        },
    )

    with caplog.at_level("INFO"):
        await sync_users.main(test_settings)

    await db_session.refresh(user)
    assert user.name == "New Name"
    assert user.email == "new@example.com"
    assert user.icon == "/v1/accounts/users/USR-0000-0001/icon"
    assert user.status == UserStatus.ACTIVE
    assert "Users updated: 1, unchanged: 0, disabled: 0, failed: 0." in caplog.text


async def test_main_leaves_up_to_date_user_untouched(
    test_settings: Settings,
    db_session: AsyncSession,
    operations_account: Account,
    user_factory: ModelFactory[User],
    httpx_mock: HTTPXMock,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A user whose data already matches MPT is counted as unchanged and not updated."""
    user = await user_factory(
        external_id="USR-0000-0002",
        name="Same Name",
        email="same@example.com",
        icon="/v1/accounts/users/USR-0000-0002/icon",
    )
    updated_at = user.updated_at
    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.mpt_api_base_url}/accounts/users/USR-0000-0002",
        json={
            "id": "USR-0000-0002",
            "name": "Same Name",
            "email": "same@example.com",
            "icon": "/v1/accounts/users/USR-0000-0002/icon",
        },
    )

    with caplog.at_level("INFO"):
        await sync_users.main(test_settings)

    await db_session.refresh(user)
    assert user.updated_at == updated_at
    assert "Users updated: 0, unchanged: 1, disabled: 0, failed: 0." in caplog.text


async def test_main_disables_user_not_found_in_mpt(
    test_settings: Settings,
    db_session: AsyncSession,
    operations_account: Account,
    user_factory: ModelFactory[User],
    httpx_mock: HTTPXMock,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """An active user for which MPT returns 404 is disabled."""
    user = await user_factory(external_id="USR-0000-0003")
    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.mpt_api_base_url}/accounts/users/USR-0000-0003",
        status_code=404,
    )

    with caplog.at_level("INFO"):
        await sync_users.main(test_settings)

    await db_session.refresh(user)
    assert user.status == UserStatus.DISABLED
    assert "Users updated: 0, unchanged: 0, disabled: 1, failed: 0." in caplog.text


async def test_main_counts_failed_user_and_continues(
    test_settings: Settings,
    db_session: AsyncSession,
    operations_account: Account,
    user_factory: ModelFactory[User],
    httpx_mock: HTTPXMock,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A user that MPT fails to return (non-404 error) is left as is and the next user is
    still synced."""
    failing = await user_factory(external_id="USR-0000-0004", name="Failing")
    synced = await user_factory(external_id="USR-0000-0005", name="Old Name")
    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.mpt_api_base_url}/accounts/users/USR-0000-0004",
        status_code=500,
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.mpt_api_base_url}/accounts/users/USR-0000-0005",
        json={"id": "USR-0000-0005", "name": "New Name", "email": synced.email, "icon": None},
    )

    with caplog.at_level("INFO"):
        await sync_users.main(test_settings)

    await db_session.refresh(failing)
    await db_session.refresh(synced)
    assert failing.name == "Failing"
    assert failing.status == UserStatus.ACTIVE
    assert synced.name == "New Name"
    assert f"{failing.id}: Failed to get user USR-0000-0004" in caplog.text
    assert "Users updated: 1, unchanged: 0, disabled: 0, failed: 1." in caplog.text


@pytest.mark.parametrize("user_status", [UserStatus.DISABLED, UserStatus.DELETED, UserStatus.DRAFT])
async def test_main_skips_non_active_users(
    test_settings: Settings,
    operations_account: Account,
    user_factory: ModelFactory[User],
    user_status: UserStatus,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Users that aren't active are never fetched from MPT."""
    await user_factory(external_id="USR-0000-0006", status=user_status)

    with caplog.at_level("INFO"):
        await sync_users.main(test_settings)

    assert "Users updated: 0, unchanged: 0, disabled: 0, failed: 0." in caplog.text


async def test_main_dry_run_persists_nothing(
    test_settings: Settings,
    db_session: AsyncSession,
    operations_account: Account,
    user_factory: ModelFactory[User],
    httpx_mock: HTTPXMock,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """With `dry_run` the changes are reported but rolled back."""
    user = await user_factory(external_id="USR-0000-0007", name="Old Name")
    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.mpt_api_base_url}/accounts/users/USR-0000-0007",
        status_code=404,
    )

    with caplog.at_level("INFO"):
        await sync_users.main(test_settings, dry_run=True)

    await db_session.refresh(user)
    assert user.status == UserStatus.ACTIVE
    assert (
        "Dry run, nothing persisted. Users updated: 0, unchanged: 0, disabled: 1, failed: 0."
        in caplog.text
    )


async def test_main_exits_when_operations_account_missing(
    test_settings: Settings,
    mock_sync_users_installation_client: MockType,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Without an Operations account the command logs an error and exits with code 1."""
    with pytest.raises(typer.Exit) as exc_info:
        await sync_users.main(test_settings)

    assert exc_info.value.exit_code == 1
    assert "Operations account not found. Cannot sync users." in caplog.text
    mock_sync_users_installation_client.assert_not_called()


@pytest.mark.parametrize(
    ("args", "expected_dry_run"),
    [
        pytest.param([], False, id="default"),
        pytest.param(["--dry-run"], True, id="dry-run"),
    ],
)
def test_command_runs_main_with_settings_and_dry_run_flag(
    mocker: MockerFixture,
    test_settings: Settings,
    args: list[str],
    expected_dry_run: bool,
) -> None:
    """The CLI command runs `main` with the settings and the `--dry-run` flag."""
    mock_main_coro = mocker.MagicMock()
    mock_main = mocker.MagicMock(return_value=mock_main_coro)
    mocker.patch("app.commands.sync_users.main", mock_main)
    mock_run = mocker.patch("app.commands.sync_users.asyncio.run")

    result = CliRunner().invoke(app, ["sync-users", *args])

    assert result.exit_code == 0
    mock_run.assert_called_once_with(mock_main_coro)
    mock_main.assert_called_once_with(test_settings, expected_dry_run)
