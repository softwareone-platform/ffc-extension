import logging
import uuid
from datetime import UTC, datetime
from decimal import Decimal

import pytest
import time_machine
from fastapi import status
from pytest_httpx import HTTPXMock
from pytest_mock import MockerFixture
from sqlalchemy.ext.asyncio import AsyncSession
from typer.testing import CliRunner

from app.cli import app
from app.commands import fetch_datasource_expenses
from app.conf import Settings
from app.db.handlers import DatasourceExpenseHandler
from app.db.models import DatasourceExpense, Organization
from app.enums import DatasourceType, OrganizationStatus
from tests.fixtures.mock_api_clients import MockOptscaleClient
from tests.types import ModelFactory


@time_machine.travel("2025-03-20T10:00:00Z", tick=False)
@pytest.mark.parametrize(
    "organization_status",
    [
        OrganizationStatus.ACTIVE,
        OrganizationStatus.CANCELLED,
    ],
)
async def test_create_new_datasource_expenses_single_organization(
    mocker: MockerFixture,
    test_settings: Settings,
    db_session: AsyncSession,
    mock_optscale_client: MockOptscaleClient,
    organization_factory: ModelFactory[Organization],
    organization_status: OrganizationStatus,
    datasource_expense_factory: ModelFactory[DatasourceExpense],
):
    mocker.patch("app.commands.fetch_datasource_expenses.send_info")
    datasource_expense_handler = DatasourceExpenseHandler(db_session)
    organization = await organization_factory(
        linked_organization_id=str(uuid.uuid4()),
        status=organization_status,
    )

    datasource_id1 = str(uuid.uuid4())
    datasource_id2 = str(uuid.uuid4())

    existing_datasource_expense1 = await datasource_expense_factory(
        organization=organization,
        linked_datasource_id=datasource_id1,
        linked_datasource_type=DatasourceType.AZURE_CNR,
        datasource_name="First cloud account",
        datasource_id="123456",
        year=2025,
        month=3,
        day=19,
        total_expenses=Decimal("123.45"),
    )

    mock_optscale_client.mock_fetch_datasources_for_organization(
        organization,
        [
            {
                "id": datasource_id1,
                "name": "First cloud account",
                "details": {"cost": 123.45},
                "account_id": "123456",
            },
            {
                "id": datasource_id2,
                "name": "Second cloud account",
                "details": {"cost": 567.89},
                "account_id": "654321",
            },
        ],
    )

    mock_optscale_client.mock_fetch_daily_expenses_for_organization(
        organization,
        int(datetime(2025, 3, 19, 0, 0, 0, tzinfo=UTC).timestamp()),
        int(datetime(2025, 3, 19, 23, 59, 59, tzinfo=UTC).timestamp()),
        {
            datasource_id1: {
                "total": 12.34,
                "id": datasource_id1,
                "name": "First cloud account",
                "account_id": "123456",
                "type": "azure_cnr",
            },
            datasource_id2: {
                "total": 56.78,
                "id": datasource_id2,
                "name": "Second cloud account",
                "type": "azure_cnr",
                "account_id": "654321",
            },
        },
    )

    existing_datasource_expenses = await datasource_expense_handler.query_db(unique=True)
    assert len(existing_datasource_expenses) == 1

    await fetch_datasource_expenses.main(test_settings, organization.id)

    new_datasource_expenses = await datasource_expense_handler.query_db(unique=True)
    assert len(new_datasource_expenses) == 3

    ds_exp1_total = next(
        ds_exp
        for ds_exp in new_datasource_expenses
        if ds_exp.linked_datasource_id == datasource_id1 and ds_exp.day == 20
    )
    ds_exp2_total = next(
        ds_exp
        for ds_exp in new_datasource_expenses
        if ds_exp.linked_datasource_id == datasource_id2 and ds_exp.day == 20
    )

    ds_exp1_daily = next(
        ds_exp
        for ds_exp in new_datasource_expenses
        if ds_exp.linked_datasource_id == datasource_id1 and ds_exp.day == 19
    )

    await db_session.refresh(existing_datasource_expense1)

    assert ds_exp1_total.organization_id == organization.id
    assert ds_exp1_total.year == 2025
    assert ds_exp1_total.month == 3
    assert ds_exp1_total.day == 20
    assert ds_exp1_total.total_expenses == Decimal("123.45")
    assert ds_exp1_total.datasource_name == "First cloud account"
    assert ds_exp1_total.datasource_id == "123456"

    assert ds_exp2_total.organization_id == organization.id
    assert ds_exp2_total.year == 2025
    assert ds_exp2_total.month == 3
    assert ds_exp2_total.day == 20
    assert ds_exp2_total.total_expenses == Decimal("567.89")
    assert ds_exp2_total.datasource_name == "Second cloud account"
    assert ds_exp2_total.datasource_id == "654321"

    assert ds_exp1_daily.organization_id == organization.id
    assert ds_exp1_daily.year == 2025
    assert ds_exp1_daily.month == 3
    assert ds_exp1_daily.day == 19
    assert ds_exp1_daily.expenses == Decimal("12.34")
    assert ds_exp1_daily.datasource_name == "First cloud account"
    assert ds_exp1_daily.datasource_id == "123456"


