import asyncio
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx
import pytest
from freezegun import freeze_time
from pytest_httpx import HTTPXMock
from pytest_mock import MockerFixture
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typer.testing import CliRunner

from app.api_clients.mpt import MPTClient
from app.cli import app
from app.commands.sync_subscriptions import (
    DEFAULT_STATUS_LIST,
    SyncResult,
    build_notification_details,
    build_query,
    main,
    report,
    sync_account,
    sync_page,
    sync_subscription,
)
from app.conf import Settings
from app.db.handlers import EntitlementHandler
from app.db.models import Account, Entitlement
from app.enums import AccountStatus, AccountType, EntitlementStatus
from app.events.subscriptions.constants import (
    ACTIVE_SUBSCRIPTION_STATUS,
    EXPIRED_SUBSCRIPTION_STATUS,
    TERMINATED_SUBSCRIPTION_STATUS,
)
from app.notifications import ColumnHeader
from tests.types import ModelFactory, MPTSubscriptionFactory, SubscriptionsPageMocker

SUBSCRIPTION_ID = "SUB-1234-5678"
DATASOURCE_ID = "ds0001234"
SINCE = datetime(2026, 9, 12, 9, 0, 0, tzinfo=UTC)
UNTIL = datetime(2026, 9, 13, 9, 0, 0, tzinfo=UTC)
WINDOW = "changed between 2026-09-12 09:00:00 UTC and 2026-09-13 09:00:00 UTC"


@pytest.fixture
def entitlement_handler(db_session: AsyncSession) -> EntitlementHandler:
    return EntitlementHandler(db_session)


@pytest.fixture
def mock_subscriptions_api(httpx_mock: HTTPXMock) -> SubscriptionsPageMocker:
    def _mock(subscriptions: list[dict[str, Any]]) -> None:
        def respond(request: httpx.Request) -> httpx.Response:
            params = dict(
                pair.split("=", 1) for pair in request.url.query.decode().split("&") if "=" in pair
            )
            limit, offset = int(params["limit"]), int(params["offset"])
            return httpx.Response(
                status_code=200,
                json={
                    "data": subscriptions[offset : offset + limit],
                    "$meta": {
                        "pagination": {
                            "total": len(subscriptions),
                            "limit": limit,
                            "offset": offset,
                        }
                    },
                },
            )

        httpx_mock.add_callback(respond, method="GET", is_reusable=True)

    return _mock


async def get_entitlements(db_session: AsyncSession, owner: Account) -> list[Entitlement]:
    result = await db_session.execute(
        select(Entitlement)
        .where(Entitlement.owner == owner)
        .order_by(Entitlement.datasource_id.asc())
    )
    return list(result.scalars().all())


@pytest.mark.parametrize(
    ("status", "expected_status_filter"),
    [
        (DEFAULT_STATUS_LIST, "in(status,(Active,Expired,Terminated))"),
        ([ACTIVE_SUBSCRIPTION_STATUS], "in(status,(Active))"),
        ([EXPIRED_SUBSCRIPTION_STATUS], "in(status,(Expired))"),
    ],
)
def test_build_query_filters_by_product_status_and_window(
    status: list[str],
    expected_status_filter: str,
) -> None:
    query = build_query(["PRD-1111-1111", "PRD-2222-2222"], status, SINCE, UNTIL)

    assert query == (
        "and("
        "in(product.id,(PRD-1111-1111,PRD-2222-2222)),"
        f"{expected_status_filter},"
        "or(and(gt(audit.created.at,2026-09-12T09:00:00.000Z),"
        "lt(audit.created.at,2026-09-13T09:00:00.000Z)),"
        "and(gt(audit.updated.at,2026-09-12T09:00:00.000Z),"
        "lt(audit.updated.at,2026-09-13T09:00:00.000Z)))"
        ")"
    )


async def test_sync_subscription_creates_missing_entitlement(
    entitlement_handler: EntitlementHandler,
    subscription_account: Account,
    mpt_subscription_factory: MPTSubscriptionFactory,
    db_session: AsyncSession,
) -> None:
    subscription = mpt_subscription_factory()

    result = await sync_subscription(entitlement_handler, subscription_account, subscription, [])

    entitlement = (await get_entitlements(db_session, subscription_account))[0]
    assert entitlement.status == EntitlementStatus.NEW
    assert entitlement.datasource_id == DATASOURCE_ID
    assert entitlement.affiliate_external_id == SUBSCRIPTION_ID
    assert entitlement.name == subscription["name"]

    assert result is not None
    assert result.subscription_id == SUBSCRIPTION_ID
    assert result.account_id == subscription_account.id
    assert result.message == f"Created new entitlement {entitlement.id}."
    assert result.succeeded is True


