from collections.abc import Awaitable, Callable

import pytest
from fastapi.exceptions import ResponseValidationError
from httpx import Response
from pytest_mock import MockerFixture
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api_clients.mpt import MPTClient
from app.db.models import Account, Entitlement
from app.enums import EntitlementStatus
from app.events.orders.processing import PurchaseOrderProcessor
from app.events.processing import ProcessingResult, ProcessingStatus
from app.schemas.core import Event, ExtensionContext
from tests.types import EventFactory, MPTSubscriptionFactory, TemplatesMocker


async def test_process_order_completes(
    mocker: MockerFixture,
    mocked_extension_ctx: ExtensionContext,
    event_factory: EventFactory,
    post_order_event: Callable[[Event], Awaitable[Response]],
    purchase_order: dict,
    mock_owned_task: TemplatesMocker,
) -> None:
    """A COMPLETE result logs the task, completes it, and returns an OK response."""
    mocker.patch.object(ExtensionContext, "from_identity_file", return_value=mocked_extension_ctx)
    event = event_factory(object_id=purchase_order["id"])
    mock_owned_task()
    mocked_start_task = mocker.patch.object(MPTClient, "start_task")
    mocked_get_order = mocker.patch.object(MPTClient, "get_order", return_value=purchase_order)
    mocked_process = mocker.patch.object(
        PurchaseOrderProcessor,
        "process",
        return_value=ProcessingResult(status=ProcessingStatus.COMPLETE),
    )
    mocked_log_task = mocker.patch.object(MPTClient, "log_task")
    mocked_complete_task = mocker.patch.object(MPTClient, "complete_task")

    response = await post_order_event(event)

    assert response.status_code == 200
    assert response.json()["response"] == "OK"
    mocked_start_task.assert_awaited_once()
    mocked_get_order.assert_awaited_once()
    mocked_process.assert_awaited_once()
    mocked_log_task.assert_awaited_once_with(event.task.id, severity=None, error_message=None)
    mocked_complete_task.assert_awaited_once_with(event.task.id)


async def test_process_order_reschedule(
    mocker: MockerFixture,
    mocked_extension_ctx: ExtensionContext,
    event_factory: EventFactory,
    post_order_event: Callable[[Event], Awaitable[Response]],
    purchase_order: dict,
    mock_owned_task: TemplatesMocker,
) -> None:
    """A RESCHEDULE result logs a warning, reschedules the task, and returns a Delay response."""
    mocker.patch.object(ExtensionContext, "from_identity_file", return_value=mocked_extension_ctx)
    event = event_factory(object_id=purchase_order["id"])
    mock_owned_task()
    mocker.patch.object(MPTClient, "start_task")
    mocker.patch.object(MPTClient, "get_order", return_value=purchase_order)
    mocker.patch.object(
        PurchaseOrderProcessor,
        "process",
        return_value=ProcessingResult(
            status=ProcessingStatus.RESCHEDULE, severity="Warning", message="boom"
        ),
    )
    mocked_log_task = mocker.patch.object(MPTClient, "log_task")
    mocked_reschedule_task = mocker.patch.object(MPTClient, "reschedule_task")
    mocked_complete_task = mocker.patch.object(MPTClient, "complete_task")

    response = await post_order_event(event)

    assert response.status_code == 200
    body = response.json()
    assert body["response"] == "Delay"
    assert body["delay"] == 300
    mocked_log_task.assert_awaited_once_with(
        event.task.id, severity="Warning", error_message="boom"
    )
    mocked_reschedule_task.assert_awaited_once_with(event.task.id)
    mocked_complete_task.assert_not_awaited()


async def test_process_order_cancel(
    mocker: MockerFixture,
    mocked_extension_ctx: ExtensionContext,
    event_factory: EventFactory,
    post_order_event: Callable[[Event], Awaitable[Response]],
    purchase_order: dict,
    mock_owned_task: TemplatesMocker,
) -> None:
    """A CANCEL result logs an error, leaves the task open, and returns a Cancel response."""
    mocker.patch.object(ExtensionContext, "from_identity_file", return_value=mocked_extension_ctx)
    event = event_factory(object_id=purchase_order["id"])
    mock_owned_task()
    mocker.patch.object(MPTClient, "start_task")
    mocker.patch.object(MPTClient, "get_order", return_value=purchase_order)
    mocker.patch.object(
        PurchaseOrderProcessor,
        "process",
        return_value=ProcessingResult(
            status=ProcessingStatus.CANCEL, severity="Error", message="boom"
        ),
    )
    mocked_log_task = mocker.patch.object(MPTClient, "log_task")
    mocked_complete_task = mocker.patch.object(MPTClient, "complete_task")

    response = await post_order_event(event)

    assert response.status_code == 200
    assert response.json()["response"] == "Cancel"
    mocked_log_task.assert_awaited_once_with(event.task.id, severity="Error", error_message="boom")
    mocked_complete_task.assert_not_awaited()