async def test_create_new_datasource_expenses_single_organization_deleted(
    mocker: MockerFixture,
    test_settings: Settings,
    db_session: AsyncSession,
    mock_optscale_client: MockOptscaleClient,
    organization_factory: ModelFactory[Organization],
    datasource_expense_factory: ModelFactory[DatasourceExpense],
):
    mocker.patch("app.commands.fetch_datasource_expenses.send_info")
    datasource_expense_handler = DatasourceExpenseHandler(db_session)
    organization = await organization_factory(
        linked_organization_id=str(uuid.uuid4()),
        status=OrganizationStatus.DELETED,
    )

    datasource_id1 = str(uuid.uuid4())

    await datasource_expense_factory(
        organization=organization,
        linked_datasource_id=datasource_id1,
        linked_datasource_type=DatasourceType.AZURE_CNR,
        datasource_name="First cloud account",
        datasource_id="123456",
        year=2025,
        month=3,
        day=19,
        total_expenses=Decimal("123.45"),
    )

    existing_datasource_expenses = await datasource_expense_handler.query_db(unique=True)
    assert len(existing_datasource_expenses) == 1

    await fetch_datasource_expenses.main(test_settings, organization.id)

    new_datasource_expenses = await datasource_expense_handler.query_db(unique=True)
    assert len(new_datasource_expenses) == 1


async def test_create_new_datasource_expenses_organization_deleted(
    mocker: MockerFixture,
    test_settings: Settings,
    db_session: AsyncSession,
    mock_optscale_client: MockOptscaleClient,
    organization_factory: ModelFactory[Organization],
    datasource_expense_factory: ModelFactory[DatasourceExpense],
):
    mocker.patch("app.commands.fetch_datasource_expenses.send_info")
    datasource_expense_handler = DatasourceExpenseHandler(db_session)
    organization = await organization_factory(
        linked_organization_id=str(uuid.uuid4()),
        status=OrganizationStatus.DELETED,
    )

    datasource_id1 = str(uuid.uuid4())

    await datasource_expense_factory(
        organization=organization,
        linked_datasource_id=datasource_id1,
        linked_datasource_type=DatasourceType.AZURE_CNR,
        datasource_name="First cloud account",
        datasource_id="123456",
        year=2025,
        month=3,
        day=19,
        total_expenses=Decimal("123.45"),
    )

    existing_datasource_expenses = await datasource_expense_handler.query_db(unique=True)
    assert len(existing_datasource_expenses) == 1

    await fetch_datasource_expenses.main(test_settings)

    new_datasource_expenses = await datasource_expense_handler.query_db(unique=True)
    assert len(new_datasource_expenses) == 1