async def test_sync_subscription_skips_an_active_subscription_with_active_entitlement(
    entitlement_handler: EntitlementHandler,
    subscription_account: Account,
    mpt_subscription_factory: MPTSubscriptionFactory,
    entitlement_factory: ModelFactory[Entitlement],
) -> None:
    entitlement = await entitlement_factory(
        owner=subscription_account,
        datasource_id=DATASOURCE_ID,
        status=EntitlementStatus.ACTIVE,
    )
    subscription = mpt_subscription_factory()

    result = await sync_subscription(
        entitlement_handler, subscription_account, subscription, [entitlement]
    )

    assert result is None


async def test_sync_subscription_reports_more_than_one_live_entitlement(
    entitlement_handler: EntitlementHandler,
    subscription_account: Account,
    mpt_subscription_factory: MPTSubscriptionFactory,
    entitlement_factory: ModelFactory[Entitlement],
    db_session: AsyncSession,
) -> None:
    first = await entitlement_factory(
        owner=subscription_account, datasource_id=DATASOURCE_ID, status=EntitlementStatus.NEW
    )
    second = await entitlement_factory(
        owner=subscription_account, datasource_id=DATASOURCE_ID, status=EntitlementStatus.ACTIVE
    )
    subscription = mpt_subscription_factory()

    result = await sync_subscription(
        entitlement_handler, subscription_account, subscription, [first, second]
    )

    assert result is not None
    assert result.succeeded is False
    assert result.error == "Subscription has more than one new and/or active entitlement."
    assert first.id in result.message
    assert second.id in result.message

    assert len(await get_entitlements(db_session, subscription_account)) == 2


@pytest.mark.parametrize(
    "subscription_status",
    [TERMINATED_SUBSCRIPTION_STATUS, EXPIRED_SUBSCRIPTION_STATUS],
)
async def test_sync_subscription_ignore_non_active_subscription_without_entitlements(
    entitlement_handler: EntitlementHandler,
    subscription_account: Account,
    mpt_subscription_factory: MPTSubscriptionFactory,
    subscription_status: str,
) -> None:
    subscription = mpt_subscription_factory(status=subscription_status)

    result = await sync_subscription(entitlement_handler, subscription_account, subscription, [])

    assert result is None


@pytest.mark.parametrize(
    "subscription_status",
    [TERMINATED_SUBSCRIPTION_STATUS, EXPIRED_SUBSCRIPTION_STATUS],
)
async def test_sync_subscription_actions_for_non_active_subscription(
    entitlement_handler: EntitlementHandler,
    subscription_account: Account,
    mpt_subscription_factory: MPTSubscriptionFactory,
    entitlement_factory: ModelFactory[Entitlement],
    db_session: AsyncSession,
    subscription_status: str,
) -> None:
    new_ent = await entitlement_factory(
        owner=subscription_account, datasource_id=DATASOURCE_ID, status=EntitlementStatus.NEW
    )
    active_ent = await entitlement_factory(
        owner=subscription_account, datasource_id=DATASOURCE_ID, status=EntitlementStatus.ACTIVE
    )
    subscription = mpt_subscription_factory(status=subscription_status)

    result = await sync_subscription(
        entitlement_handler, subscription_account, subscription, [new_ent, active_ent]
    )

    await db_session.refresh(new_ent)
    assert new_ent.status == EntitlementStatus.DELETED

    await db_session.refresh(active_ent)
    assert active_ent.status == EntitlementStatus.TERMINATED
    assert active_ent.terminated_at is not None

    assert result is not None
    assert f"The entitlement {new_ent.id} was deleted." in result.message
    assert f"The entitlement {active_ent.id} was terminated." in result.message
    assert result.succeeded is True


