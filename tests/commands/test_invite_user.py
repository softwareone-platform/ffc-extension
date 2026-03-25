import shlex
from datetime import UTC, datetime, timedelta

import pytest
import time_machine
from pytest_mock import MockerFixture
from sqlalchemy.ext.asyncio import AsyncSession
from typer import Abort
from typer.testing import CliRunner

from app.cli import app
from app.commands.invite_user import invite_user
from app.conf import Settings
from app.db.handlers import AccountUserHandler, UserHandler
from app.db.models import Account, AccountUser, User
from app.enums import AccountStatus, AccountUserStatus, UserStatus
from tests.types import ModelFactory


@time_machine.travel("2025-03-07T10:00:00Z", tick=False)
async def test_invite_user(
    mocker: MockerFixture,
    test_settings: Settings,
    db_session: AsyncSession,
    operations_account: Account,
    capsys: pytest.CaptureFixture,
):
    mocked_send_email = mocker.patch("app.commands.invite_user.send_email")
    await invite_user(test_settings, "test@example.com", "Test User", None)

    captured = capsys.readouterr()
    assert "invited successfully" in captured.out.replace("\n", "")

    user_handler = UserHandler(db_session)
    user = await user_handler.first(where_clauses=[User.email == "test@example.com"])
    assert user is not None
    assert user.status == UserStatus.DRAFT
    assert user.name == "Test User"
    accountuser_handler = AccountUserHandler(db_session)
    account_user = await accountuser_handler.get_account_user(operations_account.id, user.id)
    assert account_user is not None
    assert account_user.status == AccountUserStatus.INVITED
    assert account_user.invitation_token is not None
    assert account_user.invitation_token_expires_at == (
        datetime.now(UTC) + timedelta(days=test_settings.invitation_token_expires_days)
    )
    mocked_send_email.assert_called_once_with(
        test_settings,
        user.email,
        user.name,
        f"Join the FinOps for Cloud {operations_account.name} Account!",
        mocker.ANY,
    )


@time_machine.travel("2025-03-07T10:00:00Z", tick=False)
async def test_invite_user_already_invited_force(
    mocker: MockerFixture,
    test_settings: Settings,
    db_session: AsyncSession,
    operations_account: Account,
    user_factory: ModelFactory[User],
    accountuser_factory: ModelFactory[AccountUser],
    capsys: pytest.CaptureFixture,
):
    mocked_send_email = mocker.patch("app.commands.invite_user.send_email")
    user = await user_factory(
        email="test@example.com",
        name="Test User",
        status=UserStatus.DRAFT,
    )

    original_invitation_token = "an invitation token"
    original_invitation_token_expires_at = datetime(2025, 3, 7, 9, 0, 0, tzinfo=UTC)

    await accountuser_factory(
        user_id=user.id,
        account_id=operations_account.id,
        status=AccountUserStatus.INVITED,
        invitation_token=original_invitation_token,
        invitation_token_expires_at=original_invitation_token_expires_at,
    )

    await invite_user(test_settings, "test@example.com", "Test User", None, True)

    captured = capsys.readouterr()

    assert "invitation token regenerated successfully" in captured.out.replace("\n", "")

    db_session.expunge_all()

    user_handler = UserHandler(db_session)
    db_user = await user_handler.first(where_clauses=[User.email == "test@example.com"])
    assert db_user is not None
    assert db_user.status == UserStatus.DRAFT
    assert db_user.name == "Test User"

    accountuser_handler = AccountUserHandler(db_session)
    db_account_user = await accountuser_handler.get_account_user(operations_account.id, user.id)

    assert db_account_user is not None
    assert db_account_user.status == AccountUserStatus.INVITED
    assert db_account_user.invitation_token != original_invitation_token
    assert db_account_user.invitation_token_expires_at != original_invitation_token_expires_at
    assert db_account_user.invitation_token_expires_at == (
        datetime.now(UTC) + timedelta(days=test_settings.invitation_token_expires_days)
    )
    mocked_send_email.assert_not_called()


@time_machine.travel("2025-03-07T10:00:00Z", tick=False)
async def test_invite_user_already_invited(
    mocker: MockerFixture,
    test_settings: Settings,
    db_session: AsyncSession,
    operations_account: Account,
    user_factory: ModelFactory[User],
    accountuser_factory: ModelFactory[AccountUser],
    capsys: pytest.CaptureFixture,
):
    mocked_send_email = mocker.patch("app.commands.invite_user.send_email")
    user = await user_factory(
        email="test@example.com",
        name="Test User",
        status=UserStatus.DRAFT,
    )
    account_user = await accountuser_factory(
        user_id=user.id,
        account_id=operations_account.id,
        status=AccountUserStatus.INVITED,
        invitation_token="an invitation token",
        invitation_token_expires_at=datetime(2025, 3, 7, 9, 0, 0, tzinfo=UTC),
    )

    await invite_user(test_settings, "test@example.com", "Test User", None, False)

    captured = capsys.readouterr()

    assert "has already been invited!" in captured.out.replace("\n", "")

    db_session.expunge_all()

    user_handler = UserHandler(db_session)
    db_user = await user_handler.first(where_clauses=[User.email == "test@example.com"])
    assert db_user is not None
    assert db_user.status == UserStatus.DRAFT
    assert db_user.name == "Test User"
    accountuser_handler = AccountUserHandler(db_session)
    db_account_user = await accountuser_handler.get_account_user(operations_account.id, user.id)
    assert db_account_user is not None
    assert db_account_user.status == AccountUserStatus.INVITED
    assert db_account_user.invitation_token == account_user.invitation_token
    assert db_account_user.invitation_token_expires_at == account_user.invitation_token_expires_at
    mocked_send_email.assert_not_called()