async def test_process_order_skip(
    mocker: MockerFixture,
    mocked_extension_ctx: ExtensionContext,
    event_factory: EventFactory,
    post_order_event: Callable[[Event], Awaitable[Response]],
    purchase_order: dict,
    mock_owned_task: TemplatesMocker,
) -> None:
    """A SKIP result logs an info message, leaves the task open, and returns an OK response."""
    mocker.patch.object(ExtensionContext, "from_identity_file", return_value=mocked_extension_ctx)
    event = event_factory(object_id=purchase_order["id"])
    mock_owned_task()
    mocker.patch.object(MPTClient, "start_task")
    mocker.patch.object(MPTClient, "get_order", return_value=purchase_order)
    mocker.patch.object(
        PurchaseOrderProcessor,
        "process",
        return_value=ProcessingResult(
            status=ProcessingStatus.SKIP, severity="Info", message="moved to querying"
        ),
    )
    mocked_log_task = mocker.patch.object(MPTClient, "log_task")
    mocked_complete_task = mocker.patch.object(MPTClient, "complete_task")

    response = await post_order_event(event)

    assert response.status_code == 200
    assert response.json()["response"] == "OK"
    mocked_log_task.assert_awaited_once_with(
        event.task.id, severity="Info", error_message="moved to querying"
    )
    mocked_complete_task.assert_not_awaited()


async def test_process_order_ignores_task_owned_by_another_account(
    mocker: MockerFixture,
    mocked_extension_ctx: ExtensionContext,
    event_factory: EventFactory,
    post_order_event: Callable[[Event], Awaitable[Response]],
    purchase_order: dict,
    mock_owned_task: TemplatesMocker,
) -> None:
    """A task owned by another account is logged and closed without processing the order."""
    mocker.patch.object(ExtensionContext, "from_identity_file", return_value=mocked_extension_ctx)
    event = event_factory(object_id=purchase_order["id"])
    mock_owned_task(account_id="ACC-9999-9999")
    mocked_start_task = mocker.patch.object(MPTClient, "start_task")
    mocked_process = mocker.patch.object(PurchaseOrderProcessor, "process")
    mocked_log_task = mocker.patch.object(MPTClient, "log_task")
    mocked_complete_task = mocker.patch.object(MPTClient, "complete_task")

    response = await post_order_event(event)

    assert response.status_code == 200
    assert response.json()["response"] == "OK"
    mocked_process.assert_not_awaited()
    mocked_start_task.assert_awaited_once_with(event.task.id, mocked_extension_ctx.instance_id)
    mocked_complete_task.assert_awaited_once_with(event.task.id)
    assert mocked_log_task.await_args.kwargs["severity"] == "Info"
    assert "is not the fulfillment owner" in mocked_log_task.await_args.kwargs["error_message"]


async def test_process_order_cancels_unsupported_order_type(
    mocker: MockerFixture,
    mocked_extension_ctx: ExtensionContext,
    event_factory: EventFactory,
    post_order_event: Callable[[Event], Awaitable[Response]],
    purchase_order: dict,
    mock_owned_task: TemplatesMocker,
) -> None:
    """An order type with no processor is logged as a warning and the task is cancelled."""
    mocker.patch.object(ExtensionContext, "from_identity_file", return_value=mocked_extension_ctx)
    event = event_factory(object_id=purchase_order["id"])
    mock_owned_task()
    mocker.patch.object(MPTClient, "start_task")
    mocker.patch.object(
        MPTClient, "get_order", return_value={**purchase_order, "type": "Configuration"}
    )
    mocked_log_task = mocker.patch.object(MPTClient, "log_task")
    mocked_complete_task = mocker.patch.object(MPTClient, "complete_task")
    mocked_reschedule_task = mocker.patch.object(MPTClient, "reschedule_task")

    response = await post_order_event(event)

    assert response.status_code == 200
    assert response.json()["response"] == "Cancel"
    assert mocked_log_task.await_args.kwargs["severity"] == "Warning"
    assert "Configuration" in mocked_log_task.await_args.kwargs["error_message"]
    mocked_complete_task.assert_not_awaited()
    mocked_reschedule_task.assert_not_awaited()