@time_machine.travel("2025-03-20T10:00:00Z", tick=False)
async def test_datasource_expenses_are_updated_for_current_month(
    mocker: MockerFixture,
    test_settings: Settings,
    db_session: AsyncSession,
    mock_optscale_client: MockOptscaleClient,
    organization_factory: ModelFactory[Organization],
    datasource_expense_factory: ModelFactory[DatasourceExpense],
):
    mocker.patch(
        "app.commands.fetch_datasource_expenses.send_info",
    )
    datasource_expense_handler = DatasourceExpenseHandler(db_session)
    organization = await organization_factory(linked_organization_id=str(uuid.uuid4()))

    datasource_id1 = str(uuid.uuid4())
    datasource_id2 = str(uuid.uuid4())

    existing_datasource_expense1 = await datasource_expense_factory(
        organization=organization,
        linked_datasource_id=datasource_id1,
        linked_datasource_type=DatasourceType.AWS_CNR,
        datasource_name="First cloud account",
        datasource_id="11111111",
        year=2025,
        month=3,  # NOTE: This is for the current month, so it should be updated
        day=20,
        total_expenses=Decimal("123.45"),
    )

    existing_datasource_expense2 = await datasource_expense_factory(
        organization=organization,
        linked_datasource_id=datasource_id2,
        linked_datasource_type=DatasourceType.AZURE_CNR,
        datasource_name="Second cloud account",
        datasource_id="22222222",
        year=2025,
        month=2,  # NOTE: this is for the previous month, so it should NOT be updated
        day=20,
        expenses=Decimal("56.78"),
        total_expenses=Decimal("567.89"),
    )

    existing_datasource_expense3 = await datasource_expense_factory(
        organization=organization,
        linked_datasource_id=datasource_id1,
        linked_datasource_type=DatasourceType.AWS_CNR,
        datasource_name="First cloud account",
        datasource_id="11111111",
        year=2025,
        month=3,
        day=19,
        total_expenses=Decimal("123.45"),
    )

    existing_datasource_expense4 = await datasource_expense_factory(
        organization=organization,
        linked_datasource_id=datasource_id2,
        linked_datasource_type=DatasourceType.AZURE_CNR,
        datasource_name="Second cloud account",
        datasource_id="22222222",
        year=2025,
        month=3,
        day=19,
        total_expenses=Decimal("123.45"),
    )

    mock_optscale_client.mock_fetch_datasources_for_organization(
        organization,
        [
            {
                "id": datasource_id1,
                "account_id": "11111111",
                "type": "aws_cnr",
                "name": "First cloud account",
                "details": {"cost": 234.56},
            },
            {
                "id": datasource_id2,
                "account_id": "22222222",
                "type": "azure_cnr",
                "name": "Second cloud account",
                "details": {"cost": 678.90},
            },
        ],
    )

    mock_optscale_client.mock_fetch_daily_expenses_for_organization(
        organization,
        int(datetime(2025, 3, 19, 0, 0, 0, tzinfo=UTC).timestamp()),
        int(datetime(2025, 3, 19, 23, 59, 59, tzinfo=UTC).timestamp()),
        {
            datasource_id1: {
                "total": 12.34,
                "id": datasource_id1,
                "name": "First cloud account",
                "account_id": "11111111",
                "type": "aws_cnr",
            },
            datasource_id2: {
                "total": 56.78,
                "id": datasource_id2,
                "name": "Second cloud account",
                "type": "azure_cnr",
                "account_id": "22222222",
            },
        },
    )

    existing_datasource_expenses = await datasource_expense_handler.query_db(unique=True)
    assert len(existing_datasource_expenses) == 4

    await fetch_datasource_expenses.main(test_settings)

    new_datasource_expenses = await datasource_expense_handler.query_db(unique=True)
    assert len(new_datasource_expenses) == 5

    ds_exp1 = next(
        ds_exp
        for ds_exp in new_datasource_expenses
        if ds_exp.linked_datasource_id == datasource_id1 and ds_exp.day == 20
    )
    ds_exp2_current_month = next(
        ds_exp
        for ds_exp in new_datasource_expenses
        if (ds_exp.linked_datasource_id == datasource_id2 and ds_exp.month == 2)
    )

    ds_exp2_this_month = next(
        ds_exp
        for ds_exp in new_datasource_expenses
        if (
            ds_exp.linked_datasource_id == datasource_id2 and ds_exp.month == 3 and ds_exp.day == 20
        )
    )

    ds_exp3_this_month = next(
        ds_exp
        for ds_exp in new_datasource_expenses
        if ds_exp.linked_datasource_id == datasource_id1 and ds_exp.day == 19
    )

    ds_exp4_this_month = next(
        ds_exp
        for ds_exp in new_datasource_expenses
        if ds_exp.linked_datasource_id == datasource_id2 and ds_exp.day == 19
    )

    await db_session.refresh(existing_datasource_expense1)
    await db_session.refresh(existing_datasource_expense3)
    await db_session.refresh(existing_datasource_expense4)

    assert ds_exp1.id == existing_datasource_expense1.id
    assert ds_exp1.datasource_name == "First cloud account"
    assert ds_exp1.organization_id == organization.id
    assert ds_exp1.year == 2025
    assert ds_exp1.month == 3
    assert ds_exp1.day == 20
    assert ds_exp1.total_expenses == Decimal("234.56")
    assert ds_exp1.expenses == Decimal("0.0000")

    assert ds_exp2_current_month.id == existing_datasource_expense2.id
    assert ds_exp2_current_month.datasource_name == "Second cloud account"
    assert ds_exp2_current_month.organization_id == organization.id
    assert ds_exp2_current_month.year == 2025
    assert ds_exp2_current_month.month == 2
    assert ds_exp2_current_month.day == 20
    assert ds_exp2_current_month.total_expenses == Decimal("567.89")
    assert ds_exp2_current_month.expenses == Decimal("56.78")

    assert ds_exp2_this_month.id not in (
        existing_datasource_expense1.id,
        existing_datasource_expense2.id,
    )
    assert ds_exp2_this_month.datasource_name == "Second cloud account"
    assert ds_exp2_this_month.organization_id == organization.id
    assert ds_exp2_this_month.year == 2025
    assert ds_exp2_this_month.month == 3
    assert ds_exp2_this_month.day == 20
    assert ds_exp2_this_month.total_expenses == Decimal("678.90")
    assert ds_exp2_this_month.expenses == Decimal("0.0000")

    assert ds_exp3_this_month.id == existing_datasource_expense3.id
    assert ds_exp3_this_month.month == 3
    assert ds_exp3_this_month.day == 19
    assert ds_exp3_this_month.total_expenses == Decimal("123.45")
    assert ds_exp3_this_month.expenses == Decimal("12.34")

    assert ds_exp4_this_month.datasource_name == "Second cloud account"
    assert ds_exp4_this_month.month == 3
    assert ds_exp4_this_month.day == 19
    assert ds_exp4_this_month.total_expenses == Decimal("123.45")
    assert ds_exp4_this_month.expenses == Decimal("56.78")


