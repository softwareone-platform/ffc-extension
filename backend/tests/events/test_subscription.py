import logging
from typing import Any

import httpx
import pytest
from pytest_httpx import HTTPXMock
from pytest_mock import MockerFixture
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.conf import Settings
from app.db.handlers import EntitlementHandler
from app.db.models import Account, Entitlement
from app.enums import AccountType, EntitlementStatus
from app.events.processing import ProcessingStatus
from app.events.subscriptions.constants import (
    ACTIVE_SUBSCRIPTION_STATUS,
    TERMINATED_SUBSCRIPTION_STATUS,
)
from app.events.subscriptions.exceptions import SubscriptionNotFoundError
from app.events.subscriptions.processing import SubscriptionEventHandler, SubscriptionProcessor
from app.schemas.core import ExtensionContext
from tests.types import ModelFactory, MPTSubscriptionFactory, SubscriptionMocker

SUBSCRIPTION_ID = "SUB-1234-5678"
DATASOURCE_ID = "ds0001234"
TASK_ID = "TSK-0014-5578-6577-4688"


@pytest.fixture
def mock_get_subscription(httpx_mock: HTTPXMock, test_settings: Settings) -> SubscriptionMocker:
    """Make the marketplace answer `get_subscription` with the given payload."""

    def _mock(subscription: dict[str, Any], subscription_id: str = SUBSCRIPTION_ID) -> None:
        httpx_mock.add_response(
            method="GET",
            url=f"{test_settings.mpt_api_base_url}/commerce/subscriptions/{subscription_id}",
            json=subscription,
        )

    return _mock


async def get_entitlements(db_session: AsyncSession, owner: Account) -> list[Entitlement]:
    """Every entitlement the account owns, oldest first."""
    result = await db_session.execute(
        select(Entitlement).where(Entitlement.owner == owner).order_by(Entitlement.created_at.asc())
    )
    return list(result.scalars().all())


# -- get_processor --


async def test_get_processor_for_subscription_event(
    subscription_event_handler: SubscriptionEventHandler,
    mpt_subscription_factory: MPTSubscriptionFactory,
    mock_get_subscription: SubscriptionMocker,
    subscription_account: Account,
    db_session: AsyncSession,
) -> None:
    """`get_processor` fetches the subscription and hands it to the processor."""
    subscription = mpt_subscription_factory()
    mock_get_subscription(subscription)

    processor = await subscription_event_handler.get_processor(object_id=SUBSCRIPTION_ID)

    assert isinstance(processor, SubscriptionProcessor)
    assert processor.subscription == subscription
    assert processor.account is subscription_account
    assert processor.object_id == SUBSCRIPTION_ID
    assert processor.entitlement_repo.session is db_session


async def test_get_processor_raises_when_the_marketplace_returns_no_subscription(
    subscription_event_handler: SubscriptionEventHandler,
    mock_get_subscription: SubscriptionMocker,
) -> None:
    """An empty payload is an error that still closes the task."""
    mock_get_subscription({})

    with pytest.raises(SubscriptionNotFoundError) as exc_info:
        await subscription_event_handler.get_processor(object_id=SUBSCRIPTION_ID)

    result = exc_info.value.to_result()
    assert result.status is ProcessingStatus.COMPLETE
    assert result.severity == "Error"
    assert result.message == f"No subscription found for {SUBSCRIPTION_ID}."


async def test_get_processor_propagates_a_marketplace_failure(
    subscription_event_handler: SubscriptionEventHandler,
    httpx_mock: HTTPXMock,
    test_settings: Settings,
) -> None:
    """A marketplace error is not a domain error: the platform retries the event."""
    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.mpt_api_base_url}/commerce/subscriptions/{SUBSCRIPTION_ID}",
        status_code=httpx.codes.NOT_FOUND,
        json={"errors": {"id": "Subscription not found"}},
    )

    with pytest.raises(httpx.HTTPStatusError):
        await subscription_event_handler.get_processor(object_id=SUBSCRIPTION_ID)


# -- claim_task --


async def test_claim_task_starts_the_task_without_an_ownership_check(
    subscription_event_handler: SubscriptionEventHandler,
    httpx_mock: HTTPXMock,
    test_settings: Settings,
    mocked_extension_ctx: ExtensionContext,
) -> None:
    """Subscription events carry no fulfilment ownership: the task is simply started."""
    httpx_mock.add_response(
        method="POST",
        url=f"{test_settings.mpt_api_base_url}/system/tasks/{TASK_ID}/execute",
        json={"id": TASK_ID, "parameters": {"accountId": "ACC-9999-9999"}},
    )
    httpx_mock.add_response(
        method="PUT",
        url=f"{test_settings.mpt_api_base_url}/system/tasks/{TASK_ID}",
        json={"id": TASK_ID},
    )

    claimed = await subscription_event_handler.claim_task(
        mocked_extension_ctx, TASK_ID, SUBSCRIPTION_ID
    )

    assert claimed is True
    assert [request.method for request in httpx_mock.get_requests()] == ["POST", "PUT"]


