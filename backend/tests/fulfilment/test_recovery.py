from datetime import date
from unittest.mock import AsyncMock

import pytest

from app.conf import Settings
from app.fulfilment.constants import ORDER_TYPE_TERMINATE, ProcessResult
from app.fulfilment.error import (
    ERR_DUE_DATE_IS_REACHED,
    ERR_DUE_DATE_NOT_SET,
    ERR_ORDER_TYPE_NOT_SUPPORTED,
)
from app.fulfilment.exceptions import (
    OrderMovedToQuery,
    OrderNotValidError,
    UnsupportedOrderTypeError,
)
from app.fulfilment.processing import PurchaseOrderProcessor

FIXED_NOW = date(2026, 6, 8)


def _make_purchase_processor(order: dict, settings) -> PurchaseOrderProcessor:
    return PurchaseOrderProcessor(
        api_modifier_client=AsyncMock(),
        client=AsyncMock(),
        ext_client=AsyncMock(),
        optscale_auth_client=AsyncMock(),
        optscale_client=AsyncMock(),
        organization_repo=AsyncMock(),
        order=order,
        settings=settings,
    )


def _set_due_date(order: dict, value: str | None) -> dict:
    for param in order["parameters"]["fulfillment"]:
        if param["externalId"] == "dueDate":
            param["value"] = value
    return order


# -- unsupported order type --


async def test_unsupported_order_type_fails_order_and_completes(
    order_factory, test_settings: Settings
):
    order = order_factory(
        order_type="Purchase",
        status="Processing",
        product_id="PRD-4141-4379",
        product_name="SoftwareOne FinOps for Cloud",
    )
    processor = _make_purchase_processor(order, test_settings)

    result = await processor.handle_exception(
        UnsupportedOrderTypeError(ORDER_TYPE_TERMINATE), now=FIXED_NOW
    )

    assert result == ProcessResult.COMPLETE
    processor.ext_client.fail_order.assert_awaited_once_with(
        order_id=order["id"],
        payload=ERR_ORDER_TYPE_NOT_SUPPORTED.to_dict(order_type=ORDER_TYPE_TERMINATE),
    )


# -- errors already handled inside the flow --


@pytest.mark.parametrize(
    "exc",
    [OrderMovedToQuery("ORD-1111"), OrderNotValidError("ORD-1111")],
)
async def test_flow_handled_errors_skip_without_failing_order(
    order_factory, test_settings: Settings, exc
):
    order = order_factory(
        order_type="Purchase",
        status="Processing",
        product_id="PRD-4141-4379",
        product_name="SoftwareOne FinOps for Cloud",
    )
    processor = _make_purchase_processor(order, test_settings)

    result = await processor.handle_exception(exc, now=FIXED_NOW)

    assert result == ProcessResult.SKIP
    processor.ext_client.fail_order.assert_not_awaited()


# -- due date recovery --


async def test_no_due_date_fails_order_and_cancels(order_factory, test_settings: Settings):
    order = _set_due_date(
        order_factory(
            order_type="Purchase",
            status="Processing",
            product_id="PRD-4141-4379",
            product_name="SoftwareOne FinOps for Cloud",
        ),
        None,
    )
    processor = _make_purchase_processor(order, test_settings)

    result = await processor.handle_exception(RuntimeError("boom"), now=FIXED_NOW)

    assert result == ProcessResult.CANCEL
    processor.ext_client.fail_order.assert_awaited_once_with(
        order_id=order["id"],
        payload=ERR_DUE_DATE_NOT_SET.to_dict(),
    )


async def test_due_date_in_future_reschedules(order_factory, test_settings: Settings):
    order = _set_due_date(
        order_factory(
            order_type="Purchase",
            status="Processing",
            product_id="PRD-4141-4379",
            product_name="SoftwareOne FinOps for Cloud",
        ),
        "2026-12-31",
    )
    processor = _make_purchase_processor(order, test_settings)

    result = await processor.handle_exception(RuntimeError("boom"), now=FIXED_NOW)

    assert result == ProcessResult.RESCHEDULE
    processor.ext_client.fail_order.assert_not_awaited()


@pytest.mark.parametrize("due_date", ["2026-01-01", "2026-06-08"])  # past and == now
async def test_due_date_reached_fails_order_and_completes(
    order_factory, test_settings: Settings, due_date
):
    order = _set_due_date(
        order_factory(
            order_type="Purchase",
            status="Processing",
            product_id="PRD-4141-4379",
            product_name="SoftwareOne FinOps for Cloud",
        ),
        due_date,
    )
    processor = _make_purchase_processor(order, test_settings)

    result = await processor.handle_exception(RuntimeError("boom"), now=FIXED_NOW)

    assert result == ProcessResult.COMPLETE
    processor.ext_client.fail_order.assert_awaited_once_with(
        order_id=order["id"],
        payload=ERR_DUE_DATE_IS_REACHED.to_dict(due_date=due_date),
    )