@time_machine.travel("2025-03-20T10:00:00Z", tick=False)
async def test_organization_with_no_linked_organization_id(
    mocker: MockerFixture,
    test_settings: Settings,
    db_session: AsyncSession,
    organization_factory: ModelFactory[Organization],
    caplog: pytest.LogCaptureFixture,
    httpx_mock: HTTPXMock,
):
    mocker.patch(
        "app.commands.fetch_datasource_expenses.send_info",
    )
    datasource_expense_handler = DatasourceExpenseHandler(db_session)
    organization = await organization_factory(linked_organization_id=None)

    with caplog.at_level(logging.WARNING):
        await fetch_datasource_expenses.main(test_settings)

    assert (
        f"Organization {organization.id} - {organization.name} has no "
        "linked organization ID. Skipping..."
    ) in caplog.text

    new_datasource_expenses = await datasource_expense_handler.query_db(unique=True)
    assert len(new_datasource_expenses) == 0

    assert not httpx_mock.get_request()


@time_machine.travel("2025-03-20T10:00:00Z", tick=False)
async def test_organization_with_recent_updates_to_datasource_expenses(
    test_settings: Settings,
    db_session: AsyncSession,
    organization_factory: ModelFactory[Organization],
    datasource_expense_factory: ModelFactory[DatasourceExpense],
    httpx_mock: HTTPXMock,
    mocker: MockerFixture,
):
    organization = await organization_factory(linked_organization_id=None)

    store_datasource_expenses_mock = mocker.patch(
        "app.commands.fetch_datasource_expenses.store_datasource_expenses"
    )

    await datasource_expense_factory(
        organization=organization,
        year=2025,
        month=3,
        day=20,
        expenses=Decimal("123.45"),
        updated_at=datetime.now(UTC),
    )

    await fetch_datasource_expenses.main(test_settings)
    assert not httpx_mock.get_request()
    assert store_datasource_expenses_mock.call_count == 2
    # store_datasource_expenses_mock expenses_per_organization argument
    assert store_datasource_expenses_mock.call_args_list[0][0][1] == {}
    assert store_datasource_expenses_mock.call_args_list[1][0][1] == {}