# -- validate --


async def test_process_completes_for_a_non_affiliate_account(
    mpt_subscription_factory: MPTSubscriptionFactory,
    account_factory: ModelFactory[Account],
    db_session: AsyncSession,
) -> None:
    """An operations account owns no entitlements: log an info and close the task."""
    account = await account_factory(
        type=AccountType.OPERATIONS,
        external_id="ACC-5555-5555",
        products="PRD-1111-1111",
    )
    processor = SubscriptionProcessor(
        entitlement_repo=EntitlementHandler(db_session),
        account=account,
        subscription=mpt_subscription_factory(),
    )

    result = await processor.process()

    assert result.status is ProcessingStatus.COMPLETE
    assert result.severity == "Info"
    assert result.message == f"The account {account.id} is not an affiliate account."
    assert await get_entitlements(db_session, account) == []


async def test_process_completes_fails_for_not_supported_product(
    subscription_event_handler: SubscriptionEventHandler,
    mpt_subscription_factory: MPTSubscriptionFactory,
    mock_get_subscription: SubscriptionMocker,
    subscription_account: Account,
    db_session: AsyncSession,
) -> None:
    """A subscription for another vendor's product is logged as an error and closed."""
    mock_get_subscription(mpt_subscription_factory(product_id="PRD-9999-9999"))
    processor = await subscription_event_handler.get_processor(object_id=SUBSCRIPTION_ID)

    result = await processor.process()

    assert result.status is ProcessingStatus.COMPLETE
    assert result.severity == "Error"
    assert result.message == (
        f"The product PRD-9999-9999 is not enabled for the account {subscription_account.id}."
    )
    assert await get_entitlements(db_session, subscription_account) == []


async def test_validate_accepts_a_product_id_in_any_case(
    subscription_event_handler: SubscriptionEventHandler,
    mpt_subscription_factory: MPTSubscriptionFactory,
    mock_get_subscription: SubscriptionMocker,
) -> None:
    """The product membership check is case-insensitive."""
    mock_get_subscription(mpt_subscription_factory(product_id="prd-1111-1111"))
    processor = await subscription_event_handler.get_processor(object_id=SUBSCRIPTION_ID)

    assert await processor.validate() is None


# -- active subscription --