async def test_sync_page(
    mpt_client: MPTClient,
    mock_subscriptions_api: SubscriptionsPageMocker,
    subscription_account: Account,
    mpt_subscription_factory: MPTSubscriptionFactory,
    entitlement_factory: ModelFactory[Entitlement],
    db_session: AsyncSession,
) -> None:
    ent = await entitlement_factory(
        owner=subscription_account,
        datasource_id=DATASOURCE_ID,
        status=EntitlementStatus.ACTIVE,
    )
    synced_sub = mpt_subscription_factory()

    sub_1 = mpt_subscription_factory(subscription_id="SUB-0000-0001", datasource_id="ds0000001")
    sub_2 = mpt_subscription_factory(subscription_id="SUB-0000-0002", datasource_id="ds0000002")
    mock_subscriptions_api([sub_1, sub_2, synced_sub])

    results = await sync_page(
        mpt_client,
        "and(...)",
        offset=0,
        page_size=50,
        account_id=subscription_account.id,
        dry_run=False,
        semaphore=asyncio.Semaphore(1),
    )

    assert [result.subscription_id for result in results] == ["SUB-0000-0001", "SUB-0000-0002"]

    entitlements = await get_entitlements(db_session, subscription_account)
    assert [entitlement.datasource_id for entitlement in entitlements] == [
        "ds0000001",
        "ds0000002",
        ent.datasource_id,
    ]


async def test_sync_page_dry_run(
    mpt_client: MPTClient,
    mock_subscriptions_api: SubscriptionsPageMocker,
    subscription_account: Account,
    mpt_subscription_factory: MPTSubscriptionFactory,
    db_session: AsyncSession,
) -> None:
    mock_subscriptions_api([mpt_subscription_factory()])

    results = await sync_page(
        mpt_client,
        "and(...)",
        offset=0,
        page_size=50,
        account_id=subscription_account.id,
        dry_run=True,
        semaphore=asyncio.Semaphore(1),
    )

    assert len(results) == 1
    assert results[0].subscription_id == SUBSCRIPTION_ID

    assert await get_entitlements(db_session, subscription_account) == []


async def test_sync_page_fetch_subscriptions_fails(
    mpt_client: MPTClient,
    httpx_mock: HTTPXMock,
    subscription_account: Account,
    caplog: pytest.LogCaptureFixture,
) -> None:
    httpx_mock.add_response(method="GET", status_code=500)

    with caplog.at_level("ERROR"):
        results = await sync_page(
            mpt_client,
            "and(...)",
            offset=100,
            page_size=50,
            account_id=subscription_account.id,
            dry_run=False,
            semaphore=asyncio.Semaphore(1),
        )

    assert len(results) == 1
    assert results[0].succeeded is False
    assert results[0].subscription_id is None
    assert results[0].account_id == subscription_account.id
    assert "offset=100" in results[0].message
    assert "failed to sync the page" in caplog.text


async def test_sync_account_empty_window(
    mocker: MockerFixture,
    mpt_client: MPTClient,
    mock_subscriptions_api: SubscriptionsPageMocker,
    subscription_account: Account,
    caplog: pytest.LogCaptureFixture,
) -> None:
    mocker.patch("app.commands.sync_subscriptions.get_installation_client", return_value=mpt_client)
    mock_subscriptions_api([])

    with caplog.at_level("INFO"):
        results = await sync_account(
            subscription_account,
            DEFAULT_STATUS_LIST,
            SINCE,
            UNTIL,
            page_size=50,
            dry_run=False,
            semaphore=asyncio.Semaphore(1),
        )

    assert results == []
    assert "no subscription events within the window" in caplog.text


async def test_sync_account_returns_one_flat_list_for_every_page(
    mocker: MockerFixture,
    mpt_client: MPTClient,
    mock_subscriptions_api: SubscriptionsPageMocker,
    subscription_account: Account,
    mpt_subscription_factory: MPTSubscriptionFactory,
) -> None:
    mocker.patch("app.commands.sync_subscriptions.get_installation_client", return_value=mpt_client)
    subscriptions = [
        mpt_subscription_factory(
            subscription_id=f"SUB-0000-000{index}", datasource_id=f"ds000000{index}"
        )
        for index in range(3)
    ]
    mock_subscriptions_api(subscriptions)

    results = await sync_account(
        subscription_account,
        DEFAULT_STATUS_LIST,
        SINCE,
        UNTIL,
        page_size=2,
        dry_run=False,
        semaphore=asyncio.Semaphore(1),
    )

    assert all(isinstance(result, SyncResult) for result in results)
    assert [result.subscription_id for result in results] == [
        subscription["id"] for subscription in subscriptions
    ]


