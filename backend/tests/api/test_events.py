from datetime import UTC, datetime

from httpx import AsyncClient

from app.api_clients.mpt import MPTClient
from app.fulfilment.constants import ExceptionSeverity, ProcessResult
from app.fulfilment.processing import PurchaseOrderProcessor
from app.schemas.core import Details, Event, Object, Task

TASK_ID = "TSK-0014-5578-6577-4688"


def _make_event(order_id: str) -> Event:
    return Event(
        id="01ef68d7-3792-48cc-96cc-924599f6d490",
        object=Object(id=order_id, name="order", objectType="Order"),
        details=Details(
            eventType="status_changed",
            enqueueTime=datetime(2026, 6, 10, 14, 50, 30, 609000, tzinfo=UTC),
            deliveryTime=datetime(2026, 6, 10, 14, 51, 12, 681000, tzinfo=UTC),
        ),
        task=Task(id=TASK_ID),
    )


async def _post_event(client: AsyncClient, token: str, event: Event):
    return await client.post(
        "/events/commerce/orders",
        headers={"Authorization": f"Bearer {token}"},
        json=event.model_dump(mode="json", by_alias=True),
    )


async def test_process_order_completes(
    mocker,
    mpt_api_client: AsyncClient,
    ffc_jwt_token: str,
    order_factory,
):
    # Happy path: the processor runs and the task is completed with an OK response.
    order = order_factory(
        order_type="Purchase",
        status="Processing",
        product_id="PRD-4141-4379",
        product_name="SoftwareOne FinOps for Cloud",
    )
    mocked_start_task = mocker.patch.object(MPTClient, "start_task")
    mocked_get_order = mocker.patch.object(MPTClient, "get_order", return_value=order)
    mocked_process = mocker.patch.object(PurchaseOrderProcessor, "process", return_value=order)
    mocked_complete_task = mocker.patch.object(MPTClient, "complete_task")
    mocked_handle_exception = mocker.patch.object(PurchaseOrderProcessor, "handle_exception")

    response = await _post_event(mpt_api_client, ffc_jwt_token, _make_event(order["id"]))

    assert response.status_code == 200
    assert response.json()["response"] == "OK"

    mocked_start_task.assert_awaited_once()
    mocked_get_order.assert_awaited_once()
    mocked_process.assert_awaited_once()
    mocked_complete_task.assert_awaited_once_with(TASK_ID)
    mocked_handle_exception.assert_not_awaited()


async def test_process_order_reschedule(
    mocker,
    mpt_api_client: AsyncClient,
    ffc_jwt_token: str,
    order_factory,
):
    # process() raises and recovery asks for a reschedule: the task is logged as a
    # warning, rescheduled, and the response is a Delay.
    order = order_factory(
        order_type="Purchase",
        status="Processing",
        product_id="PRD-4141-4379",
        product_name="SoftwareOne FinOps for Cloud",
    )
    mocker.patch.object(MPTClient, "start_task")
    mocker.patch.object(MPTClient, "get_order", return_value=order)
    mocker.patch.object(PurchaseOrderProcessor, "process", side_effect=RuntimeError("boom"))
    mocked_handle_exception = mocker.patch.object(
        PurchaseOrderProcessor, "handle_exception", return_value=ProcessResult.RESCHEDULE
    )
    mocked_log_task = mocker.patch.object(MPTClient, "log_task")
    mocked_reschedule_task = mocker.patch.object(MPTClient, "reschedule_task")
    mocked_complete_task = mocker.patch.object(MPTClient, "complete_task")

    response = await _post_event(mpt_api_client, ffc_jwt_token, _make_event(order["id"]))

    assert response.status_code == 200
    body = response.json()
    assert body["response"] == "Delay"
    assert body["delay"] == 300

    mocked_handle_exception.assert_awaited_once()
    mocked_log_task.assert_awaited_once_with(
        TASK_ID, severity=ExceptionSeverity.WARNING, error_message="boom"
    )
    mocked_reschedule_task.assert_awaited_once_with(TASK_ID)
    mocked_complete_task.assert_not_awaited()