@pytest.mark.parametrize(
    ("status_code", "expected_log_level", "expected_log_format"),
    [
        (
            status.HTTP_404_NOT_FOUND,
            logging.WARNING,
            [
                "Organization %s not found on Optscale.",
                (
                    "Organization %s not found or organization doesn't have "
                    "any cloud accounts connected in Optscale."
                ),
            ],
        ),
        (
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            logging.ERROR,
            [
                "Unexpected error occurred fetching datasources for organization %s",
                "Unexpected error occurred fetching daily expenses for organization %s",
            ],
        ),
    ],
)
@time_machine.travel("2025-03-20T10:00:00Z", tick=False)
async def test_optscale_api_returns_exception(
    mocker: MockerFixture,
    caplog: pytest.LogCaptureFixture,
    test_settings: Settings,
    db_session: AsyncSession,
    organization_factory: ModelFactory[Organization],
    mock_optscale_client: MockOptscaleClient,
    status_code: int,
    expected_log_level: int,
    expected_log_format: list[str],
):
    datasource_expense_handler = DatasourceExpenseHandler(db_session)
    organization = await organization_factory(linked_organization_id=str(uuid.uuid4()))

    mock_optscale_client.mock_fetch_datasources_for_organization(
        organization, status_code=status_code
    )
    mock_optscale_client.mock_fetch_daily_expenses_for_organization(
        organization,
        int(datetime(2025, 3, 19, 0, 0, 0, tzinfo=UTC).timestamp()),
        int(datetime(2025, 3, 19, 23, 59, 59, tzinfo=UTC).timestamp()),
        {},
        status_code=status_code,
    )

    mocker.patch(
        "app.commands.fetch_datasource_expenses.send_exception",
    )
    mocker.patch(
        "app.commands.fetch_datasource_expenses.send_info",
    )
    with caplog.at_level(logging.WARNING):
        await fetch_datasource_expenses.main(test_settings)

    for expected_log in expected_log_format:
        assert (
            fetch_datasource_expenses.logger.name,
            expected_log_level,
            expected_log % organization.id,
        ) in caplog.record_tuples

    new_datasource_expenses = await datasource_expense_handler.query_db(unique=True)
    assert len(new_datasource_expenses) == 0


