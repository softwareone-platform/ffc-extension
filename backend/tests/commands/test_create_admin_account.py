import pytest
from app.cli import app
from app.commands.create_admin_account import create_admin_account
from app.conf import Settings
from app.db.handlers import AccountHandler
from app.db.models import Account
from app.enums import AccountStatus, AccountType
from pytest_mock import MockerFixture
from sqlalchemy.ext.asyncio import AsyncSession
from typer.testing import CliRunner


async def test_create_admin_account(
    test_settings: Settings,
    db_session: AsyncSession,
    capsys: pytest.CaptureFixture,
):
    await create_admin_account(
        test_settings,
        "ACC-1234-5678",
    )
    captured = capsys.readouterr()
    assert "The Admin Account has been created" in captured.out.replace("\n", "")
    account_handler = AccountHandler(db_session)
    assert (
        await account_handler.count(
            where_clauses=[
                Account.type == AccountType.ADMIN,
                Account.status == AccountStatus.ACTIVE,
                Account.external_id == "ACC-1234-5678",
            ]
        )
        == 1
    )


async def test_create_admin_account_exist(
    test_settings: Settings,
    db_session: AsyncSession,
    capsys: pytest.CaptureFixture,
):
    account_handler = AccountHandler(db_session)
    await account_handler.create(
        Account(
            name="SWO",
            type=AccountType.ADMIN,
            status=AccountStatus.ACTIVE,
            external_id="ACC-1234-5678",
        )
    )
    await db_session.commit()
    await create_admin_account(
        test_settings,
        "ACC-1234-5678",
    )
    captured = capsys.readouterr()
    assert "The Admin Account already exist" in captured.out.replace("\n", "")
    assert (
        await account_handler.count(
            where_clauses=[
                Account.type == AccountType.ADMIN,
                Account.status == AccountStatus.ACTIVE,
            ]
        )
        == 1
    )


def test_create_admin_account_command(
    mocker: MockerFixture,
    test_settings: Settings,
):
    mocker.patch("app.cli.get_settings", return_value=test_settings)
    mock_create_coro = mocker.MagicMock()
    mock_create_admin_account = mocker.MagicMock(return_value=mock_create_coro)

    mocker.patch(
        "app.commands.create_admin_account.create_admin_account",
        mock_create_admin_account,
    )
    mock_run = mocker.patch("app.commands.create_admin_account.asyncio.run")
    runner = CliRunner()

    # Run the command
    result = runner.invoke(
        app,
        ["create-admin-account", "ACC-1234-5678"],
    )
    assert result.exit_code == 0
    mock_run.assert_called_once_with(mock_create_coro)

    mock_create_admin_account.assert_called_once_with(
        test_settings,
        "ACC-1234-5678",
    )