def test_build_notification_details() -> None:
    details = build_notification_details(
        [
            SyncResult(
                account_id="ACC-1234-5678",
                subscription_id=SUBSCRIPTION_ID,
                message="Created new entitlement ENT-1234-5678.",
            ),
            SyncResult(
                account_id="ACC-1234-5678",
                message="Failed to sync page.",
                error="Offset 50.",
            ),
        ]
    )

    assert details.header == (
        ColumnHeader(text="Account", width="stretch"),
        ColumnHeader(text="Subscription", width="stretch"),
        ColumnHeader(text="Action", width="stretch"),
        ColumnHeader(text="Details", width="stretch"),
    )
    assert details.rows == [
        ("ACC-1234-5678", SUBSCRIPTION_ID, "Created new entitlement ENT-1234-5678.", ""),
        ("ACC-1234-5678", "", "Failed to sync page.", "Offset 50."),
    ]


async def test_report_success_all_synced(mocker: MockerFixture) -> None:
    mocked_send_info = mocker.patch("app.commands.sync_subscriptions.send_info")

    await report([], SINCE, UNTIL)

    assert mocked_send_info.await_count == 1
    assert mocked_send_info.await_args is not None
    assert mocked_send_info.await_args.args == (
        "Subscriptions Sync Success",
        f"Checked subscriptions {WINDOW}: all in sync.",
    )
    assert "details" not in mocked_send_info.await_args.kwargs


async def test_report_success_applied_changes(mocker: MockerFixture) -> None:
    mocked_send_info = mocker.patch("app.commands.sync_subscriptions.send_info")
    results = [
        SyncResult(
            account_id="ACC-1234-5678",
            subscription_id=SUBSCRIPTION_ID,
            message="Created new entitlement ENT-1234-5678.",
        )
    ]

    await report(results, SINCE, UNTIL)

    assert mocked_send_info.await_args is not None
    assert mocked_send_info.await_args.args == (
        "Subscriptions Sync Applied Changes",
        f"Checked subscriptions {WINDOW} and synced 1 subscriptions.",
    )
    assert len(mocked_send_info.await_args.kwargs["details"].rows) == 1


async def test_report_partial_fail(
    mocker: MockerFixture,
    caplog: pytest.LogCaptureFixture,
) -> None:
    mocked_send_error = mocker.patch("app.commands.sync_subscriptions.send_error")
    results = [
        SyncResult(
            account_id="ACC-1234-5678",
            subscription_id="SUB-0000-0001",
            message="Created new entitlement ENT-1234-5678.",
        ),
        SyncResult(
            account_id="ACC-1234-5678",
            subscription_id="SUB-0000-0002",
            message="Found active and new entitlements: ENT-1, ENT-2.",
            error="Subscription has more than one new and/or active entitlement.",
        ),
    ]

    with caplog.at_level("WARNING"):
        await report(results, SINCE, UNTIL)

    assert mocked_send_error.await_count == 1
    assert mocked_send_error.await_args is not None
    assert mocked_send_error.await_args.args == (
        "Subscriptions Sync Partial Failure",
        f"Checked subscriptions {WINDOW}. Partially failed to sync.",
    )
    assert len(mocked_send_error.await_args.kwargs["details"].rows) == 2
    assert "Partially failed to sync." in caplog.text


def test_sync_subscriptions_command(mocker: MockerFixture, test_settings: Settings) -> None:
    mock_coro = mocker.MagicMock()
    mock_main = mocker.MagicMock(return_value=mock_coro)

    mocker.patch("app.commands.sync_subscriptions.main", mock_main)
    mock_run = mocker.patch("app.commands.sync_subscriptions.asyncio.run")
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "sync-subscriptions",
            "--account",
            "ACC-3333-3333",
            "--since",
            "2026-09-12",
            "--page-size",
            "10",
            "--max-parallel",
            "2",
            "--dry-run",
        ],
    )

    assert result.exit_code == 0
    mock_run.assert_called_once_with(mock_coro)
    mock_main.assert_called_once_with(
        test_settings,
        10,
        2,
        24,
        "ACC-3333-3333",
        None,
        datetime(2026, 9, 12, 0, 0, 0),
        None,
        True,
    )


async def test_main_accounts_filter(
    mocker: MockerFixture,
    test_settings: Settings,
    account_factory: ModelFactory[Account],
    subscription_account: Account,
) -> None:
    await account_factory(type=AccountType.OPERATIONS, products="PRD-1111-1111")
    await account_factory(status=AccountStatus.DISABLED, products="PRD-1111-1111")
    await account_factory(products=None)
    await account_factory(products="")
    mocked_sync_account = mocker.patch(
        "app.commands.sync_subscriptions.sync_account", return_value=[]
    )
    mocker.patch("app.commands.sync_subscriptions.send_info")

    await main(test_settings, 50, 5, 24)

    assert [call.args[0].id for call in mocked_sync_account.await_args_list] == [
        subscription_account.id
    ]