@time_machine.travel("2025-03-20T10:00:00Z", tick=False)
async def test_multiple_datasources_are_handled_correctly(
    mocker: MockerFixture,
    caplog: pytest.LogCaptureFixture,
    test_settings: Settings,
    db_session: AsyncSession,
    mock_optscale_client: MockOptscaleClient,
    organization_factory: ModelFactory[Organization],
    datasource_expense_factory: ModelFactory[DatasourceExpense],
):
    mocker.patch(
        "app.commands.fetch_datasource_expenses.send_exception",
    )
    mocker.patch(
        "app.commands.fetch_datasource_expenses.send_info",
    )
    datasource_expense_handler = DatasourceExpenseHandler(db_session)
    organization1 = await organization_factory(
        linked_organization_id=str(uuid.uuid4()), operations_external_id="org_1_external_id"
    )
    organization2 = await organization_factory(
        linked_organization_id=str(uuid.uuid4()), operations_external_id="org_2_external_id"
    )
    organization3 = await organization_factory(
        linked_organization_id=str(uuid.uuid4()), operations_external_id="org_3_external_id"
    )
    organization4 = await organization_factory(
        linked_organization_id=str(uuid.uuid4()), operations_external_id="org_4_external_id"
    )

    org1_datasource_id1 = str(uuid.uuid4())
    org1_datasource_id2 = str(uuid.uuid4())
    org1_datasource_id3 = str(uuid.uuid4())
    org1_datasource_id4 = str(uuid.uuid4())

    org2_datasource_id1 = str(uuid.uuid4())
    org2_datasource_id2 = str(uuid.uuid4())

    org3_datasource_id1 = str(uuid.uuid4())

    await datasource_expense_factory(
        organization=organization1,
        linked_datasource_id=org1_datasource_id1,
        linked_datasource_type=DatasourceType.AWS_CNR,
        datasource_id="11111111",
        year=2025,
        month=2,
        day=20,
        total_expenses=Decimal("123.45"),
    )

    await datasource_expense_factory(
        organization=organization1,
        linked_datasource_id=org1_datasource_id1,
        linked_datasource_type=DatasourceType.AWS_CNR,
        datasource_id="11111111",
        year=2025,
        month=3,
        day=20,
        total_expenses=Decimal("234.56"),
    )

    await datasource_expense_factory(
        organization=organization1,
        linked_datasource_id=org1_datasource_id2,
        datasource_id="12222222",
        linked_datasource_type=DatasourceType.AWS_CNR,
        year=2025,
        month=3,
        day=20,
        total_expenses=Decimal("567.89"),
    )

    await datasource_expense_factory(
        organization=organization2,
        linked_datasource_id=org2_datasource_id1,
        datasource_id="21111111",
        linked_datasource_type=DatasourceType.AWS_CNR,
        year=2025,
        month=3,
        day=20,
        total_expenses=Decimal("999.88"),
        expenses=Decimal("56.78"),
    )

    existing_datasource_expense1 = await datasource_expense_factory(
        organization=organization1,
        linked_datasource_id=org1_datasource_id1,
        linked_datasource_type=DatasourceType.AWS_CNR,
        datasource_id="11111111",
        year=2025,
        month=3,
        day=19,
        total_expenses=Decimal("123.45"),
    )

    existing_datasource_expense2 = await datasource_expense_factory(
        organization=organization2,
        linked_datasource_id=org2_datasource_id1,
        linked_datasource_type=DatasourceType.AWS_CNR,
        datasource_id="21111111",
        year=2025,
        month=3,
        day=19,
        total_expenses=Decimal("123.45"),
    )

    existing_datasource_expense3 = await datasource_expense_factory(
        organization=organization3,
        linked_datasource_id=org3_datasource_id1,
        linked_datasource_type=DatasourceType.AWS_CNR,
        datasource_id="31111111",
        year=2025,
        month=3,
        day=19,
        total_expenses=Decimal("123.45"),
    )

    existing_datasource_expenses = await datasource_expense_handler.query_db(unique=True)
    assert len(existing_datasource_expenses) == 7

    mock_optscale_client.mock_fetch_datasources_for_organization(
        organization1,
        [
            {
                "id": org1_datasource_id1,
                "account_id": "11111111",
                "type": "aws_cnr",
                "details": {"cost": 789.01},
            },
            {
                "id": org1_datasource_id2,
                "account_id": "12222222",
                "type": "aws_cnr",
                "details": {"cost": 678.90},
            },
            {"id": org1_datasource_id3, "account_id": "13333333", "type": "azure_tenant"},
            {"id": org1_datasource_id4, "account_id": "14444444", "type": "gcp_tenant"},
        ],
    )

    mock_optscale_client.mock_fetch_daily_expenses_for_organization(
        organization1,
        int(datetime(2025, 3, 19, 0, 0, 0, tzinfo=UTC).timestamp()),
        int(datetime(2025, 3, 19, 23, 59, 59, tzinfo=UTC).timestamp()),
        {
            org1_datasource_id1: {
                "total": 12.34,
                "id": org1_datasource_id1,
                "name": "First cloud account",
                "account_id": "11111111",
                "type": "aws_cnr",
            },
        },
    )

    mock_optscale_client.mock_fetch_datasources_for_organization(
        organization2,
        [
            {
                "id": org2_datasource_id1,
                "account_id": "21111111",
                "type": "aws_cnr",
                "details": {"cost": 234.56},
            },
            {
                "id": org2_datasource_id2,
                "account_id": "22222222",
                "type": "aws_cnr",
                "details": {"cost": 654.32},
            },
        ],
    )

    mock_optscale_client.mock_fetch_daily_expenses_for_organization(
        organization2,
        int(datetime(2025, 3, 19, 0, 0, 0, tzinfo=UTC).timestamp()),
        int(datetime(2025, 3, 19, 23, 59, 59, tzinfo=UTC).timestamp()),
        {
            org2_datasource_id1: {
                "total": 12.34,
                "id": org2_datasource_id1,
                "name": "First cloud account",
                "account_id": "21111111",
                "type": "aws_cnr",
            },
        },
    )

    mock_optscale_client.mock_fetch_datasources_for_organization(
        organization3,
        [
            {
                "id": org3_datasource_id1,
                "account_id": "31111111",
                "type": "azure_cnr",
                "details": {"cost": 777.88},
            }
        ],
    )

    mock_optscale_client.mock_fetch_daily_expenses_for_organization(
        organization3,
        int(datetime(2025, 3, 19, 0, 0, 0, tzinfo=UTC).timestamp()),
        int(datetime(2025, 3, 19, 23, 59, 59, tzinfo=UTC).timestamp()),
        {
            org3_datasource_id1: {
                "total": 12.34,
                "id": org3_datasource_id1,
                "name": "First cloud account",
                "account_id": "31111111",
                "type": "aws_cnr",
            },
        },
    )

    mock_optscale_client.mock_fetch_datasources_for_organization(organization4, status_code=404)
    mock_optscale_client.mock_fetch_daily_expenses_for_organization(
        organization4,
        int(datetime(2025, 3, 19, 0, 0, 0, tzinfo=UTC).timestamp()),
        int(datetime(2025, 3, 19, 23, 59, 59, tzinfo=UTC).timestamp()),
        {},
        status_code=424,
    )

    with caplog.at_level(logging.WARNING):
        await fetch_datasource_expenses.main(test_settings)
        assert (
            f"Skipping child datasource {org1_datasource_id3} of type azure_tenant" in caplog.text
        )
        assert f"Skipping child datasource {org1_datasource_id4} of type gcp_tenant" in caplog.text
        assert (
            f"Organization {organization4.id} not found or "
            "organization doesn't have any cloud accounts connected in Optscale."
        ) in caplog.text

    new_datasource_expenses = await datasource_expense_handler.query_db(unique=True)

    await db_session.refresh(existing_datasource_expense1)
    await db_session.refresh(existing_datasource_expense2)
    await db_session.refresh(existing_datasource_expense3)

    expenses_data = {
        (
            ds_exp.organization_id,
            ds_exp.linked_datasource_id,
            ds_exp.datasource_id,
            ds_exp.year,
            ds_exp.month,
            ds_exp.day,
            ds_exp.total_expenses,
            ds_exp.expenses,
        )
        for ds_exp in new_datasource_expenses
    }

    assert expenses_data == {
        (
            organization1.id,
            org1_datasource_id1,
            "11111111",
            2025,
            2,
            20,
            Decimal("123.4500"),
            Decimal("0.0000"),
        ),
        (
            organization1.id,
            org1_datasource_id1,
            "11111111",
            2025,
            3,
            20,
            Decimal("234.5600"),
            Decimal("0.0000"),
        ),
        (
            organization1.id,
            org1_datasource_id2,
            "12222222",
            2025,
            3,
            20,
            Decimal("567.8900"),
            Decimal("0.0000"),
        ),
        (
            organization2.id,
            org2_datasource_id1,
            "21111111",
            2025,
            3,
            20,
            Decimal("999.8800"),
            Decimal("56.7800"),
        ),
        (
            organization2.id,
            org2_datasource_id2,
            "22222222",
            2025,
            3,
            20,
            Decimal("654.3200"),
            Decimal("0.0000"),
        ),
        (
            organization3.id,
            org3_datasource_id1,
            "31111111",
            2025,
            3,
            20,
            Decimal("777.8800"),
            Decimal("0.0000"),
        ),
        (
            organization1.id,
            org1_datasource_id1,
            "11111111",
            2025,
            3,
            19,
            Decimal("123.4500"),
            Decimal("12.3400"),
        ),
        (
            organization2.id,
            org2_datasource_id1,
            "21111111",
            2025,
            3,
            19,
            Decimal("123.4500"),
            Decimal("12.3400"),
        ),
        (
            organization3.id,
            org3_datasource_id1,
            "31111111",
            2025,
            3,
            19,
            Decimal("123.4500"),
            Decimal("12.3400"),
        ),
    }


def test_cli_command(mocker: MockerFixture):
    mock_command_coro = mocker.MagicMock()
    mock_command = mocker.MagicMock(return_value=mock_command_coro)

    mocker.patch("app.commands.fetch_datasource_expenses.main", mock_command)
    mock_run = mocker.patch("app.commands.fetch_datasource_expenses.asyncio.run")
    runner = CliRunner()

    result = runner.invoke(app, ["fetch-datasource-expenses"])
    assert result.exit_code == 0
    mock_run.assert_called_once_with(mock_command_coro)