async def test_process_order_complete_on_exception(
    mocker,
    mpt_api_client: AsyncClient,
    ffc_jwt_token: str,
    order_factory,
):
    # process() raises and recovery decides the order is definitively failed: the task
    # is logged as an error, completed, and the response is OK.
    order = order_factory(
        order_type="Purchase",
        status="Processing",
        product_id="PRD-4141-4379",
        product_name="SoftwareOne FinOps for Cloud",
    )
    mocker.patch.object(MPTClient, "start_task")
    mocker.patch.object(MPTClient, "get_order", return_value=order)
    mocker.patch.object(PurchaseOrderProcessor, "process", side_effect=RuntimeError("boom"))
    mocker.patch.object(
        PurchaseOrderProcessor, "handle_exception", return_value=ProcessResult.COMPLETE
    )
    mocked_log_task = mocker.patch.object(MPTClient, "log_task")
    mocked_complete_task = mocker.patch.object(MPTClient, "complete_task")

    response = await _post_event(mpt_api_client, ffc_jwt_token, _make_event(order["id"]))

    assert response.status_code == 200
    assert response.json()["response"] == "OK"

    mocked_log_task.assert_awaited_once_with(
        TASK_ID, severity=ExceptionSeverity.ERROR, error_message="boom"
    )
    mocked_complete_task.assert_awaited_once_with(TASK_ID)


async def test_process_order_cancel(
    mocker,
    mpt_api_client: AsyncClient,
    ffc_jwt_token: str,
    order_factory,
):
    # process() raises and recovery cancels: the task is logged as an error, the task is
    # NOT completed, and the response is Cancel.
    order = order_factory(
        order_type="Purchase",
        status="Processing",
        product_id="PRD-4141-4379",
        product_name="SoftwareOne FinOps for Cloud",
    )
    mocker.patch.object(MPTClient, "start_task")
    mocker.patch.object(MPTClient, "get_order", return_value=order)
    mocker.patch.object(PurchaseOrderProcessor, "process", side_effect=RuntimeError("boom"))
    mocker.patch.object(
        PurchaseOrderProcessor, "handle_exception", return_value=ProcessResult.CANCEL
    )
    mocked_log_task = mocker.patch.object(MPTClient, "log_task")
    mocked_complete_task = mocker.patch.object(MPTClient, "complete_task")

    response = await _post_event(mpt_api_client, ffc_jwt_token, _make_event(order["id"]))

    assert response.status_code == 200
    assert response.json()["response"] == "Cancel"

    mocked_log_task.assert_awaited_once_with(
        TASK_ID, severity=ExceptionSeverity.ERROR, error_message="boom"
    )
    mocked_complete_task.assert_not_awaited()


async def test_process_order_skip(
    mocker,
    mpt_api_client: AsyncClient,
    ffc_jwt_token: str,
    order_factory,
):
    # process() raises an already-handled flow error: the task is logged as info,
    # completed, and the response is OK.
    order = order_factory(
        order_type="Purchase",
        status="Processing",
        product_id="PRD-4141-4379",
        product_name="SoftwareOne FinOps for Cloud",
    )
    mocker.patch.object(MPTClient, "start_task")
    mocker.patch.object(MPTClient, "get_order", return_value=order)
    mocker.patch.object(PurchaseOrderProcessor, "process", side_effect=RuntimeError("boom"))
    mocker.patch.object(PurchaseOrderProcessor, "handle_exception", return_value=ProcessResult.SKIP)
    mocked_log_task = mocker.patch.object(MPTClient, "log_task")
    mocked_complete_task = mocker.patch.object(MPTClient, "complete_task")

    response = await _post_event(mpt_api_client, ffc_jwt_token, _make_event(order["id"]))

    assert response.status_code == 200
    assert response.json()["response"] == "OK"

    mocked_log_task.assert_awaited_once_with(
        TASK_ID, severity=ExceptionSeverity.INFO, error_message="boom"
    )
    mocked_complete_task.assert_awaited_once_with(TASK_ID)