async def test_process_order_raises_on_unhandled_status(
    mocker: MockerFixture,
    mocked_extension_ctx: ExtensionContext,
    event_factory: EventFactory,
    post_order_event: Callable[[Event], Awaitable[Response]],
    purchase_order: dict,
    mock_owned_task: TemplatesMocker,
) -> None:
    """A status the router does not handle returns nothing and fails response validation."""
    # The router deliberately has no `case _`, so an unmatched status falls out of the `match`
    # and the handler returns `None`. Add a `case` arm here if a new `ProcessingStatus` lands.
    mocker.patch.object(ExtensionContext, "from_identity_file", return_value=mocked_extension_ctx)
    event = event_factory(object_id=purchase_order["id"])
    mock_owned_task()
    mocker.patch.object(MPTClient, "start_task")
    mocker.patch.object(MPTClient, "get_order", return_value=purchase_order)
    mocker.patch.object(
        PurchaseOrderProcessor,
        "process",
        return_value=ProcessingResult(status="Bogus"),  # ty: ignore[invalid-argument-type]
    )
    mocked_log_task = mocker.patch.object(MPTClient, "log_task")
    mocked_complete_task = mocker.patch.object(MPTClient, "complete_task")
    mocked_reschedule_task = mocker.patch.object(MPTClient, "reschedule_task")

    with pytest.raises(ResponseValidationError, match="valid dictionary or object"):
        await post_order_event(event)

    mocked_log_task.assert_not_awaited()
    mocked_complete_task.assert_not_awaited()
    mocked_reschedule_task.assert_not_awaited()


async def test_process_subscription_creates_the_entitlement_and_completes_the_task(
    mocker: MockerFixture,
    mocked_extension_ctx: ExtensionContext,
    event_factory: EventFactory,
    post_subscription_event: Callable[[Event], Awaitable[Response]],
    mpt_subscription_factory: MPTSubscriptionFactory,
    subscription_account: Account,
    db_session: AsyncSession,
) -> None:
    """An affiliate subscription event issues the entitlement and closes its task."""
    mocker.patch.object(ExtensionContext, "from_identity_file", return_value=mocked_extension_ctx)
    subscription = mpt_subscription_factory()
    event = event_factory(
        object_id=subscription["id"], object_name="subscription", object_type="Subscription"
    )
    mocked_start_task = mocker.patch.object(MPTClient, "start_task")
    mocked_get_subscription = mocker.patch.object(
        MPTClient, "get_subscription", return_value=subscription
    )
    mocked_log_task = mocker.patch.object(MPTClient, "log_task")
    mocked_complete_task = mocker.patch.object(MPTClient, "complete_task")

    response = await post_subscription_event(event)

    assert response.status_code == 200
    assert response.json()["response"] == "OK"
    result = await db_session.execute(
        select(Entitlement).where(Entitlement.owner == subscription_account)
    )
    entitlement = result.scalars().one()
    assert entitlement.status is EntitlementStatus.NEW
    assert entitlement.affiliate_external_id == subscription["id"]
    assert entitlement.datasource_id == subscription["externalIds"]["vendor"]
    mocked_start_task.assert_awaited_once_with(event.task.id, mocked_extension_ctx.instance_id)
    mocked_get_subscription.assert_awaited_once_with(subscription["id"])
    mocked_log_task.assert_awaited_once_with(
        event.task.id,
        severity="Info",
        error_message=f"The entitlement {entitlement.id} was created.",
    )
    mocked_complete_task.assert_awaited_once_with(event.task.id)


async def test_process_subscription_completes_the_task_for_an_unknown_subscription(
    mocker: MockerFixture,
    mocked_extension_ctx: ExtensionContext,
    event_factory: EventFactory,
    post_subscription_event: Callable[[Event], Awaitable[Response]],
    subscription_account: Account,
    db_session: AsyncSession,
) -> None:
    """A subscription the marketplace does not know is logged as an error and closed."""
    mocker.patch.object(ExtensionContext, "from_identity_file", return_value=mocked_extension_ctx)
    event = event_factory(
        object_id="SUB-0000-0000", object_name="subscription", object_type="Subscription"
    )
    mocker.patch.object(MPTClient, "start_task")
    mocker.patch.object(MPTClient, "get_subscription", return_value={})
    mocked_log_task = mocker.patch.object(MPTClient, "log_task")
    mocked_complete_task = mocker.patch.object(MPTClient, "complete_task")

    response = await post_subscription_event(event)

    assert response.status_code == 200
    assert response.json()["response"] == "OK"
    mocked_log_task.assert_awaited_once_with(
        event.task.id,
        severity="Error",
        error_message="No subscription found for SUB-0000-0000.",
    )
    mocked_complete_task.assert_awaited_once_with(event.task.id)
    result = await db_session.execute(
        select(Entitlement).where(Entitlement.owner == subscription_account)
    )
    assert result.scalars().all() == []