async def test_active_subscription_creates_an_entitlement_when_none_exists(
    subscription_event_handler: SubscriptionEventHandler,
    mpt_subscription_factory: MPTSubscriptionFactory,
    mock_get_subscription: SubscriptionMocker,
    subscription_account: Account,
    db_session: AsyncSession,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A new entitlement is issued and bound to the subscription's datasource."""
    subscription = mpt_subscription_factory(status=ACTIVE_SUBSCRIPTION_STATUS)
    mock_get_subscription(subscription)
    processor = await subscription_event_handler.get_processor(object_id=SUBSCRIPTION_ID)

    with caplog.at_level(logging.INFO):
        result = await processor.process()

    entitlements = await get_entitlements(db_session, subscription_account)
    assert len(entitlements) == 1
    created = entitlements[0]
    assert created.name == subscription["name"]
    assert created.affiliate_external_id == SUBSCRIPTION_ID
    assert created.datasource_id == DATASOURCE_ID
    assert created.status is EntitlementStatus.NEW
    assert result.status is ProcessingStatus.COMPLETE
    assert result.severity == "Info"
    assert result.message == f"The entitlement {created.id} was created."
    assert f"{SUBSCRIPTION_ID}: The entitlement {created.id} was created." in caplog.text


@pytest.mark.parametrize("status", [EntitlementStatus.NEW, EntitlementStatus.ACTIVE])
async def test_active_subscription_does_nothing_when_a_live_entitlement_exists(
    subscription_event_handler: SubscriptionEventHandler,
    mpt_subscription_factory: MPTSubscriptionFactory,
    mock_get_subscription: SubscriptionMocker,
    entitlement_factory: ModelFactory[Entitlement],
    subscription_account: Account,
    db_session: AsyncSession,
    status: EntitlementStatus,
) -> None:
    """A new or active entitlement already covers the subscription."""
    existing = await entitlement_factory(
        owner=subscription_account, datasource_id=DATASOURCE_ID, status=status
    )
    mock_get_subscription(mpt_subscription_factory(status=ACTIVE_SUBSCRIPTION_STATUS))
    processor = await subscription_event_handler.get_processor(object_id=SUBSCRIPTION_ID)

    result = await processor.process()

    assert result.status is ProcessingStatus.COMPLETE
    assert result.message == f"The entitlement {existing.id} already exists."
    entitlements = await get_entitlements(db_session, subscription_account)
    assert [entitlement.id for entitlement in entitlements] == [existing.id]
    await db_session.refresh(existing)
    assert existing.status is status


@pytest.mark.parametrize("status", [EntitlementStatus.TERMINATED, EntitlementStatus.DELETED])
async def test_active_subscription_create_an_entitlement_if_no_live_exists(
    subscription_event_handler: SubscriptionEventHandler,
    mpt_subscription_factory: MPTSubscriptionFactory,
    mock_get_subscription: SubscriptionMocker,
    entitlement_factory: ModelFactory[Entitlement],
    subscription_account: Account,
    db_session: AsyncSession,
    status: EntitlementStatus,
) -> None:
    """A terminated or deleted entitlement no longer covers the subscription: issue a new one."""
    stale = await entitlement_factory(
        owner=subscription_account, datasource_id=DATASOURCE_ID, status=status
    )
    mock_get_subscription(mpt_subscription_factory(status=ACTIVE_SUBSCRIPTION_STATUS))
    processor = await subscription_event_handler.get_processor(object_id=SUBSCRIPTION_ID)

    result = await processor.process()

    entitlements = await get_entitlements(db_session, subscription_account)
    assert len(entitlements) == 2
    issued = next(item for item in entitlements if item.id != stale.id)
    assert issued.status is EntitlementStatus.NEW
    assert issued.datasource_id == DATASOURCE_ID
    assert result.message == f"The entitlement {issued.id} was created."


# -- terminated subscription --


async def test_terminated_subscription_does_nothing_when_no_entitlement_is_bound(
    subscription_event_handler: SubscriptionEventHandler,
    mpt_subscription_factory: MPTSubscriptionFactory,
    mock_get_subscription: SubscriptionMocker,
    subscription_account: Account,
    db_session: AsyncSession,
) -> None:
    """Nothing was ever issued for this datasource, so there is nothing to terminate."""
    mock_get_subscription(mpt_subscription_factory(status=TERMINATED_SUBSCRIPTION_STATUS))
    processor = await subscription_event_handler.get_processor(object_id=SUBSCRIPTION_ID)

    result = await processor.process()

    assert result.status is ProcessingStatus.COMPLETE
    assert result.message == f"No entitlement is bound to the subscription {SUBSCRIPTION_ID}."
    assert await get_entitlements(db_session, subscription_account) == []


async def test_terminated_subscription_deletes_not_redeemed_entitlement(
    subscription_event_handler: SubscriptionEventHandler,
    mpt_subscription_factory: MPTSubscriptionFactory,
    mock_get_subscription: SubscriptionMocker,
    entitlement_factory: ModelFactory[Entitlement],
    subscription_account: Account,
    db_session: AsyncSession,
) -> None:
    """A NEW entitlement was never redeemed, so it is dropped rather than terminated."""
    unredeemed = await entitlement_factory(
        owner=subscription_account, datasource_id=DATASOURCE_ID, status=EntitlementStatus.NEW
    )
    mock_get_subscription(mpt_subscription_factory(status=TERMINATED_SUBSCRIPTION_STATUS))
    processor = await subscription_event_handler.get_processor(object_id=SUBSCRIPTION_ID)

    result = await processor.process()

    await db_session.refresh(unredeemed)
    assert unredeemed.status is EntitlementStatus.DELETED
    assert unredeemed.deleted_at is not None
    assert unredeemed.terminated_at is None
    assert result.status is ProcessingStatus.COMPLETE
    assert result.message == f"The entitlement {unredeemed.id} was deleted."


async def test_terminated_subscription_terminates_an_active_entitlement(
    subscription_event_handler: SubscriptionEventHandler,
    mpt_subscription_factory: MPTSubscriptionFactory,
    mock_get_subscription: SubscriptionMocker,
    entitlement_factory: ModelFactory[Entitlement],
    subscription_account: Account,
    db_session: AsyncSession,
) -> None:
    """An ACTIVE entitlement is in use, so it is terminated."""
    redeemed = await entitlement_factory(
        owner=subscription_account, datasource_id=DATASOURCE_ID, status=EntitlementStatus.ACTIVE
    )
    mock_get_subscription(mpt_subscription_factory(status=TERMINATED_SUBSCRIPTION_STATUS))
    processor = await subscription_event_handler.get_processor(object_id=SUBSCRIPTION_ID)

    result = await processor.process()

    await db_session.refresh(redeemed)
    assert redeemed.status is EntitlementStatus.TERMINATED
    assert redeemed.terminated_at is not None
    assert result.status is ProcessingStatus.COMPLETE
    assert result.message == f"The entitlement {redeemed.id} was terminated."


@pytest.mark.parametrize("status", [EntitlementStatus.TERMINATED, EntitlementStatus.DELETED])
async def test_terminated_subscription_does_nothing_when_with_stale_entitlement(
    subscription_event_handler: SubscriptionEventHandler,
    mpt_subscription_factory: MPTSubscriptionFactory,
    mock_get_subscription: SubscriptionMocker,
    entitlement_factory: ModelFactory[Entitlement],
    subscription_account: Account,
    db_session: AsyncSession,
    status: EntitlementStatus,
) -> None:
    """A row that is no longer live does not cover the subscription and is left alone."""
    existing = await entitlement_factory(
        owner=subscription_account, datasource_id=DATASOURCE_ID, status=status
    )
    mock_get_subscription(mpt_subscription_factory(status=TERMINATED_SUBSCRIPTION_STATUS))
    processor = await subscription_event_handler.get_processor(object_id=SUBSCRIPTION_ID)

    result = await processor.process()

    await db_session.refresh(existing)
    assert existing.status is status
    assert existing.terminated_at is None
    assert result.status is ProcessingStatus.COMPLETE
    assert result.message == f"No entitlement is bound to the subscription {SUBSCRIPTION_ID}."


# -- everything else --


async def test_unhandled_subscription_status_completes_with_a_warning(
    subscription_event_handler: SubscriptionEventHandler,
    mpt_subscription_factory: MPTSubscriptionFactory,
    mock_get_subscription: SubscriptionMocker,
    subscription_account: Account,
    db_session: AsyncSession,
) -> None:
    """A status the flow does not cover closes the task instead of leaving it open."""
    mock_get_subscription(mpt_subscription_factory(status="Draft"))
    processor = await subscription_event_handler.get_processor(object_id=SUBSCRIPTION_ID)

    result = await processor.process()

    assert result.status is ProcessingStatus.COMPLETE
    assert result.severity == "Warning"
    assert result.message == "The subscription status Draft is not handled."
    assert await get_entitlements(db_session, subscription_account) == []


async def test_process_reschedules_on_an_unexpected_failure(
    subscription_event_handler: SubscriptionEventHandler,
    mpt_subscription_factory: MPTSubscriptionFactory,
    mock_get_subscription: SubscriptionMocker,
    mocker: MockerFixture,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """An unexpected error retries the event and reports the traceback."""
    mock_get_subscription(mpt_subscription_factory())
    processor = await subscription_event_handler.get_processor(object_id=SUBSCRIPTION_ID)
    mocker.patch.object(processor, "get_entitlement", side_effect=RuntimeError("boom"))

    with caplog.at_level(logging.ERROR):
        result = await processor.process()

    assert result.status is ProcessingStatus.RESCHEDULE
    assert result.severity == "Warning"
    assert result.message is not None
    assert f"processing the subscription {SUBSCRIPTION_ID}" in result.message
    assert "RuntimeError: boom" in result.message
    assert f"{SUBSCRIPTION_ID}: subscription processing failed." in caplog.text


# -- get_entitlement --


@pytest.mark.parametrize(
    "entitlement_status", [EntitlementStatus.TERMINATED, EntitlementStatus.DELETED]
)
async def test_get_entitlement_ignores_entitlements_that_are_not_live(
    subscription_event_handler: SubscriptionEventHandler,
    mpt_subscription_factory: MPTSubscriptionFactory,
    mock_get_subscription: SubscriptionMocker,
    entitlement_factory: ModelFactory[Entitlement],
    subscription_account: Account,
    entitlement_status: EntitlementStatus,
) -> None:
    """Terminated and deleted rows stay in the table but no longer cover the subscription."""
    await entitlement_factory(
        owner=subscription_account, datasource_id=DATASOURCE_ID, status=entitlement_status
    )
    mock_get_subscription(mpt_subscription_factory())
    processor = await subscription_event_handler.get_processor(object_id=SUBSCRIPTION_ID)

    assert await processor.get_entitlement() is None


async def test_get_entitlement_ignores_another_account_entitlement(
    subscription_event_handler: SubscriptionEventHandler,
    mpt_subscription_factory: MPTSubscriptionFactory,
    mock_get_subscription: SubscriptionMocker,
    entitlement_factory: ModelFactory[Entitlement],
    account_factory: ModelFactory[Account],
) -> None:
    """Entitlements are scoped to their owner, even when the datasource id is shared."""
    other_owner = await account_factory(type=AccountType.AFFILIATE, external_id="ACC-4444-4444")
    await entitlement_factory(
        owner=other_owner, datasource_id=DATASOURCE_ID, status=EntitlementStatus.ACTIVE
    )
    mock_get_subscription(mpt_subscription_factory())
    processor = await subscription_event_handler.get_processor(object_id=SUBSCRIPTION_ID)

    assert await processor.get_entitlement() is None
