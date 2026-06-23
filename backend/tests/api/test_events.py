import logging
from datetime import UTC, datetime

from httpx import AsyncClient

from app.api_clients.mpt import MPTClient
from app.fulfilment.processing import PurchaseOrderProcessor
from app.schemas.core import Details, Event, EventResponse, Object, Task


async def test_process_order_status_not_processing(
    mocker,
    mpt_api_client: AsyncClient,
    ffc_jwt_token: str,
    order_factory,
):
    # Order is not in "Processing": process_order completes the task and returns OK
    # without running the fulfilment chain.
    order = order_factory(
        order_type="Purchase",
        status="Completed",
        product_id="PRD-4141-4379",
        product_name="SoftwareOne FinOps for Cloud",
    )

    mocked_start_task_and_get_order = mocker.patch(
        "app.routers.events.start_task_and_get_order",
        return_value=order,
    )
    mocked_complete_task = mocker.patch.object(MPTClient, "complete_task")

    event = Event(
        id="01ef68d7-3792-48cc-96cc-924599f6d490",
        object=Object(id=order["id"], name="order", objectType="Order"),
        details=Details(
            eventType="status_changed",
            enqueueTime=datetime(2026, 6, 10, 14, 50, 30, 609000, tzinfo=UTC),
            deliveryTime=datetime(2026, 6, 10, 14, 51, 12, 681000, tzinfo=UTC),
        ),
        task=Task(id="TSK-0014-5578-6577-4688"),
    )

    response = await mpt_api_client.post(
        "/events/commerce/orders",
        headers={"Authorization": f"Bearer {ffc_jwt_token}"},
        json=event.model_dump(mode="json", by_alias=True),
    )

    assert response.status_code == 200
    assert response.json()["response"] == "OK"

    mocked_start_task_and_get_order.assert_awaited_once()
    mocked_complete_task.assert_awaited_once_with(event.task.id)


async def test_process_order_status_processing(
    mocker,
    mpt_api_client: AsyncClient,
    ffc_jwt_token: str,
    order_factory,
):
    # Order is in "Processing": process_order completes the task and returns OK
    # running the whole fulfilment chain.
    order = order_factory(
        order_type="Purchase",
        status="Processing",
        product_id="PRD-4141-4379",
        product_name="SoftwareOne FinOps for Cloud",
    )
    mocked_start_task = mocker.patch.object(MPTClient, "start_task")
    mocked_get_order = mocker.patch.object(MPTClient, "get_order", return_value=order)
    mocked_run = mocker.patch.object(PurchaseOrderProcessor, "run", return_value=order)
    mocked_complete_task = mocker.patch.object(MPTClient, "complete_task")

    event = Event(
        id="01ef68d7-3792-48cc-96cc-924599f6d490",
        object=Object(id=order["id"], name="order", objectType="Order"),
        details=Details(
            eventType="status_changed",
            enqueueTime=datetime(2026, 6, 10, 14, 50, 30, 609000, tzinfo=UTC),
            deliveryTime=datetime(2026, 6, 10, 14, 51, 12, 681000, tzinfo=UTC),
        ),
        task=Task(id="TSK-0014-5578-6577-4688"),
    )

    response = await mpt_api_client.post(
        "/events/commerce/orders",
        headers={"Authorization": f"Bearer {ffc_jwt_token}"},
        json=event.model_dump(mode="json", by_alias=True),
    )

    assert response.status_code == 200
    assert response.json()["response"] == "OK"

    mocked_start_task.assert_awaited_once()
    mocked_get_order.assert_awaited_once()
    mocked_run.assert_awaited_once()
    mocked_complete_task.assert_awaited_once_with(event.task.id)


