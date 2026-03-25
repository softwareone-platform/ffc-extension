from datetime import UTC, datetime, timedelta

import pytest
from pytest_mock import MockerFixture
from sqlalchemy.ext.asyncio import AsyncSession
from typer.testing import CliRunner

from app.cli import app
from app.commands.check_expired_invitations import check_expired_invitations
from app.conf import Settings
from app.db.models import Account, AccountUser, User
from app.enums import AccountUserStatus, UserStatus
from tests.types import ModelFactory


async def test_check_expired_invitation(
    mocker: MockerFixture,
    caplog: pytest.LogCaptureFixture,
    test_settings: Settings,
    db_session: AsyncSession,
    operations_account: Account,
    affiliate_account: Account,
    user_factory: ModelFactory[User],
    accountuser_factory: ModelFactory[AccountUser],
):
    user = await user_factory(
        name="Peter Parker",
        email="peter.parker@spiderman.com",
        status=UserStatus.ACTIVE,
    )
    active = await accountuser_factory(
        account_id=operations_account.id,
        user_id=user.id,
        status=AccountUserStatus.ACTIVE,
        invitation_token_expires_at=datetime.now(UTC) - timedelta(days=1),
    )
    deleted = await accountuser_factory(
        account_id=operations_account.id,
        user_id=user.id,
        status=AccountUserStatus.DELETED,
        invitation_token_expires_at=datetime.now(UTC) - timedelta(days=1),
    )
    invitation_expired = await accountuser_factory(
        account_id=operations_account.id,
        user_id=user.id,
        status=AccountUserStatus.INVITATION_EXPIRED,
        invitation_token_expires_at=datetime.now(UTC) - timedelta(days=1),
    )
    expired_invited_1 = await accountuser_factory(
        account_id=operations_account.id,
        user_id=user.id,
        status=AccountUserStatus.INVITED,
        invitation_token_expires_at=datetime.now(UTC) - timedelta(days=1),
    )
    expired_invited_2 = await accountuser_factory(
        account_id=affiliate_account.id,
        user_id=user.id,
        status=AccountUserStatus.INVITED,
        invitation_token_expires_at=datetime.now(UTC) - timedelta(days=1),
    )

    mocked_send_info = mocker.patch(
        "app.commands.check_expired_invitations.send_info",
    )

    with caplog.at_level("INFO"):
        await check_expired_invitations(test_settings)

    assert "2 Invitations" in caplog.text

    await db_session.refresh(active)
    assert active.status == AccountUserStatus.ACTIVE

    await db_session.refresh(deleted)
    assert deleted.status == AccountUserStatus.DELETED

    await db_session.refresh(invitation_expired)
    assert invitation_expired.status == AccountUserStatus.INVITATION_EXPIRED

    await db_session.refresh(expired_invited_1)
    assert expired_invited_1.status == AccountUserStatus.INVITATION_EXPIRED

    await db_session.refresh(expired_invited_2)
    assert expired_invited_2.status == AccountUserStatus.INVITATION_EXPIRED

    assert mocked_send_info.await_count == 1
    assert mocked_send_info.await_args is not None
    assert mocked_send_info.await_args.args == (
        "Expire Invitations Success",
        "2 Invitations have been successfully transitioned to `invitation-expired`.",
    )
    assert mocked_send_info.await_args.kwargs["details"].header == (
        "User ID",
        "Name",
        "Email",
        "Account ID",
        "Account Name",
    )
    assert mocked_send_info.await_args.kwargs["details"].rows == [
        (user.id, user.name, user.email, affiliate_account.id, affiliate_account.name),
        (user.id, user.name, user.email, operations_account.id, operations_account.name),
    ]


def test_invite_user_command(
    mocker: MockerFixture,
    test_settings: Settings,
):
    mock_check_coro = mocker.MagicMock()
    mock_check = mocker.MagicMock(return_value=mock_check_coro)

    mocker.patch("app.commands.check_expired_invitations.check_expired_invitations", mock_check)
    mock_run = mocker.patch("app.commands.invite_user.asyncio.run")
    runner = CliRunner()

    result = runner.invoke(app, ["check-expired-invitations"])
    assert result.exit_code == 0
    mock_run.assert_called_once_with(mock_check_coro)

    mock_check.assert_called_once_with(test_settings)