async def test_invite_user_user_disabled(
    mocker: MockerFixture,
    test_settings: Settings,
    user_factory: ModelFactory[User],
    operations_account: Account,
    capsys: pytest.CaptureFixture,
):
    mocked_send_email = mocker.patch("app.commands.invite_user.send_email")
    await user_factory(
        email="test@example.com",
        name="Test User",
        status=UserStatus.DISABLED,
    )

    with pytest.raises(Abort):
        await invite_user(test_settings, "test@example.com", "Test User", None)

    captured = capsys.readouterr()

    assert "The user test@example.com is disabled." in captured.out.replace("\n", "")
    mocked_send_email.assert_not_called()


@time_machine.travel("2025-03-07T10:00:00Z", tick=False)
async def test_invite_user_non_default_account(
    mocker: MockerFixture,
    test_settings: Settings,
    db_session: AsyncSession,
    account_factory: ModelFactory[Account],
    capsys: pytest.CaptureFixture,
):
    mocked_send_email = mocker.patch("app.commands.invite_user.send_email")
    account = await account_factory()

    await invite_user(test_settings, "test@example.com", "Test User", account.id)

    captured = capsys.readouterr()

    assert "invited successfully" in captured.out.replace("\n", "")

    user_handler = UserHandler(db_session)
    user = await user_handler.first(where_clauses=[User.email == "test@example.com"])
    assert user is not None
    assert user.status == UserStatus.DRAFT
    assert user.name == "Test User"
    accountuser_handler = AccountUserHandler(db_session)
    account_user = await accountuser_handler.get_account_user(account.id, user.id)
    assert account_user is not None
    assert account_user.status == AccountUserStatus.INVITED
    assert account_user.invitation_token is not None
    assert account_user.invitation_token_expires_at == (
        datetime.now(UTC) + timedelta(days=test_settings.invitation_token_expires_days)
    )
    mocked_send_email.assert_called_once_with(
        test_settings,
        user.email,
        user.name,
        f"Join the FinOps for Cloud {account.name} Account!",
        mocker.ANY,
    )


@pytest.mark.parametrize(
    "account_status",
    [AccountStatus.DELETED, AccountStatus.DISABLED],
)
async def test_invite_user_non_default_account_not_active(
    mocker: MockerFixture,
    test_settings: Settings,
    account_factory: ModelFactory[Account],
    account_status: AccountStatus,
    capsys: pytest.CaptureFixture,
):
    mocked_send_email = mocker.patch("app.commands.invite_user.send_email")
    account = await account_factory(status=account_status)
    with pytest.raises(Abort):
        await invite_user(test_settings, "test@example.com", "Test User", account.id)
    captured = capsys.readouterr()
    stderr_output = captured.out.replace("\n", "")
    assert f"No Active Account with ID {account.id} has been found." in stderr_output
    mocked_send_email.assert_not_called()


async def test_invite_user_no_operations_account(
    test_settings: Settings,
    db_session: AsyncSession,
    capsys: pytest.CaptureFixture,
):
    with pytest.raises(Abort):
        await invite_user(test_settings, "test@example.com", "Test User", None)
    captured = capsys.readouterr()
    assert "No Active Operations Account has been found." in captured.out.replace("\n", "")


def test_invite_user_invalid_email():
    runner = CliRunner()
    result = runner.invoke(app, shlex.split("invite-user invalid-email UserName"))
    assert result.exit_code != 0
    assert "Invalid value for 'EMAIL'" in result.stderr.replace("\n", "")


def test_invite_user_command(
    mocker: MockerFixture,
    test_settings: Settings,
):
    mock_invite_coro = mocker.MagicMock()
    mock_invite_user = mocker.MagicMock(return_value=mock_invite_coro)

    mocker.patch("app.commands.invite_user.invite_user", mock_invite_user)
    mock_run = mocker.patch("app.commands.invite_user.asyncio.run")
    runner = CliRunner()

    # Run the command
    result = runner.invoke(
        app,
        ["invite-user", "test@example.com", "Test User", "-a", "FACC-1234"],
    )
    assert result.exit_code == 0
    mock_run.assert_called_once_with(mock_invite_coro)

    mock_invite_user.assert_called_once_with(
        test_settings, "test@example.com", "Test User", "FACC-1234", False
    )


def test_invite_user_command_with_update(
    mocker: MockerFixture,
    test_settings: Settings,
):
    mock_invite_coro = mocker.MagicMock()
    mock_invite_user = mocker.MagicMock(return_value=mock_invite_coro)

    mocker.patch("app.commands.invite_user.invite_user", mock_invite_user)
    mock_run = mocker.patch("app.commands.invite_user.asyncio.run")
    runner = CliRunner()

    # Run the command
    result = runner.invoke(
        app,
        ["invite-user", "test@example.com", "Test User", "-a", "FACC-1234", "--force"],
    )
    assert result.exit_code == 0
    mock_run.assert_called_once_with(mock_invite_coro)

    mock_invite_user.assert_called_once_with(
        test_settings, "test@example.com", "Test User", "FACC-1234", True
    )