async def test_process_order_moved_to_query(
    mocker,
    mpt_api_client: AsyncClient,
    ffc_jwt_token: str,
    order_factory,
):
    # Order is in "Processing" but with errors in the required parameters.
    # process_order completes the task and returns OK
    order = order_factory(
        order_type="Purchase",
        status="Processing",
        product_id="PRD-4141-4379",
        product_name="SoftwareOne FinOps for Cloud",
    )
    order["parameters"]["ordering"][0]["value"] = None

    mocked_start_task_and_get_order = mocker.patch(
        "app.routers.events.start_task_and_get_order",
        return_value=order,
    )
    mocked_apply_fulfillment_defaults = mocker.patch(
        "app.routers.events.apply_fulfillment_defaults",
        return_value=order,
    )
    mocked_validate = mocker.patch(
        "app.routers.events.validate_and_move_to_querying_if_needed", return_value=(order, False)
    )
    mocked_complete_task = mocker.patch.object(MPTClient, "complete_task")

    event = Event(
        id="01ef68d7-3792-48cc-96cc-924599f6d490",
        object=Object(id=order["id"], name="order", objectType="Order"),
        details=Details(
            eventType="status_changed",
            enqueueTime=datetime(2026, 6, 10, 14, 50, 30, 609000, tzinfo=UTC),
            deliveryTime=datetime(2026, 6, 10, 14, 51, 12, 681000, tzinfo=UTC),
        ),
        task=Task(id="TSK-0014-5578-6577-4688"),
    )

    response = await mpt_api_client.post(
        "/events/commerce/orders",
        headers={"Authorization": f"Bearer {ffc_jwt_token}"},
        json=event.model_dump(mode="json", by_alias=True),
    )

    assert response.status_code == 200
    assert response.json()["response"] == "OK"

    mocked_start_task_and_get_order.assert_awaited_once()
    mocked_apply_fulfillment_defaults.assert_awaited_once()
    mocked_validate.assert_awaited_once()
    mocked_complete_task.assert_awaited_once()


async def test_process_order_missing_task_id(
    mpt_api_client: AsyncClient,
    ffc_jwt_token: str,
    order_factory,
    caplog,
):
    order = order_factory(
        order_type="Purchase",
        status="Processing",
        product_id="PRD-4141-4379",
        product_name="SoftwareOne FinOps for Cloud",
    )

    event = Event(
        id="1428965b-5735-498d-8d31-d51a22f4205d",
        object=Object(id=order["id"], name="order", objectType="Order"),
        details=Details(
            eventType="status_changed",
            enqueueTime=datetime(2026, 6, 10, 14, 50, 30, 609000, tzinfo=UTC),
            deliveryTime=datetime(2026, 6, 10, 14, 51, 12, 681000, tzinfo=UTC),
        ),
        task=None,
    )
    with caplog.at_level(logging.ERROR):
        response = await mpt_api_client.post(
            "/events/commerce/orders",
            headers={"Authorization": f"Bearer {ffc_jwt_token}"},
            json=event.model_dump(mode="json", by_alias=True),
        )
    assert response.status_code == 200
    assert response.json()["response"] == "Cancel"
    assert (
        "Received order event 01ef68d7-3792-48cc-96cc-924599f6d490 without task information"
        in caplog.messages
    )


async def test_process_order_exception(
    mocker,
    mpt_api_client: AsyncClient,
    ffc_jwt_token: str,
    order_factory,
):
    order = order_factory(
        order_type="Purchase",
        status="Processing",
        product_id="PRD-4141-4379",
        product_name="SoftwareOne FinOps for Cloud",
    )

    mocker.patch("app.routers.events.start_task_and_get_order", side_effect=KeyError())

    event = Event(
        id="01ef68d7-3792-48cc-96cc-924599f6d490",
        object=Object(id=order["id"], name="order", objectType="Order"),
        details=Details(
            eventType="status_changed",
            enqueueTime=datetime(2026, 6, 10, 14, 50, 30, 609000, tzinfo=UTC),
            deliveryTime=datetime(2026, 6, 10, 14, 51, 12, 681000, tzinfo=UTC),
        ),
        task=Task(id="TSK-0014-5578-6577-4688"),
    )
    mocked_start_task_and_get_order = mocker.patch(
        "app.routers.events.handle_exception",
        return_value=EventResponse.reschedule(seconds=300),
    )
    response = await mpt_api_client.post(
        "/events/commerce/orders",
        headers={"Authorization": f"Bearer {ffc_jwt_token}"},
        json=event.model_dump(mode="json", by_alias=True),
    )

    assert response.status_code == 200
    assert response.json()["response"] == "Delay"

    mocked_start_task_and_get_order.assert_awaited_once()


async def test_process_order_bug(
    mocker,
    mpt_api_client: AsyncClient,
    ffc_jwt_token: str,
    order_factory,
):
    event = Event(
        id="01ef68d7-3792-48cc-96cc-924599f6d490",
        object=Object(id="ORD-8037-9951-5349", name="order", objectType="Order"),
        details=Details(
            eventType="status_changed",
            enqueueTime=datetime(2026, 6, 23, 14, 48, 54, 288000, tzinfo=UTC),
            deliveryTime=datetime(2026, 6, 23, 14, 54, 41, 681000, tzinfo=UTC),
        ),
        task=Task(id="TSK-0014-7929-1583-2941"),
    )
    response = await mpt_api_client.post(
        "/events/commerce/orders",
        headers={"Authorization": f"Bearer {ffc_jwt_token}"},
        json=event.model_dump(mode="json", by_alias=True),
    )

    assert response.status_code == 200
