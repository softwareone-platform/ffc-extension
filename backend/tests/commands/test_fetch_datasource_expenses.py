import asyncio
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
from app.conf import Settings, get_settings
from app.db.base import session_factory
from app.db.handlers import DatasourceExpenseHandler, OrganizationHandler
from app.db.models import DatasourceExpense, Organization
from app.enums import DatasourceType, OrganizationStatus


@time_machine.travel("2025-03-20T10:00:00Z", tick=False)
@pytest.mark.parametrize(
    "organization_status",
    [
        OrganizationStatus.ACTIVE,
        OrganizationStatus.TERMINATED,
    ],
)
async def test_create_new_datasource_expenses_single_organization(
    test_settings: Settings,
    db_session: AsyncSession,
    httpx_mock: HTTPXMock,
    organization_status: OrganizationStatus,
) -> None:
    """Monthly datasources are stored and yesterday's expenses update the existing daily row.

    Optscale and the MSTeams webhook are stubbed at the HTTP level with ``httpx_mock``, so the
    real ``OptscaleClient`` (URL building, cluster secret auth, response parsing), the real
    notification code and the real DB handlers run. Every non-deleted status is processed.
    """
    webhook_url = get_settings().msteams_notifications_webhook_url
    httpx_mock.add_response(
        method="POST",
        url=webhook_url,
        status_code=status.HTTP_202_ACCEPTED,
    )

    linked_organization_id = str(uuid.uuid4())
    organization = await OrganizationHandler(db_session).create(
        Organization(
            name="ACME Inc",
            currency="USD",
            billing_currency="USD",
            operations_external_id="AGR-1234-5678-9012",
            linked_organization_id=linked_organization_id,
            status=organization_status,
        )
    )

    datasource_id1 = str(uuid.uuid4())
    datasource_id2 = str(uuid.uuid4())

    existing_datasource_expense1 = await DatasourceExpenseHandler(db_session).create(
        DatasourceExpense(
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
    )

    organization_url = (
        f"{test_settings.optscale_rest_api_base_url}/organizations/{linked_organization_id}"
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{organization_url}/cloud_accounts",
        match_params={"details": "true"},
        match_headers={"Secret": test_settings.optscale_cluster_secret},
        json={
            "cloud_accounts": [
                {
                    "id": datasource_id1,
                    "name": "First cloud account",
                    "type": DatasourceType.AZURE_CNR.value,
                    "account_id": "123456",
                    "details": {"cost": 123.45},
                },
                {
                    "id": datasource_id2,
                    "name": "Second cloud account",
                    "type": DatasourceType.AZURE_CNR.value,
                    "account_id": "654321",
                    "details": {"cost": 567.89},
                },
            ]
        },
    )

    day_start = int(datetime(2025, 3, 19, 0, 0, 0, tzinfo=UTC).timestamp())
    day_end = int(datetime(2025, 3, 19, 23, 59, 59, tzinfo=UTC).timestamp())
    httpx_mock.add_response(
        method="GET",
        url=f"{organization_url}/breakdown_expenses",
        match_params={
            "start_date": str(day_start),
            "end_date": str(day_end),
            "breakdown_by": "cloud_account_id",
        },
        match_headers={"Secret": test_settings.optscale_cluster_secret},
        json={
            "counts": {
                datasource_id1: {
                    "total": 12.34,
                    "id": datasource_id1,
                    "name": "First cloud account",
                    "type": DatasourceType.AZURE_CNR.value,
                    "account_id": "123456",
                },
                datasource_id2: {
                    "total": 56.78,
                    "id": datasource_id2,
                    "name": "Second cloud account",
                    "type": DatasourceType.AZURE_CNR.value,
                    "account_id": "654321",
                },
            },
            "start_date": day_start,
            "end_date": day_end,
            "breakdown_by": "cloud_account_id",
        },
    )

    existing_datasource_expenses = await DatasourceExpenseHandler(db_session).query_db(unique=True)
    assert len(existing_datasource_expenses) == 1

    await fetch_datasource_expenses.main(test_settings, organization.id)

    new_datasource_expenses = await DatasourceExpenseHandler(db_session).query_db(unique=True)
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

    # the daily figure updates the pre-existing row for yesterday instead of creating a new one
    assert ds_exp1_daily.id == existing_datasource_expense1.id
    assert ds_exp1_daily.organization_id == organization.id
    assert ds_exp1_daily.year == 2025
    assert ds_exp1_daily.month == 3
    assert ds_exp1_daily.day == 19
    assert ds_exp1_daily.expenses == Decimal("12.34")
    assert ds_exp1_daily.total_expenses == Decimal("123.45")
    assert ds_exp1_daily.datasource_name == "First cloud account"
    assert ds_exp1_daily.datasource_id == "123456"

    notifications = httpx_mock.get_requests(method="POST", url=webhook_url)
    assert len(notifications) == 1
    assert "Datasource expenses updated for 1 organizations" in notifications[0].content.decode()


@time_machine.travel("2025-03-20T10:00:00Z", tick=False)
async def test_create_new_datasource_expenses_single_organization_deleted(
    test_settings: Settings,
    db_session: AsyncSession,
    httpx_mock: HTTPXMock,
) -> None:
    """A deleted organization is skipped: Optscale
    is never called and its expenses are untouched."""
    webhook_url = get_settings().msteams_notifications_webhook_url
    httpx_mock.add_response(
        method="POST",
        url=webhook_url,
        status_code=status.HTTP_202_ACCEPTED,
    )

    organization = await OrganizationHandler(db_session).create(
        Organization(
            name="ACME Inc",
            currency="USD",
            billing_currency="USD",
            operations_external_id="AGR-1234-5678-9012",
            linked_organization_id=str(uuid.uuid4()),
            status=OrganizationStatus.DELETED,
        )
    )

    existing_datasource_expense = await DatasourceExpenseHandler(db_session).create(
        DatasourceExpense(
            organization=organization,
            linked_datasource_id=str(uuid.uuid4()),
            linked_datasource_type=DatasourceType.AZURE_CNR,
            datasource_name="First cloud account",
            datasource_id="123456",
            year=2025,
            month=3,
            day=19,
            total_expenses=Decimal("123.45"),
        )
    )

    existing_datasource_expenses = await DatasourceExpenseHandler(db_session).query_db(unique=True)
    assert len(existing_datasource_expenses) == 1

    await fetch_datasource_expenses.main(test_settings, organization.id)

    new_datasource_expenses = await DatasourceExpenseHandler(db_session).query_db(unique=True)
    assert len(new_datasource_expenses) == 1

    await db_session.refresh(existing_datasource_expense)
    assert new_datasource_expenses[0].id == existing_datasource_expense.id
    assert existing_datasource_expense.total_expenses == Decimal("123.45")
    assert existing_datasource_expense.expenses == Decimal("0.0000")

    # the notification is the only request made: Optscale was never contacted
    assert not [
        request
        for request in httpx_mock.get_requests()
        if str(request.url).startswith(test_settings.optscale_rest_api_base_url)
    ]
    notification = httpx_mock.get_request(method="POST", url=webhook_url)
    assert notification is not None
    assert "Datasource expenses updated for 0 organizations" in notification.content.decode()


@time_machine.travel("2025-03-20T10:00:00Z", tick=False)
async def test_create_new_datasource_expenses_organization_deleted(
    test_settings: Settings,
    db_session: AsyncSession,
    httpx_mock: HTTPXMock,
) -> None:
    """The all-organizations run skips deleted organizations and leaves their expenses intact.

    ``main`` is called without an organization ID, so the deleted organization is excluded by
    the query itself.
    """
    webhook_url = get_settings().msteams_notifications_webhook_url
    httpx_mock.add_response(
        method="POST",
        url=webhook_url,
        status_code=status.HTTP_202_ACCEPTED,
    )

    organization = await OrganizationHandler(db_session).create(
        Organization(
            name="ACME Inc",
            currency="USD",
            billing_currency="USD",
            operations_external_id="AGR-1234-5678-9012",
            linked_organization_id=str(uuid.uuid4()),
            status=OrganizationStatus.DELETED,
        )
    )

    existing_datasource_expense = await DatasourceExpenseHandler(db_session).create(
        DatasourceExpense(
            organization=organization,
            linked_datasource_id=str(uuid.uuid4()),
            linked_datasource_type=DatasourceType.AZURE_CNR,
            datasource_name="First cloud account",
            datasource_id="123456",
            year=2025,
            month=3,
            day=19,
            total_expenses=Decimal("123.45"),
        )
    )

    existing_datasource_expenses = await DatasourceExpenseHandler(db_session).query_db(unique=True)
    assert len(existing_datasource_expenses) == 1

    await fetch_datasource_expenses.main(test_settings)

    new_datasource_expenses = await DatasourceExpenseHandler(db_session).query_db(unique=True)
    assert len(new_datasource_expenses) == 1

    await db_session.refresh(existing_datasource_expense)
    assert new_datasource_expenses[0].id == existing_datasource_expense.id
    assert existing_datasource_expense.total_expenses == Decimal("123.45")
    assert existing_datasource_expense.expenses == Decimal("0.0000")

    # the notification is the only request made: Optscale was never contacted
    assert not [
        request
        for request in httpx_mock.get_requests()
        if str(request.url).startswith(test_settings.optscale_rest_api_base_url)
    ]
    notification = httpx_mock.get_request(method="POST", url=webhook_url)
    assert notification is not None
    assert "Datasource expenses updated for 0 organizations" in notification.content.decode()


@time_machine.travel("2025-03-20T10:00:00Z", tick=False)
async def test_datasource_expenses_are_updated_for_current_month(
    test_settings: Settings,
    db_session: AsyncSession,
    httpx_mock: HTTPXMock,
) -> None:
    """Only rows for the current month are updated; previous months are left untouched.

    Four rows exist up front: the monthly total for today, a total for the *previous* month,
    and yesterday's daily rows for both datasources. The run must update today's total for
    the first datasource, create the missing total for the second, fill in yesterday's daily
    expenses, and leave the February row exactly as it was.
    """
    webhook_url = get_settings().msteams_notifications_webhook_url
    httpx_mock.add_response(
        method="POST",
        url=webhook_url,
        status_code=status.HTTP_202_ACCEPTED,
    )
    linked_organization_id = str(uuid.uuid4())
    organization = await OrganizationHandler(db_session).create(
        Organization(
            name="ACME Inc",
            currency="USD",
            billing_currency="USD",
            operations_external_id="AGR-1234-5678-9012",
            linked_organization_id=linked_organization_id,
            status=OrganizationStatus.ACTIVE,
        )
    )

    datasource_id1 = str(uuid.uuid4())
    datasource_id2 = str(uuid.uuid4())
    existing_datasource_expense1 = await DatasourceExpenseHandler(db_session).create(
        DatasourceExpense(
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
    )

    existing_datasource_expense2 = await DatasourceExpenseHandler(db_session).create(
        DatasourceExpense(
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
    )

    existing_datasource_expense3 = await DatasourceExpenseHandler(db_session).create(
        DatasourceExpense(
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
    )

    existing_datasource_expense4 = await DatasourceExpenseHandler(db_session).create(
        DatasourceExpense(
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
    )

    organization_url = (
        f"{test_settings.optscale_rest_api_base_url}/organizations/{linked_organization_id}"
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{organization_url}/cloud_accounts",
        match_params={"details": "true"},
        match_headers={"Secret": test_settings.optscale_cluster_secret},
        json={
            "cloud_accounts": [
                {
                    "id": datasource_id1,
                    "account_id": "11111111",
                    "type": DatasourceType.AWS_CNR.value,
                    "name": "First cloud account",
                    "details": {"cost": 234.56},
                },
                {
                    "id": datasource_id2,
                    "account_id": "22222222",
                    "type": DatasourceType.AZURE_CNR.value,
                    "name": "Second cloud account",
                    "details": {"cost": 678.90},
                },
            ]
        },
    )

    day_start = int(datetime(2025, 3, 19, 0, 0, 0, tzinfo=UTC).timestamp())
    day_end = int(datetime(2025, 3, 19, 23, 59, 59, tzinfo=UTC).timestamp())
    httpx_mock.add_response(
        method="GET",
        url=f"{organization_url}/breakdown_expenses",
        match_params={
            "start_date": str(day_start),
            "end_date": str(day_end),
            "breakdown_by": "cloud_account_id",
        },
        match_headers={"Secret": test_settings.optscale_cluster_secret},
        json={
            "counts": {
                datasource_id1: {
                    "total": 12.34,
                    "id": datasource_id1,
                    "account_id": "11111111",
                    "type": DatasourceType.AWS_CNR.value,
                    "name": "First cloud account",
                },
                datasource_id2: {
                    "total": 56.78,
                    "id": datasource_id2,
                    "account_id": "22222222",
                    "type": DatasourceType.AZURE_CNR.value,
                    "name": "Second cloud account",
                },
            },
            "start_date": day_start,
            "end_date": day_end,
            "breakdown_by": "cloud_account_id",
        },
    )

    existing_datasource_expenses = await DatasourceExpenseHandler(db_session).query_db(unique=True)
    assert len(existing_datasource_expenses) == 4

    await fetch_datasource_expenses.main(test_settings)

    new_datasource_expenses = await DatasourceExpenseHandler(db_session).query_db(unique=True)
    assert len(new_datasource_expenses) == 5

    ds_exp1_total = next(
        ds_exp
        for ds_exp in new_datasource_expenses
        if ds_exp.linked_datasource_id == datasource_id1 and ds_exp.month == 3 and ds_exp.day == 20
    )
    ds_exp2_previous_month = next(
        ds_exp
        for ds_exp in new_datasource_expenses
        if ds_exp.linked_datasource_id == datasource_id2 and ds_exp.month == 2
    )
    ds_exp2_total = next(
        ds_exp
        for ds_exp in new_datasource_expenses
        if ds_exp.linked_datasource_id == datasource_id2 and ds_exp.month == 3 and ds_exp.day == 20
    )
    ds_exp1_daily = next(
        ds_exp
        for ds_exp in new_datasource_expenses
        if ds_exp.linked_datasource_id == datasource_id1 and ds_exp.day == 19
    )
    ds_exp2_daily = next(
        ds_exp
        for ds_exp in new_datasource_expenses
        if ds_exp.linked_datasource_id == datasource_id2 and ds_exp.month == 3 and ds_exp.day == 19
    )

    await db_session.refresh(existing_datasource_expense1)
    await db_session.refresh(existing_datasource_expense2)
    await db_session.refresh(existing_datasource_expense3)
    await db_session.refresh(existing_datasource_expense4)

    # the pre-existing total for the current month is updated in place
    assert ds_exp1_total.id == existing_datasource_expense1.id
    assert ds_exp1_total.datasource_name == "First cloud account"
    assert ds_exp1_total.organization_id == organization.id
    assert ds_exp1_total.year == 2025
    assert ds_exp1_total.month == 3
    assert ds_exp1_total.day == 20
    assert ds_exp1_total.total_expenses == Decimal("234.56")
    assert ds_exp1_total.expenses == Decimal("0.0000")

    # the previous month is left untouched
    assert ds_exp2_previous_month.id == existing_datasource_expense2.id
    assert ds_exp2_previous_month.datasource_name == "Second cloud account"
    assert ds_exp2_previous_month.organization_id == organization.id
    assert ds_exp2_previous_month.year == 2025
    assert ds_exp2_previous_month.month == 2
    assert ds_exp2_previous_month.day == 20
    assert ds_exp2_previous_month.total_expenses == Decimal("567.89")
    assert ds_exp2_previous_month.expenses == Decimal("56.78")

    # the missing total for the current month is created
    assert ds_exp2_total.id not in {
        existing_datasource_expense1.id,
        existing_datasource_expense2.id,
        existing_datasource_expense3.id,
        existing_datasource_expense4.id,
    }
    assert ds_exp2_total.datasource_name == "Second cloud account"
    assert ds_exp2_total.organization_id == organization.id
    assert ds_exp2_total.year == 2025
    assert ds_exp2_total.month == 3
    assert ds_exp2_total.day == 20
    assert ds_exp2_total.total_expenses == Decimal("678.90")
    assert ds_exp2_total.expenses == Decimal("0.0000")

    # yesterday's daily figures update the pre-existing rows
    assert ds_exp1_daily.id == existing_datasource_expense3.id
    assert ds_exp1_daily.month == 3
    assert ds_exp1_daily.day == 19
    assert ds_exp1_daily.total_expenses == Decimal("123.45")
    assert ds_exp1_daily.expenses == Decimal("12.34")

    assert ds_exp2_daily.id == existing_datasource_expense4.id
    assert ds_exp2_daily.datasource_name == "Second cloud account"
    assert ds_exp2_daily.month == 3
    assert ds_exp2_daily.day == 19
    assert ds_exp2_daily.total_expenses == Decimal("123.45")
    assert ds_exp2_daily.expenses == Decimal("56.78")

    notifications = httpx_mock.get_requests(method="POST", url=webhook_url)
    assert len(notifications) == 1
    assert "Datasource expenses updated for 1 organizations" in notifications[0].content.decode()


@time_machine.travel("2025-03-20T10:00:00Z", tick=False)
async def test_organization_with_no_linked_organization_id(
    test_settings: Settings,
    db_session: AsyncSession,
    caplog: pytest.LogCaptureFixture,
    httpx_mock: HTTPXMock,
) -> None:
    """An organization without a linked Optscale organization is logged and skipped."""
    webhook_url = get_settings().msteams_notifications_webhook_url
    httpx_mock.add_response(
        method="POST",
        url=webhook_url,
        status_code=status.HTTP_202_ACCEPTED,
    )

    organization = await OrganizationHandler(db_session).create(
        Organization(
            name="ACME Inc",
            currency="USD",
            billing_currency="USD",
            operations_external_id="AGR-1234-5678-9012",
            linked_organization_id=None,
            status=OrganizationStatus.ACTIVE,
        )
    )

    with caplog.at_level(logging.WARNING):
        await fetch_datasource_expenses.main(test_settings)

    assert "1 organizations without linked organization ID" in caplog.text
    assert organization.id in caplog.text

    new_datasource_expenses = await DatasourceExpenseHandler(db_session).query_db(unique=True)
    assert len(new_datasource_expenses) == 0

    assert not [
        request
        for request in httpx_mock.get_requests()
        if str(request.url).startswith(test_settings.optscale_rest_api_base_url)
    ]
    notification = httpx_mock.get_request(method="POST", url=webhook_url)
    assert notification is not None
    assert "Datasource expenses updated for 0 organizations" in notification.content.decode()


@pytest.mark.parametrize(
    ("status_code", "expected_log_level", "expected_log_format", "expected_error_notifications"),
    [
        pytest.param(
            status.HTTP_404_NOT_FOUND,
            logging.WARNING,
            [
                "Organization %s not found on Optscale.",
                (
                    "Organization %s not found or organization doesn't have "
                    "any cloud accounts connected in Optscale."
                ),
            ],
            0,
            id="404-not-found",
        ),
        pytest.param(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            logging.ERROR,
            [
                "Unexpected error occurred fetching datasources for organization %s",
                "Unexpected error occurred fetching daily expenses for organization %s",
            ],
            2,
            id="500-server-error",
        ),
    ],
)
@pytest.mark.httpx_mock(can_send_already_matched_responses=True)
@time_machine.travel("2025-03-20T10:00:00Z", tick=False)
async def test_optscale_api_returns_exception(
    caplog: pytest.LogCaptureFixture,
    test_settings: Settings,
    db_session: AsyncSession,
    httpx_mock: HTTPXMock,
    status_code: int,
    expected_log_level: int,
    expected_log_format: list[str],
    expected_error_notifications: int,
) -> None:
    """Optscale failures are logged and store nothing; only a 500 notifies an exception."""
    webhook_url = get_settings().msteams_notifications_webhook_url
    httpx_mock.add_response(
        method="POST",
        url=webhook_url,
        status_code=status.HTTP_202_ACCEPTED,
    )

    linked_organization_id = str(uuid.uuid4())
    organization = await OrganizationHandler(db_session).create(
        Organization(
            name="ACME Inc",
            currency="USD",
            billing_currency="USD",
            operations_external_id="AGR-1234-5678-9012",
            linked_organization_id=linked_organization_id,
            status=OrganizationStatus.ACTIVE,
        )
    )

    organization_url = (
        f"{test_settings.optscale_rest_api_base_url}/organizations/{linked_organization_id}"
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{organization_url}/cloud_accounts",
        match_params={"details": "true"},
        status_code=status_code,
    )

    day_start = int(datetime(2025, 3, 19, 0, 0, 0, tzinfo=UTC).timestamp())
    day_end = int(datetime(2025, 3, 19, 23, 59, 59, tzinfo=UTC).timestamp())
    httpx_mock.add_response(
        method="GET",
        url=f"{organization_url}/breakdown_expenses",
        match_params={
            "start_date": str(day_start),
            "end_date": str(day_end),
            "breakdown_by": "cloud_account_id",
        },
        status_code=status_code,
    )

    with caplog.at_level(logging.WARNING):
        await fetch_datasource_expenses.main(test_settings)

    for expected_log in expected_log_format:
        assert (
            fetch_datasource_expenses.logger.name,
            expected_log_level,
            expected_log % organization.id,
        ) in caplog.record_tuples

    new_datasource_expenses = await DatasourceExpenseHandler(db_session).query_db(unique=True)
    assert len(new_datasource_expenses) == 0

    optscale_paths = [
        str(request.url).split("?")[0] for request in httpx_mock.get_requests(method="GET")
    ]
    assert optscale_paths.count(f"{organization_url}/cloud_accounts") == 1
    assert optscale_paths.count(f"{organization_url}/breakdown_expenses") == 1

    notifications = httpx_mock.get_requests(method="POST", url=webhook_url)
    assert len(notifications) == expected_error_notifications + 1

    error_notifications = [
        notification
        for notification in notifications
        if "Datasource Expenses Update Error" in notification.content.decode()
    ]
    assert len(error_notifications) == expected_error_notifications

    summary = notifications[-1].content.decode()
    assert "Datasource expenses updated for 1 organizations" in summary
    assert "0 data sources expenses processed" in summary


@time_machine.travel("2025-03-20T10:00:00Z", tick=False)
async def test_multiple_datasources_are_handled_correctly(
    caplog: pytest.LogCaptureFixture,
    test_settings: Settings,
    db_session: AsyncSession,
    httpx_mock: HTTPXMock,
) -> None:
    """Four organizations are processed in one run, each with its own datasource mix.

    Covers, in a single run: monthly totals updated in place, monthly totals created for
    unseen datasources, previous-month rows left alone, yesterday's daily expenses applied,
    child datasources (``azure_tenant`` / ``gcp_tenant``) skipped, and an organization whose
    Optscale endpoints fail being skipped without aborting the others.

    Optscale and the MSTeams webhook are stubbed at the HTTP level with ``httpx_mock``, so the
    real ``OptscaleClient``, the real notification code and the real DB handlers run.
    """
    webhook_url = get_settings().msteams_notifications_webhook_url
    httpx_mock.add_response(
        method="POST",
        url=webhook_url,
        status_code=status.HTTP_202_ACCEPTED,
    )

    day_start = int(datetime(2025, 3, 19, 0, 0, 0, tzinfo=UTC).timestamp())
    day_end = int(datetime(2025, 3, 19, 23, 59, 59, tzinfo=UTC).timestamp())

    def stub_optscale(
        linked_organization_id: str,
        cloud_accounts: list[dict] | None = None,
        daily_counts: dict[str, dict] | None = None,
        cloud_accounts_status_code: int = status.HTTP_200_OK,
        daily_expenses_status_code: int = status.HTTP_200_OK,
    ) -> None:
        """Stub both Optscale endpoints for one organization."""
        organization_url = (
            f"{test_settings.optscale_rest_api_base_url}/organizations/{linked_organization_id}"
        )
        httpx_mock.add_response(
            method="GET",
            url=f"{organization_url}/cloud_accounts",
            match_params={"details": "true"},
            match_headers={"Secret": test_settings.optscale_cluster_secret},
            status_code=cloud_accounts_status_code,
            json={"cloud_accounts": cloud_accounts or []},
        )
        httpx_mock.add_response(
            method="GET",
            url=f"{organization_url}/breakdown_expenses",
            match_params={
                "start_date": str(day_start),
                "end_date": str(day_end),
                "breakdown_by": "cloud_account_id",
            },
            match_headers={"Secret": test_settings.optscale_cluster_secret},
            status_code=daily_expenses_status_code,
            json={
                "counts": daily_counts or {},
                "start_date": day_start,
                "end_date": day_end,
                "breakdown_by": "cloud_account_id",
            },
        )

    organization_handler = OrganizationHandler(db_session)
    linked_organization_ids = [str(uuid.uuid4()) for _ in range(4)]
    organization1, organization2, organization3, organization4 = [
        await organization_handler.create(
            Organization(
                name=f"ACME Inc {index}",
                currency="USD",
                billing_currency="USD",
                operations_external_id=f"org_{index}_external_id",
                linked_organization_id=linked_organization_id,
                status=OrganizationStatus.ACTIVE,
            )
        )
        for index, linked_organization_id in enumerate(linked_organization_ids, start=1)
    ]

    org1_datasource_id1 = str(uuid.uuid4())
    org1_datasource_id2 = str(uuid.uuid4())
    org1_datasource_id3 = str(uuid.uuid4())
    org1_datasource_id4 = str(uuid.uuid4())

    org2_datasource_id1 = str(uuid.uuid4())
    org2_datasource_id2 = str(uuid.uuid4())

    org3_datasource_id1 = str(uuid.uuid4())

    datasource_expense_handler = DatasourceExpenseHandler(db_session)

    # previous month: must be left untouched
    await datasource_expense_handler.create(
        DatasourceExpense(
            organization=organization1,
            linked_datasource_id=org1_datasource_id1,
            linked_datasource_type=DatasourceType.AWS_CNR,
            datasource_name="Org 1 first cloud account",
            datasource_id="11111111",
            year=2025,
            month=2,
            day=20,
            total_expenses=Decimal("123.45"),
        )
    )

    # current month totals: must be updated with the figures returned by Optscale
    await datasource_expense_handler.create(
        DatasourceExpense(
            organization=organization1,
            linked_datasource_id=org1_datasource_id1,
            linked_datasource_type=DatasourceType.AWS_CNR,
            datasource_name="Org 1 first cloud account",
            datasource_id="11111111",
            year=2025,
            month=3,
            day=20,
            total_expenses=Decimal("234.56"),
        )
    )

    await datasource_expense_handler.create(
        DatasourceExpense(
            organization=organization1,
            linked_datasource_id=org1_datasource_id2,
            linked_datasource_type=DatasourceType.AWS_CNR,
            datasource_name="Org 1 second cloud account",
            datasource_id="12222222",
            year=2025,
            month=3,
            day=20,
            total_expenses=Decimal("567.89"),
        )
    )

    await datasource_expense_handler.create(
        DatasourceExpense(
            organization=organization2,
            linked_datasource_id=org2_datasource_id1,
            linked_datasource_type=DatasourceType.AWS_CNR,
            datasource_name="Org 2 first cloud account",
            datasource_id="21111111",
            year=2025,
            month=3,
            day=20,
            total_expenses=Decimal("999.88"),
            expenses=Decimal("56.78"),
        )
    )

    # yesterday: must receive the daily expenses
    await datasource_expense_handler.create(
        DatasourceExpense(
            organization=organization1,
            linked_datasource_id=org1_datasource_id1,
            linked_datasource_type=DatasourceType.AWS_CNR,
            datasource_name="Org 1 first cloud account",
            datasource_id="11111111",
            year=2025,
            month=3,
            day=19,
            total_expenses=Decimal("123.45"),
        )
    )

    await datasource_expense_handler.create(
        DatasourceExpense(
            organization=organization2,
            linked_datasource_id=org2_datasource_id1,
            linked_datasource_type=DatasourceType.AWS_CNR,
            datasource_name="Org 2 first cloud account",
            datasource_id="21111111",
            year=2025,
            month=3,
            day=19,
            total_expenses=Decimal("123.45"),
        )
    )

    await datasource_expense_handler.create(
        DatasourceExpense(
            organization=organization3,
            linked_datasource_id=org3_datasource_id1,
            linked_datasource_type=DatasourceType.AWS_CNR,
            datasource_name="Org 3 first cloud account",
            datasource_id="31111111",
            year=2025,
            month=3,
            day=19,
            total_expenses=Decimal("123.45"),
        )
    )

    existing_datasource_expenses = await datasource_expense_handler.query_db(unique=True)
    assert len(existing_datasource_expenses) == 7

    stub_optscale(
        linked_organization_ids[0],
        cloud_accounts=[
            {
                "id": org1_datasource_id1,
                "account_id": "11111111",
                "type": DatasourceType.AWS_CNR.value,
                "name": "Org 1 first cloud account",
                "details": {"cost": 789.01},
            },
            {
                "id": org1_datasource_id2,
                "account_id": "12222222",
                "type": DatasourceType.AWS_CNR.value,
                "name": "Org 1 second cloud account",
                "details": {"cost": 678.90},
            },
            # child datasources: skipped before their expenses are ever read
            {
                "id": org1_datasource_id3,
                "account_id": "13333333",
                "type": "azure_tenant",
                "name": "Org 1 azure tenant",
            },
            {
                "id": org1_datasource_id4,
                "account_id": "14444444",
                "type": "gcp_tenant",
                "name": "Org 1 gcp tenant",
            },
        ],
        daily_counts={
            org1_datasource_id1: {
                "id": org1_datasource_id1,
                "account_id": "11111111",
                "type": DatasourceType.AWS_CNR.value,
                "name": "Org 1 first cloud account",
                "total": 12.34,
            },
        },
    )

    stub_optscale(
        linked_organization_ids[1],
        cloud_accounts=[
            {
                "id": org2_datasource_id1,
                "account_id": "21111111",
                "type": DatasourceType.AWS_CNR.value,
                "name": "Org 2 first cloud account",
                "details": {"cost": 234.56},
            },
            {
                "id": org2_datasource_id2,
                "account_id": "22222222",
                "type": DatasourceType.AWS_CNR.value,
                "name": "Org 2 second cloud account",
                "details": {"cost": 654.32},
            },
        ],
        daily_counts={
            org2_datasource_id1: {
                "id": org2_datasource_id1,
                "account_id": "21111111",
                "type": DatasourceType.AWS_CNR.value,
                "name": "Org 2 first cloud account",
                "total": 12.34,
            },
        },
    )

    stub_optscale(
        linked_organization_ids[2],
        cloud_accounts=[
            {
                "id": org3_datasource_id1,
                "account_id": "31111111",
                "type": DatasourceType.AZURE_CNR.value,
                "name": "Org 3 first cloud account",
                "details": {"cost": 777.88},
            }
        ],
        daily_counts={
            org3_datasource_id1: {
                "id": org3_datasource_id1,
                "account_id": "31111111",
                "type": DatasourceType.AWS_CNR.value,
                "name": "Org 3 first cloud account",
                "total": 12.34,
            },
        },
    )

    # the fourth organization is unknown to Optscale: warnings only, nothing stored
    stub_optscale(
        linked_organization_ids[3],
        cloud_accounts_status_code=status.HTTP_404_NOT_FOUND,
        daily_expenses_status_code=status.HTTP_424_FAILED_DEPENDENCY,
    )

    with caplog.at_level(logging.WARNING):
        await fetch_datasource_expenses.main(test_settings)

    assert f"Skipping child datasource {org1_datasource_id3} of type azure_tenant" in caplog.text
    assert f"Skipping child datasource {org1_datasource_id4} of type gcp_tenant" in caplog.text
    assert (
        f"Organization {organization4.id} not found or "
        "organization doesn't have any cloud accounts connected in Optscale."
    ) in caplog.text

    # the organizations are processed in their own sessions, so drop what this one has cached
    db_session.expire_all()
    new_datasource_expenses = await datasource_expense_handler.query_db(unique=True)

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
        # organization 1: previous month untouched
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
        # organization 1: current month totals updated
        (
            organization1.id,
            org1_datasource_id1,
            "11111111",
            2025,
            3,
            20,
            Decimal("789.0100"),
            Decimal("0.0000"),
        ),
        (
            organization1.id,
            org1_datasource_id2,
            "12222222",
            2025,
            3,
            20,
            Decimal("678.9000"),
            Decimal("0.0000"),
        ),
        # organization 2: existing total updated, daily expenses preserved
        (
            organization2.id,
            org2_datasource_id1,
            "21111111",
            2025,
            3,
            20,
            Decimal("234.5600"),
            Decimal("56.7800"),
        ),
        # organization 2: total created for the datasource seen for the first time
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
        # organization 3: total created for the current month
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
        # yesterday's daily expenses applied to the pre-existing rows
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

    # organization 4 stored nothing but is still reported as processed
    notifications = httpx_mock.get_requests(method="POST", url=webhook_url)
    assert len(notifications) == 1
    assert "Datasource expenses updated for 4 organizations" in notifications[0].content.decode()


@time_machine.travel("2025-03-20T10:00:00Z", tick=False)
async def test_main_sends_one_success_notification_for_all_organizations(
    test_settings: Settings,
    db_session: AsyncSession,
    httpx_mock: HTTPXMock,
) -> None:
    """A run over several organizations sends a single summary notification, not one per org."""
    webhook_url = get_settings().msteams_notifications_webhook_url
    httpx_mock.add_response(
        method="POST",
        url=webhook_url,
        status_code=status.HTTP_202_ACCEPTED,
    )

    day_start = int(datetime(2025, 3, 19, 0, 0, 0, tzinfo=UTC).timestamp())
    day_end = int(datetime(2025, 3, 19, 23, 59, 59, tzinfo=UTC).timestamp())
    for index in range(2):
        linked_organization_id = str(uuid.uuid4())
        await OrganizationHandler(db_session).create(
            Organization(
                name=f"ACME Inc {index}",
                currency="USD",
                billing_currency="USD",
                operations_external_id=f"NOTIFY_{index}",
                linked_organization_id=linked_organization_id,
                status=OrganizationStatus.ACTIVE,
            )
        )
        organization_url = (
            f"{test_settings.optscale_rest_api_base_url}/organizations/{linked_organization_id}"
        )
        httpx_mock.add_response(
            method="GET",
            url=f"{organization_url}/cloud_accounts",
            match_params={"details": "true"},
            match_headers={"Secret": test_settings.optscale_cluster_secret},
            json={
                "cloud_accounts": [
                    {
                        "id": str(uuid.uuid4()),
                        "account_id": str(uuid.uuid4()),
                        "type": DatasourceType.AWS_CNR.value,
                        "name": "cloud account",
                        "details": {"cost": 10.0},
                    }
                ]
            },
        )
        httpx_mock.add_response(
            method="GET",
            url=f"{organization_url}/breakdown_expenses",
            match_params={
                "start_date": str(day_start),
                "end_date": str(day_end),
                "breakdown_by": "cloud_account_id",
            },
            match_headers={"Secret": test_settings.optscale_cluster_secret},
            json={
                "counts": {},
                "start_date": day_start,
                "end_date": day_end,
                "breakdown_by": "cloud_account_id",
            },
        )

    await fetch_datasource_expenses.main(test_settings)

    notifications = httpx_mock.get_requests(method="POST", url=webhook_url)
    assert len(notifications) == 1
    message = notifications[0].content.decode()
    assert "2 organizations" in message
    assert "Datasource Expenses Update Success" in message
    assert "Datasource Expenses Update Partial Failure" not in message


@pytest.mark.transactional_db
@time_machine.travel("2025-03-20T10:00:00Z", tick=False)
async def test_each_organization_commits_in_its_own_transaction(
    test_settings: Settings,
    db_session: AsyncSession,
    httpx_mock: HTTPXMock,
) -> None:
    """Every organization's expenses are committed by its own session, in parallel."""
    webhook_url = get_settings().msteams_notifications_webhook_url
    httpx_mock.add_response(
        method="POST",
        url=webhook_url,
        status_code=status.HTTP_202_ACCEPTED,
    )
    settings = test_settings.model_copy(update={"max_parallel_tasks": 5})

    day_start = int(datetime(2025, 3, 19, 0, 0, 0, tzinfo=UTC).timestamp())
    day_end = int(datetime(2025, 3, 19, 23, 59, 59, tzinfo=UTC).timestamp())
    organizations = []
    for index in range(5):
        linked_organization_id = str(uuid.uuid4())
        organizations.append(
            await OrganizationHandler(db_session).create(
                Organization(
                    name=f"ACME Inc {index}",
                    currency="USD",
                    billing_currency="USD",
                    operations_external_id=f"org_{index}_ext_id",
                    linked_organization_id=linked_organization_id,
                    status=OrganizationStatus.ACTIVE,
                )
            )
        )
        organization_url = (
            f"{settings.optscale_rest_api_base_url}/organizations/{linked_organization_id}"
        )
        httpx_mock.add_response(
            method="GET",
            url=f"{organization_url}/cloud_accounts",
            match_params={"details": "true"},
            match_headers={"Secret": settings.optscale_cluster_secret},
            json={
                "cloud_accounts": [
                    {
                        "id": str(uuid.uuid4()),
                        "account_id": str(uuid.uuid4()),
                        "type": DatasourceType.AWS_CNR.value,
                        "name": "cloud account",
                        "details": {"cost": 10.0},
                    }
                ]
            },
        )
        httpx_mock.add_response(
            method="GET",
            url=f"{organization_url}/breakdown_expenses",
            match_params={
                "start_date": str(day_start),
                "end_date": str(day_end),
                "breakdown_by": "cloud_account_id",
            },
            match_headers={"Secret": settings.optscale_cluster_secret},
            json={
                "counts": {},
                "start_date": day_start,
                "end_date": day_end,
                "breakdown_by": "cloud_account_id",
            },
        )

    # the organizations must be visible to the sessions the run opens on other connections
    await db_session.commit()

    await fetch_datasource_expenses.main(settings)

    async with session_factory() as verify_session:
        rows = await DatasourceExpenseHandler(verify_session).query_db(unique=True)
    assert {row.organization_id for row in rows} == {org.id for org in organizations}


@pytest.mark.transactional_db
@time_machine.travel("2025-03-20T10:00:00Z", tick=False)
async def test_one_organization_failure(
    test_settings: Settings,
    db_session: AsyncSession,
    httpx_mock: HTTPXMock,
) -> None:
    """One organization failing rolls back only its own transaction and is reported as failed.

    The broken organization's daily expenses come back without the ``name`` Optscale always
    sends, which makes storing them raise inside that organization's transaction.
    """
    webhook_url = get_settings().msteams_notifications_webhook_url
    httpx_mock.add_response(
        method="POST",
        url=webhook_url,
        status_code=status.HTTP_202_ACCEPTED,
    )
    settings = test_settings.model_copy(update={"max_parallel_tasks": 5})

    day_start = int(datetime(2025, 3, 19, 0, 0, 0, tzinfo=UTC).timestamp())
    day_end = int(datetime(2025, 3, 19, 23, 59, 59, tzinfo=UTC).timestamp())

    def stub_optscale(linked_organization_id: str, daily_counts: dict[str, dict]) -> None:
        """Stub both Optscale endpoints for one organization."""
        organization_url = (
            f"{settings.optscale_rest_api_base_url}/organizations/{linked_organization_id}"
        )
        httpx_mock.add_response(
            method="GET",
            url=f"{organization_url}/cloud_accounts",
            match_params={"details": "true"},
            match_headers={"Secret": settings.optscale_cluster_secret},
            json={
                "cloud_accounts": [
                    {
                        "id": str(uuid.uuid4()),
                        "account_id": str(uuid.uuid4()),
                        "type": DatasourceType.AWS_CNR.value,
                        "name": "cloud account",
                        "details": {"cost": 10.0},
                    }
                ]
            },
        )
        httpx_mock.add_response(
            method="GET",
            url=f"{organization_url}/breakdown_expenses",
            match_params={
                "start_date": str(day_start),
                "end_date": str(day_end),
                "breakdown_by": "cloud_account_id",
            },
            match_headers={"Secret": settings.optscale_cluster_secret},
            json={
                "counts": daily_counts,
                "start_date": day_start,
                "end_date": day_end,
                "breakdown_by": "cloud_account_id",
            },
        )

    healthy_linked_organization_id = str(uuid.uuid4())
    healthy = await OrganizationHandler(db_session).create(
        Organization(
            name="Healthy Inc",
            currency="USD",
            billing_currency="USD",
            operations_external_id="org_1_ext_id",
            linked_organization_id=healthy_linked_organization_id,
            status=OrganizationStatus.ACTIVE,
        )
    )
    stub_optscale(healthy_linked_organization_id, daily_counts={})

    broken_linked_organization_id = str(uuid.uuid4())
    broken = await OrganizationHandler(db_session).create(
        Organization(
            name="Broken Inc",
            currency="USD",
            billing_currency="USD",
            operations_external_id="org_2_ext_id",
            linked_organization_id=broken_linked_organization_id,
            status=OrganizationStatus.ACTIVE,
        )
    )
    broken_datasource_id = str(uuid.uuid4())
    stub_optscale(
        broken_linked_organization_id,
        daily_counts={
            broken_datasource_id: {
                "id": broken_datasource_id,
                "account_id": str(uuid.uuid4()),
                "type": DatasourceType.AWS_CNR.value,
                "total": 5.0,
                # NOTE: no "name", which is what makes storing this organization fail
            }
        },
    )

    # the organizations must be visible to the sessions the run opens on other connections
    await db_session.commit()

    await fetch_datasource_expenses.main(settings)

    async with session_factory() as verify_session:
        rows = await DatasourceExpenseHandler(verify_session).query_db(unique=True)
    committed_org_ids = {row.organization_id for row in rows}
    assert healthy.id in committed_org_ids
    assert broken.id not in committed_org_ids

    notification = httpx_mock.get_request(method="POST", url=webhook_url)
    assert notification is not None
    message = notification.content.decode()
    assert "Datasource Expenses Update Partial Failure" in message
    assert "1 failed" in message
    assert "Datasource expenses updated for 1 organizations" in message


def test_cli_command(mocker: MockerFixture):
    mock_command_coro = mocker.MagicMock()
    mock_command = mocker.MagicMock(return_value=mock_command_coro)

    mocker.patch("app.commands.fetch_datasource_expenses.main", mock_command)
    mock_run = mocker.patch("app.commands.fetch_datasource_expenses.asyncio.run")
    runner = CliRunner()

    result = runner.invoke(app, ["fetch-datasource-expenses"])
    assert result.exit_code == 0
    mock_run.assert_called_once_with(mock_command_coro)


async def test_main_wires_max_parallel_tasks_into_the_semaphore(
    mocker: MockerFixture,
    test_settings: Settings,
):
    """Guards that main() builds the semaphore from settings.max_parallel_tasks."""
    mocker.patch.object(test_settings, "max_parallel_tasks", 7)
    mocker.patch.object(
        fetch_datasource_expenses,
        "OrganizationHandler",
        side_effect=RuntimeError("stop here"),
    )
    semaphore_spy = mocker.patch.object(
        fetch_datasource_expenses.asyncio, "Semaphore", wraps=asyncio.Semaphore
    )

    with pytest.raises(RuntimeError, match="stop here"):
        await fetch_datasource_expenses.main(test_settings)

    semaphore_spy.assert_called_once_with(7)
