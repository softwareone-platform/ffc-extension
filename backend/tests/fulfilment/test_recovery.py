from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from app.fulfilment.error import ERR_DUE_DATE_IS_REACHED
from app.fulfilment.recovery import handle_exception
from app.schemas.core import EventResponse

FIXED_NOW = datetime(2026, 6, 8, tzinfo=UTC)
ORDER_ID = "ORD-1111-2222-3333"
TASK_ID = "TSK-1111-2222-3333"


def _set_due_date(order: dict, value: str | None) -> dict:
    for param in order["parameters"]["fulfillment"]:
        if param["externalId"] == "dueDate":
            param["value"] = value
    return order


@pytest.fixture
def freeze_now(mocker):
    mocked = mocker.patch("app.fulfilment.recovery.datetime")
    mocked.now.return_value = FIXED_NOW
    return mocked


async def test_no_due_date_fails_order_and_cancels(order_factory):
    order = _set_due_date(
        order_factory(
            order_type="Purchase",
            status="Processing",
            product_id="PRD-4141-4379",
            product_name="SoftwareOne FinOps for Cloud",
        ),
        None,
    )
    ext_client = AsyncMock()

    response = await handle_exception(RuntimeError("boom"), ext_client, order, ORDER_ID, TASK_ID)

    assert response == EventResponse.cancel()
    ext_client.fail_order.assert_awaited_once_with(
        order_id=ORDER_ID, payload={"description": "due date is not set"}
    )
    ext_client.get_task.assert_not_awaited()
    ext_client.reschedule_task.assert_not_awaited()


async def test_missing_order_treated_as_no_due_date(order_factory):
    ext_client = AsyncMock()

    response = await handle_exception(RuntimeError("boom"), ext_client, None, ORDER_ID, TASK_ID)

    assert response == EventResponse.cancel()
    ext_client.fail_order.assert_awaited_once_with(
        order_id=ORDER_ID, payload={"description": "due date is not set"}
    )


async def test_no_due_date_cancels_even_if_fail_order_raises(order_factory):
    order = _set_due_date(
        order_factory(
            order_type="Purchase",
            status="Processing",
            product_id="PRD-4141-4379",
            product_name="SoftwareOne FinOps for Cloud",
        ),
        None,
    )
    ext_client = AsyncMock()
    ext_client.fail_order.side_effect = Exception("MPT down")

    response = await handle_exception(RuntimeError("boom"), ext_client, order, ORDER_ID, TASK_ID)

    assert response == EventResponse.cancel()
    ext_client.fail_order.assert_awaited_once()


async def test_due_date_in_future_reschedules(order_factory, freeze_now):
    order = _set_due_date(
        order_factory(
            order_type="Purchase",
            status="Processing",
            product_id="PRD-4141-4379",
            product_name="SoftwareOne FinOps for Cloud",
        ),
        "2026-12-31",
    )
    ext_client = AsyncMock()
    ext_client.get_task.return_value = {"description": "previous note"}

    response = await handle_exception(RuntimeError("boom"), ext_client, order, ORDER_ID, TASK_ID)

    assert response == EventResponse.reschedule(seconds=300)
    ext_client.get_task.assert_awaited_once_with(TASK_ID)
    ext_client.reschedule_task.assert_awaited_once_with(
        TASK_ID,
        payload={"description": "previous note - 2026-06-08 - boom"},
    )
    ext_client.fail_order.assert_not_awaited()
    ext_client.complete_task.assert_not_awaited()


@pytest.mark.parametrize("due_date", ["2026-01-01", "2026-06-08"])  # past and == now
async def test_due_date_reached_fails_order_and_completes_task(order_factory, freeze_now, due_date):
    order = _set_due_date(
        order_factory(
            order_type="Purchase",
            status="Processing",
            product_id="PRD-4141-4379",
            product_name="SoftwareOne FinOps for Cloud",
        ),
        due_date,
    )
    ext_client = AsyncMock()
    ext_client.get_task.return_value = {"description": "previous note"}

    response = await handle_exception(RuntimeError("boom"), ext_client, order, ORDER_ID, TASK_ID)

    assert response == EventResponse.ok()
    ext_client.fail_order.assert_awaited_once_with(
        order_id=ORDER_ID,
        payload=ERR_DUE_DATE_IS_REACHED.to_dict(due_date=due_date),
    )
    ext_client.complete_task.assert_awaited_once_with(
        TASK_ID,
        payload={"description": "previous note - 2026-06-08 - boom"},
    )
    ext_client.reschedule_task.assert_not_awaited()


async def test_due_date_reached_cancels_when_fail_order_raises(order_factory, freeze_now, caplog):
    # Due date reached but failing/completing the order errors out: the error
    # must be logged and swallowed, returning Cancel.
    order = _set_due_date(
        order_factory(
            order_type="Purchase",
            status="Processing",
            product_id="PRD-4141-4379",
            product_name="SoftwareOne FinOps for Cloud",
        ),
        "2026-01-01",
    )
    ext_client = AsyncMock()
    ext_client.get_task.return_value = {"description": "previous note"}
    ext_client.fail_order.side_effect = Exception("MPT down")

    response = await handle_exception(RuntimeError("boom"), ext_client, order, ORDER_ID, TASK_ID)

    assert response == EventResponse.cancel()
    ext_client.fail_order.assert_awaited_once()
    ext_client.complete_task.assert_not_awaited()
    assert "Failed to fail/complete" in caplog.text


async def test_get_task_missing_description_defaults_to_empty(order_factory, freeze_now):
    order = _set_due_date(
        order_factory(
            order_type="Purchase",
            status="Processing",
            product_id="PRD-4141-4379",
            product_name="SoftwareOne FinOps for Cloud",
        ),
        "2026-12-31",
    )
    ext_client = AsyncMock()
    ext_client.get_task.return_value = {}

    response = await handle_exception(RuntimeError("boom"), ext_client, order, ORDER_ID, TASK_ID)

    assert response == EventResponse.reschedule(seconds=300)
    ext_client.reschedule_task.assert_awaited_once_with(
        TASK_ID,
        payload={"description": " - 2026-06-08 - boom"},
    )