async def test_main_with_specified_account(
    mocker: MockerFixture,
    test_settings: Settings,
    account_factory: ModelFactory[Account],
    subscription_account: Account,
) -> None:
    other = await account_factory(external_id="ACC-9999-9999", products="PRD-1111-1111")
    mocked_sync_account = mocker.patch(
        "app.commands.sync_subscriptions.sync_account", return_value=[]
    )
    mocker.patch("app.commands.sync_subscriptions.send_info")

    await main(test_settings, 50, 5, 24, account_external_id=other.external_id)

    assert [call.args[0].id for call in mocked_sync_account.await_args_list] == [other.id]


@freeze_time("2026-03-16 09:00:00")
async def test_main_with_specified_lookback(
    mocker: MockerFixture,
    test_settings: Settings,
    subscription_account: Account,
) -> None:
    mocked_sync_account = mocker.patch(
        "app.commands.sync_subscriptions.sync_account", return_value=[]
    )
    mocker.patch("app.commands.sync_subscriptions.send_info")

    await main(test_settings, 50, 5, 24)

    assert mocked_sync_account.await_args is not None
    since, until = mocked_sync_account.await_args.args[2:4]
    assert until == datetime(2026, 3, 16, 9, 0, 0, tzinfo=UTC)
    assert since == until - timedelta(hours=24)


async def test_main_when_one_account_fails(
    mocker: MockerFixture,
    test_settings: Settings,
    account_factory: ModelFactory[Account],
    subscription_account: Account,
    caplog: pytest.LogCaptureFixture,
) -> None:
    await account_factory(external_id="ACC-9999-9999", products="PRD-1111-1111")

    async def fail_for_the_first_account(account: Account, *args: Any) -> list[SyncResult]:
        if account.id == subscription_account.id:
            raise RuntimeError("error")
        return []

    mocked_sync_account = mocker.patch(
        "app.commands.sync_subscriptions.sync_account",
        side_effect=fail_for_the_first_account,
    )
    mocked_send_error = mocker.patch("app.commands.sync_subscriptions.send_error")

    with caplog.at_level("ERROR"):
        await main(test_settings, 50, 5, 24)

    assert mocked_sync_account.await_count == 2
    assert mocked_send_error.await_count == 1
    assert mocked_send_error.await_args is not None
    assert mocked_send_error.await_args.kwargs["details"].rows == [
        (
            subscription_account.id,
            "",
            f"Failed to sync the subscriptions of account {subscription_account.id}",
            "error",
        )
    ]
    assert f"Failed to sync the subscriptions for account {subscription_account.id}" in caplog.text


async def test_main_log_on_a_dry_run(
    mocker: MockerFixture,
    test_settings: Settings,
    subscription_account: Account,
    caplog: pytest.LogCaptureFixture,
) -> None:
    mocker.patch(
        "app.commands.sync_subscriptions.sync_account",
        return_value=[
            SyncResult(
                account_id=subscription_account.id,
                subscription_id=SUBSCRIPTION_ID,
                message="Created new entitlement ENT-1234-5678.",
            )
        ],
    )
    mocked_send_info = mocker.patch("app.commands.sync_subscriptions.send_info")

    with caplog.at_level("INFO"):
        await main(test_settings, 50, 5, 24, dry_run=True)

    assert mocked_send_info.await_count == 0
    assert "1 subscription(s) to change, 0 failed:" in caplog.text
    assert (
        f"{subscription_account.id}  {SUBSCRIPTION_ID}  Created new entitlement ENT-1234-5678."
        in caplog.text
    )


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        (None, DEFAULT_STATUS_LIST),
        (ACTIVE_SUBSCRIPTION_STATUS, [ACTIVE_SUBSCRIPTION_STATUS]),
        (TERMINATED_SUBSCRIPTION_STATUS, [TERMINATED_SUBSCRIPTION_STATUS]),
    ],
)
async def test_main_status_argument(
    mocker: MockerFixture,
    test_settings: Settings,
    subscription_account: Account,
    status: str | None,
    expected: list[str],
) -> None:
    mocked_sync_account = mocker.patch(
        "app.commands.sync_subscriptions.sync_account", return_value=[]
    )
    mocker.patch("app.commands.sync_subscriptions.send_info")

    await main(test_settings, 50, 5, 24, status=status)

    assert mocked_sync_account.await_args is not None
    assert mocked_sync_account.await_args.args[1] == expected
