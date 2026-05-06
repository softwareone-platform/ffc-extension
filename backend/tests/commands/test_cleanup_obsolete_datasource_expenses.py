import logging
from datetime import UTC, datetime, timedelta

import pytest
import time_machine
from pytest_mock import MockerFixture
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from typer.testing import CliRunner

from app.cli import app
from app.commands import cleanup_obsolete_datasource_expenses
from app.conf import Settings
from app.db.models import DatasourceExpense, Organization
from tests.types import ModelFactory


async def test_command_no_datasource_expenses(
    db_session: AsyncSession,
    test_settings: Settings,
    caplog: pytest.LogCaptureFixture,
):
    with caplog.at_level(logging.INFO):
        await cleanup_obsolete_datasource_expenses.main(test_settings)

    num_ds_expenses_in_db = await db_session.scalar(select(func.count(DatasourceExpense.id)))
    assert num_ds_expenses_in_db == 0

    assert caplog.messages == [
        "Fetching obsolete datasource expenses from the database",
        "Found 0 obsolete datasource expenses to delete",
        "No obsolete datasource expenses to delete",
    ]


@time_machine.travel("2025-04-01T10:00:00Z", tick=False)
async def test_command_only_new_datasource_expenses(
    db_session: AsyncSession,
    test_settings: Settings,
    caplog: pytest.LogCaptureFixture,
    organization_factory: ModelFactory[Organization],
    datasource_expense_factory: ModelFactory[DatasourceExpense],
):
    org1 = await organization_factory(operations_external_id="org1")
    await datasource_expense_factory(organization=org1)
    await datasource_expense_factory(
        organization=org1, created_at=datetime.now(UTC) - timedelta(days=100)
    )

    org2 = await organization_factory(operations_external_id="org2")
    await datasource_expense_factory(organization=org2)

    num_ds_expenses_in_db = await db_session.scalar(select(func.count(DatasourceExpense.id)))
    assert num_ds_expenses_in_db == 3

    with caplog.at_level(logging.INFO):
        await cleanup_obsolete_datasource_expenses.main(test_settings)

    assert caplog.messages == [
        "Fetching obsolete datasource expenses from the database",
        "Found 0 obsolete datasource expenses to delete",
        "No obsolete datasource expenses to delete",
    ]

    num_ds_expenses_in_db = await db_session.scalar(select(func.count(DatasourceExpense.id)))
    assert num_ds_expenses_in_db == 3


@time_machine.travel("2025-04-01T10:00:00Z", tick=False)
async def test_command_delete_only_old_datasource_expenses(
    mocker: MockerFixture,
    caplog: pytest.LogCaptureFixture,
    db_session: AsyncSession,
    test_settings: Settings,
    organization_factory: ModelFactory[Organization],
    datasource_expense_factory: ModelFactory[DatasourceExpense],
):
    mocked_send_info = mocker.patch(
        "app.commands.cleanup_obsolete_datasource_expenses.send_info",
    )
    org1 = await organization_factory(operations_external_id="org1")
    await datasource_expense_factory(
        organization=org1,
        created_at=datetime.now(UTC) - timedelta(days=365),
    )
    await datasource_expense_factory(
        organization=org1,
        created_at=datetime.now(UTC) - timedelta(days=250),
    )
    await datasource_expense_factory(
        organization=org1,
        created_at=datetime.now(UTC) - timedelta(days=100),
    )
    await datasource_expense_factory(
        organization=org1,
        created_at=datetime.now(UTC) - timedelta(days=10),
    )

    org2 = await organization_factory(operations_external_id="org2")
    await datasource_expense_factory(
        organization=org2,
        created_at=datetime.now(UTC) - timedelta(days=1000),
    )
    await datasource_expense_factory(
        organization=org2,
        created_at=datetime.now(UTC) - timedelta(days=10),
    )
    await datasource_expense_factory(
        organization=org2,
        created_at=datetime.now(UTC),
    )

    num_ds_expenses_in_db = await db_session.scalar(select(func.count(DatasourceExpense.id)))
    assert num_ds_expenses_in_db == 7

    with caplog.at_level(logging.INFO):
        await cleanup_obsolete_datasource_expenses.main(test_settings)

    assert caplog.messages == [
        "Fetching obsolete datasource expenses from the database",
        "Found 3 obsolete datasource expenses to delete",
        "Deleting 3 obsolete datasource expenses from the database",
        "3 obsolete (older than 2024-10-01T10:00:00+00:00) datasource expenses have been deleted.",
    ]
    mocked_send_info.assert_awaited_once_with(
        "Cleanup Obsolete Datasource Expenses Success",
        "3 obsolete (older than 2024-10-01T10:00:00+00:00) datasource expenses have been deleted.",
    )

    num_ds_expenses_in_db = await db_session.scalar(select(func.count(DatasourceExpense.id)))
    assert num_ds_expenses_in_db == 4


def test_command(mocker: MockerFixture, test_settings: Settings):
    mock_check_coro = mocker.MagicMock()
    mock_check = mocker.MagicMock(return_value=mock_check_coro)

    mocker.patch("app.commands.cleanup_obsolete_datasource_expenses.main", mock_check)
    mock_run = mocker.patch("app.commands.cleanup_obsolete_datasource_expenses.asyncio.run")
    runner = CliRunner()

    result = runner.invoke(app, ["cleanup-obsolete-datasource-expenses"])
    assert result.exit_code == 0
    mock_run.assert_called_once_with(mock_check_coro)

    mock_check.assert_called_once_with(test_settings)
