from collections.abc import Awaitable, Callable

from httpx import Response
from pytest_mock import MockerFixture

from app.api_clients.mpt import MPTClient
from app.fulfilment.processing import ProcessingResult, ProcessingStatus, PurchaseOrderProcessor
from app.schemas.core import Event, ExtensionContext


async def test_process_order_completes(
    mocker: MockerFixture,
    mocked_extension_ctx: ExtensionContext,
    event_factory: Callable[..., Event],
    post_order_event: Callable[[Event], Awaitable[Response]],
    purchase_order: dict,
) -> None:
    """A COMPLETE result logs the task, completes it, and returns an OK response."""
    mocker.patch.object(ExtensionContext, "from_identity_file", return_value=mocked_extension_ctx)
    event = event_factory(order_id=purchase_order["id"])
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
    event_factory: Callable[..., Event],
    post_order_event: Callable[[Event], Awaitable[Response]],
    purchase_order: dict,
) -> None:
    """A RESCHEDULE result logs a warning, reschedules the task, and returns a Delay response."""
    mocker.patch.object(ExtensionContext, "from_identity_file", return_value=mocked_extension_ctx)
    event = event_factory(order_id=purchase_order["id"])
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
    event_factory: Callable[..., Event],
    post_order_event: Callable[[Event], Awaitable[Response]],
    purchase_order: dict,
) -> None:
    """A CANCEL result logs an error, leaves the task open, and returns a Cancel response."""
    mocker.patch.object(ExtensionContext, "from_identity_file", return_value=mocked_extension_ctx)
    event = event_factory(order_id=purchase_order["id"])
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
    event_factory: Callable[..., Event],
    post_order_event: Callable[[Event], Awaitable[Response]],
    purchase_order: dict,
) -> None:
    """A SKIP result logs an info message, leaves the task open, and returns an OK response."""
    mocker.patch.object(ExtensionContext, "from_identity_file", return_value=mocked_extension_ctx)
    event = event_factory(order_id=purchase_order["id"])
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
