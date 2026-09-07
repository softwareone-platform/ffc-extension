import copy
import logging
from datetime import date
from typing import Any

import httpx
import pytest
from freezegun import freeze_time
from pytest_httpx import HTTPXMock
from pytest_mock import MockerFixture
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.conf import Settings
from app.db.handlers import AccountHandler, EntitlementHandler, OrganizationHandler
from app.db.models import Account, Entitlement, Organization
from app.enums import AccountStatus, AccountType, EntitlementStatus, OrganizationStatus
from app.events.orders.constants import (
    COMPLETED_TEMPLATE_TYPE,
    PROCESSING_TEMPLATE_TYPE,
    PURCHASE_EXISTING_TEMPLATE_NAME,
    PURCHASE_TEMPLATE_NAME,
    QUERYING_TEMPLATE_TYPE,
    TERMINATE_TEMPLATE_NAME,
)
from app.events.orders.error import (
    ERR_ADMIN_CONTACT,
    ERR_CURRENCY,
    ERR_DUE_DATE_IS_REACHED,
    ERR_DUE_DATE_NOT_SET,
    ERR_ORDER_TYPE_NOT_SUPPORTED,
    ERR_ORGANIZATION_NAME,
    ValidationError,
)
from app.events.orders.exceptions import (
    OrderMovedToQuery,
    OrderNotValidError,
    UnsupportedOrderTypeError,
)
from app.events.orders.processing import OrderEventHandler, PurchaseOrderProcessor
from app.events.processing import ProcessingStatus
from app.parameters import (
    PARAM_ADMIN_CONTACT,
    PARAM_CURRENCY,
    PARAM_DUE_DATE,
    PARAM_ORGANIZATION_NAME,
    get_ordering_parameter,
    set_due_date,
)
from tests.types import OrderFactory

PRODUCT_ID = "PRD-4141-4379"


# -- get_processor --


async def test_get_processor(
    purchase_order: dict[str, Any],
    db_session: AsyncSession,
    test_settings: Settings,
    httpx_mock: HTTPXMock,
    order_event_handler: OrderEventHandler,
) -> None:
    """`get_processor` builds the processor for the order type on the test session."""
    order_id = purchase_order["id"]
    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.mpt_api_base_url}/commerce/orders/{order_id}",
        match_params={"select": "subscriptions.lines"},
        json=purchase_order,
    )

    processor = await order_event_handler.get_processor(object_id=order_id)

    assert isinstance(processor, PurchaseOrderProcessor)
    assert processor.order == purchase_order
    assert processor.organization_repo.session is db_session


@freeze_time("2026-08-11")
async def test_process_order_without_due_date(
    purchase_order: dict[str, Any],
    test_settings: Settings,
    httpx_mock: HTTPXMock,
    order_event_handler: OrderEventHandler,
    product_templates: list[dict[str, Any]],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A fail_order error is logged and swallowed when the order has no due date"""
    purchase_order = set_due_date(purchase_order, None)
    order_id = purchase_order["id"]
    product_id = test_settings.mpt_product_id
    rows = test_settings.mpt_api_rows_per_page
    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.mpt_api_base_url}/commerce/orders/{order_id}",
        match_params={"select": "subscriptions.lines"},
        json=purchase_order,
    )

    # 1. apply_fulfillment_defaults writes the computed dueDate back; the marketplace replies
    #    with the order unchanged, so the processor still sees no due date afterwards
    defaulted_order = set_due_date(purchase_order, date(2026, 9, 10))
    httpx_mock.add_response(
        method="PUT",
        url=f"{test_settings.mpt_api_base_url}/commerce/orders/{order_id}",
        json=purchase_order,
        match_json={"parameters": defaulted_order["parameters"]},
    )
    # 2. simulate an error during set_processing_order_template
    httpx_mock.add_response(
        method="PUT",
        url=f"{test_settings.mpt_api_base_url}/commerce/orders/{order_id}",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        json={"errors": {"template": "Template TPL-0001 could not be assigned"}},
        match_json={"template": {"id": "TPL-0001"}},
    )
    httpx_mock.add_response(
        method="POST",
        url=f"{test_settings.mpt_api_base_url}/commerce/orders/{order_id}/fail",
        json=purchase_order,
        match_json={"statusNotes": ERR_DUE_DATE_NOT_SET.to_dict()},
    )

    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.mpt_api_base_url}/catalog/products/{product_id}/templates?limit={rows}&offset=0",
        json={
            "data": product_templates,
            "$meta": {"pagination": {"total": len(product_templates)}},
        },
    )
    processor = await order_event_handler.get_processor(object_id=order_id)

    with caplog.at_level(logging.ERROR):
        result = await processor.process()
    assert result.status is ProcessingStatus.CANCEL
    assert result.severity == "Error"
    assert f"{order_id}: order processing failed." in caplog.text
    assert result.message == ERR_DUE_DATE_NOT_SET.message


async def test_get_processor_rejects_unsupported_order_type(
    purchase_order: dict[str, Any],
    test_settings: Settings,
    httpx_mock: HTTPXMock,
    order_event_handler: OrderEventHandler,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """`get_processor` raises and warns for an order type with no processor."""
    purchase_order["type"] = "BlaBla"
    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.mpt_api_base_url}/commerce/orders/{purchase_order['id']}",
        match_params={"select": "subscriptions.lines"},
        json=purchase_order,
    )

    with caplog.at_level(logging.WARNING):
        with pytest.raises(UnsupportedOrderTypeError, match="BlaBla"):
            await order_event_handler.get_processor(object_id=purchase_order["id"])

    assert "The order type BlaBla is not supported." in caplog.text


# -- OrderProcessor.set_template --


async def test_set_template_assigns_id_and_returns_copy(
    purchase_order: dict[str, Any],
    test_settings: Settings,
    httpx_mock: HTTPXMock,
    order_event_handler: OrderEventHandler,
) -> None:
    """`set_template` returns a copy with the new template id, leaving the original untouched."""
    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.mpt_api_base_url}/commerce/orders/{purchase_order['id']}",
        match_params={"select": "subscriptions.lines"},
        json=purchase_order,
    )

    processor = await order_event_handler.get_processor(object_id=purchase_order["id"])

    result = processor.set_template(order=purchase_order, template_id="TPL-1234-5678-0001")
    assert processor.order is result
    assert result["template"]["id"] == "TPL-1234-5678-0001"
    assert purchase_order["template"]["id"] == "TPL-1234-1234-4321"
    assert purchase_order["template"]["name"] == "Default Template"


async def test_set_template_raises_when_template_id_is_missing(
    purchase_order: dict[str, Any],
    test_settings: Settings,
    httpx_mock: HTTPXMock,
    order_event_handler: OrderEventHandler,
) -> None:
    """`set_template` raises `ValueError` when no template id is provided."""
    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.mpt_api_base_url}/commerce/orders/{purchase_order['id']}",
        match_params={"select": "subscriptions.lines"},
        json=purchase_order,
    )

    processor = await order_event_handler.get_processor(object_id=purchase_order["id"])

    with pytest.raises(ValueError, match="Template id is required"):
        processor.set_template(order=purchase_order, template_id="")


async def test_set_template_raises_when_order_malformed(
    purchase_order: dict[str, Any],
    test_settings: Settings,
    httpx_mock: HTTPXMock,
    order_event_handler: OrderEventHandler,
) -> None:
    """`set_template` raises `KeyError` when the order is missing its template key."""
    purchase_order.pop("template", None)
    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.mpt_api_base_url}/commerce/orders/{purchase_order['id']}",
        match_params={"select": "subscriptions.lines"},
        json=purchase_order,
    )

    processor = await order_event_handler.get_processor(object_id=purchase_order["id"])

    with pytest.raises(KeyError, match="Order is malformed"):
        processor.set_template(order=purchase_order, template_id="TPL-1234-5678-0001")


# -- get_product_template_id / fetch_product_templates --


async def test_get_product_template_returns_specific_by_name(
    purchase_order: dict[str, Any],
    test_settings: Settings,
    httpx_mock: HTTPXMock,
    order_event_handler: OrderEventHandler,
    product_templates: list[dict[str, Any]],
) -> None:
    """`get_product_template_id` returns the id of the template matching the type and name."""
    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.mpt_api_base_url}/commerce/orders/{purchase_order['id']}",
        match_params={"select": "subscriptions.lines"},
        json=purchase_order,
    )

    processor = await order_event_handler.get_processor(object_id=purchase_order["id"])
    rows = test_settings.mpt_api_rows_per_page
    httpx_mock.add_response(
        method="GET",
        url=(
            f"{test_settings.mpt_api_base_url}/catalog/products/{PRODUCT_ID}/templates?limit={rows}&offset=0"
        ),
        json={
            "data": product_templates,
            "$meta": {"pagination": {"total": len(product_templates)}},
        },
    )

    template_id = await processor.get_product_template_id(PROCESSING_TEMPLATE_TYPE, "Purchase")
    assert template_id == "TPL-0001"


async def test_get_product_template_fails_back_to_default(
    purchase_order: dict[str, Any],
    test_settings: Settings,
    httpx_mock: HTTPXMock,
    order_event_handler: OrderEventHandler,
    product_templates: list[dict[str, Any]],
) -> None:
    """`get_product_template_id` falls back to the default template when the name is unknown."""
    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.mpt_api_base_url}/commerce/orders/{purchase_order['id']}",
        match_params={"select": "subscriptions.lines"},
        json=purchase_order,
    )
    rows = test_settings.mpt_api_rows_per_page
    httpx_mock.add_response(
        method="GET",
        url=(
            f"{test_settings.mpt_api_base_url}/catalog/products/{PRODUCT_ID}/templates?limit={rows}&offset=0"
        ),
        json={
            "data": product_templates,
            "$meta": {"pagination": {"total": len(product_templates)}},
        },
    )
    processor = await order_event_handler.get_processor(object_id=purchase_order["id"])

    template_id = await processor.get_product_template_id(PROCESSING_TEMPLATE_TYPE, "DoesNotExist")
    assert template_id == "TPL-0002"


async def test_get_product_template_returns_default_when_name_is_none(
    purchase_order: dict[str, Any],
    test_settings: Settings,
    httpx_mock: HTTPXMock,
    order_event_handler: OrderEventHandler,
    product_templates: list[dict[str, Any]],
) -> None:
    """`get_product_template_id` returns the default template when the requested name is `None`."""
    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.mpt_api_base_url}/commerce/orders/{purchase_order['id']}",
        match_params={"select": "subscriptions.lines"},
        json=purchase_order,
    )
    rows = test_settings.mpt_api_rows_per_page
    httpx_mock.add_response(
        method="GET",
        url=(
            f"{test_settings.mpt_api_base_url}/catalog/products/{PRODUCT_ID}/templates?limit={rows}&offset=0"
        ),
        json={
            "data": product_templates,
            "$meta": {"pagination": {"total": len(product_templates)}},
        },
    )
    processor = await order_event_handler.get_processor(object_id=purchase_order["id"])

    template_id = await processor.get_product_template_id(QUERYING_TEMPLATE_TYPE, None)
    assert template_id == "TPL-0003"


async def test_get_product_template_uses_cache_without_http_call(
    purchase_order: dict[str, Any],
    test_settings: Settings,
    httpx_mock: HTTPXMock,
    order_event_handler: OrderEventHandler,
) -> None:
    """`get_product_template_id` serves a cached template without hitting the marketplace."""
    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.mpt_api_base_url}/commerce/orders/{purchase_order['id']}",
        match_params={"select": "subscriptions.lines"},
        json=purchase_order,
    )
    processor = await order_event_handler.get_processor(object_id=purchase_order["id"])
    processor.template_cache[(PROCESSING_TEMPLATE_TYPE, PURCHASE_TEMPLATE_NAME)] = "TPL-CACHED"
    processor.template_cache[(PROCESSING_TEMPLATE_TYPE, None)] = "TPL-DEFAULT"

    template_id = await processor.get_product_template_id(
        PROCESSING_TEMPLATE_TYPE, PURCHASE_TEMPLATE_NAME
    )
    assert template_id == "TPL-CACHED"


async def test_get_product_template_raises_exception(
    purchase_order: dict[str, Any],
    test_settings: Settings,
    httpx_mock: HTTPXMock,
    order_event_handler: OrderEventHandler,
) -> None:
    """`get_product_template_id` raises when the product declares no template of that type."""
    rows = test_settings.mpt_api_rows_per_page
    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.mpt_api_base_url}/commerce/orders/{purchase_order['id']}",
        match_params={"select": "subscriptions.lines"},
        json=purchase_order,
    )
    # the product has no template at all: neither the named one nor a default is cached
    httpx_mock.add_response(
        method="GET",
        url=(
            f"{test_settings.mpt_api_base_url}/catalog/products/{PRODUCT_ID}"
            f"/templates?limit={rows}&offset=0"
        ),
        json={"data": [], "$meta": {"pagination": {"total": 0}}},
    )
    processor = await order_event_handler.get_processor(object_id=purchase_order["id"])

    with pytest.raises(OrderNotValidError, match="has no template type"):
        await processor.get_product_template_id(PROCESSING_TEMPLATE_TYPE, PURCHASE_TEMPLATE_NAME)

    assert processor.template_cache == {}


async def test_fetch_product_template_builds_cache(
    purchase_order: dict[str, Any],
    test_settings: Settings,
    httpx_mock: HTTPXMock,
    order_event_handler: OrderEventHandler,
    product_templates: list[dict[str, Any]],
) -> None:
    """`fetch_product_templates` caches every template keyed by type and name."""
    rows = test_settings.mpt_api_rows_per_page
    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.mpt_api_base_url}/commerce/orders/{purchase_order['id']}",
        match_params={"select": "subscriptions.lines"},
        json=purchase_order,
    )
    httpx_mock.add_response(
        method="GET",
        url=(
            f"{test_settings.mpt_api_base_url}/catalog/products/{PRODUCT_ID}/templates?limit={rows}&offset=0"
        ),
        json={
            "data": product_templates,
            "$meta": {"pagination": {"total": len(product_templates)}},
        },
    )
    processor = await order_event_handler.get_processor(object_id=purchase_order["id"])

    await processor.fetch_product_templates(PRODUCT_ID)
    assert processor.template_cache == {
        (PROCESSING_TEMPLATE_TYPE, PURCHASE_TEMPLATE_NAME): "TPL-0001",
        (PROCESSING_TEMPLATE_TYPE, None): "TPL-0002",
        (QUERYING_TEMPLATE_TYPE, None): "TPL-0003",
        (COMPLETED_TEMPLATE_TYPE, None): "TPL-0004",
        (COMPLETED_TEMPLATE_TYPE, PURCHASE_TEMPLATE_NAME): "TPL-0005",
        (COMPLETED_TEMPLATE_TYPE, PURCHASE_EXISTING_TEMPLATE_NAME): "TPL-0006",
    }
    templates_requests = [
        request
        for request in httpx_mock.get_requests(method="GET")
        if "/templates" in str(request.url)
    ]
    assert len(templates_requests) == 1


async def test_fetch_product_templates_with_no_templates_leaves_cache_empty(
    purchase_order: dict[str, Any],
    test_settings: Settings,
    httpx_mock: HTTPXMock,
    order_event_handler: OrderEventHandler,
) -> None:
    """`fetch_product_templates` leaves the cache empty when no templates are returned."""
    rows = test_settings.mpt_api_rows_per_page
    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.mpt_api_base_url}/commerce/orders/{purchase_order['id']}",
        match_params={"select": "subscriptions.lines"},
        json=purchase_order,
    )
    httpx_mock.add_response(
        method="GET",
        url=(
            f"{test_settings.mpt_api_base_url}/catalog/products/{PRODUCT_ID}/templates?limit={rows}&offset=0"
        ),
        json={
            "data": [],
            "$meta": {"pagination": {"total": 0}},
        },
    )
    processor = await order_event_handler.get_processor(object_id=purchase_order["id"])

    await processor.fetch_product_templates(PRODUCT_ID)
    assert processor.template_cache == {}


# -- set_processing_order_template --


async def test_set_processing_order_template_switches_template(
    purchase_order: dict[str, Any],
    test_settings: Settings,
    httpx_mock: HTTPXMock,
    order_event_handler: OrderEventHandler,
    product_templates: list[dict[str, Any]],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """`set_processing_order_template` swaps in the purchase template when it differs."""
    rows = test_settings.mpt_api_rows_per_page
    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.mpt_api_base_url}/commerce/orders/{purchase_order['id']}",
        match_params={"select": "subscriptions.lines"},
        json=purchase_order,
    )
    httpx_mock.add_response(
        method="GET",
        url=(
            f"{test_settings.mpt_api_base_url}/catalog/products/{PRODUCT_ID}/templates?limit={rows}&offset=0"
        ),
        json={
            "data": product_templates,
            "$meta": {"pagination": {"total": len(product_templates)}},
        },
    )

    processor = await order_event_handler.get_processor(object_id=purchase_order["id"])

    updated_order = copy.deepcopy(purchase_order)
    updated_order["template"]["id"] = "TPL-0001"
    httpx_mock.add_response(
        method="PUT",
        url=f"{test_settings.mpt_api_base_url}/commerce/orders/{purchase_order['id']}",
        json=updated_order,
    )

    with caplog.at_level(logging.INFO):
        response = await processor.set_processing_order_template()
    assert response == updated_order
    assert processor.order == updated_order
    assert f"{purchase_order['id']}: processing template set to Purchase (TPL-0001)" in caplog.text
    assert f"{purchase_order['id']}: processing template is ok, continue" in caplog.text


async def test_set_processing_order_template_keeps_matching_template(
    test_settings: Settings,
    httpx_mock: HTTPXMock,
    order_event_handler: OrderEventHandler,
    order_factory: OrderFactory,
    product_templates: list[dict[str, Any]],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """`set_processing_order_template` leaves the order untouched when it already matches."""
    rows = test_settings.mpt_api_rows_per_page
    order = order_factory(
        order_type="Purchase",
        status="Processing",
        product_id=PRODUCT_ID,
        product_name="SoftwareOne FinOps for Cloud",
        template={"id": "TPL-0001", "name": "Purchase", "revision": 1},
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.mpt_api_base_url}/commerce/orders/{order['id']}",
        match_params={"select": "subscriptions.lines"},
        json=order,
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.mpt_api_base_url}/catalog/products/{PRODUCT_ID}/templates?limit={rows}&offset=0",
        json={
            "data": product_templates,
            "$meta": {"pagination": {"total": len(product_templates)}},
        },
    )

    processor = await order_event_handler.get_processor(object_id=order["id"])

    with caplog.at_level(logging.INFO):
        response = await processor.set_processing_order_template()
    assert response == order
    assert processor.order == order
    assert f"{order['id']}: processing template is ok, continue" in caplog.text
    assert "processing template set to" not in caplog.text
    assert httpx_mock.get_requests(method="PUT") == []


# -- validate_and_move_to_querying_if_needed / validate --


async def test_validate_returns_true_for_valid_order(
    purchase_order: dict[str, Any],
    test_settings: Settings,
    httpx_mock: HTTPXMock,
    order_event_handler: OrderEventHandler,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """`validate_and_move_to_querying_if_needed` returns `True` and touches nothing when valid."""
    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.mpt_api_base_url}/commerce/orders/{purchase_order['id']}",
        match_params={"select": "subscriptions.lines"},
        json=purchase_order,
    )
    processor = await order_event_handler.get_processor(object_id=purchase_order["id"])
    order_before = copy.deepcopy(processor.order)

    result = await processor.validate_and_move_to_querying_if_needed()
    assert result is True
    assert processor.order == order_before  # nothing written back
    assert processor.template_cache == {}  # querying template never fetched
    assert [str(request.url) for request in httpx_mock.get_requests()] == [
        f"{test_settings.mpt_api_base_url}/commerce/orders/{purchase_order['id']}"
        "?select=subscriptions.lines"
    ]
    assert "move to querying" not in caplog.text


@pytest.mark.parametrize(
    ("external_id", "expected_error"),
    [
        (PARAM_ORGANIZATION_NAME, ERR_ORGANIZATION_NAME),
        (PARAM_CURRENCY, ERR_CURRENCY),
        (PARAM_ADMIN_CONTACT, ERR_ADMIN_CONTACT),
    ],
)
async def test_validate_moves_invalid_order_to_querying(
    purchase_order: dict[str, Any],
    test_settings: Settings,
    httpx_mock: HTTPXMock,
    order_event_handler: OrderEventHandler,
    caplog: pytest.LogCaptureFixture,
    external_id: str,
    expected_error: ValidationError,
) -> None:
    """`validate_and_move_to_querying_if_needed` writes back errors and moves invalid orders.

    Every required ordering parameter is covered: each one must reach the marketplace as a
    JSON error object, which is what `check_order_parameters` builds from its `ValidationError`.
    """
    rows = test_settings.mpt_api_rows_per_page
    invalid_parameter = get_ordering_parameter(purchase_order, external_id)
    invalid_parameter["value"] = None
    querying_order = copy.deepcopy(purchase_order)
    querying_order["status"] = "Querying"
    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.mpt_api_base_url}/commerce/orders/{purchase_order['id']}",
        match_params={"select": "subscriptions.lines"},
        json=purchase_order,
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.mpt_api_base_url}/catalog/products/{PRODUCT_ID}/templates?limit={rows}&offset=0",
        json={
            "data": [
                {"id": "TPL-0003", "type": "OrderQuerying", "name": "Querying", "default": True}
            ],
            "$meta": {"pagination": {"total": 1}},
        },
    )
    # the validation error is written into the parameters as a JSON object
    expected_order = copy.deepcopy(purchase_order)
    expected_parameter = get_ordering_parameter(expected_order, external_id)
    expected_parameter["error"] = expected_error.to_dict()
    expected_parameter["constraints"] = {"hidden": False, "required": True}
    httpx_mock.add_response(
        method="PUT",
        url=f"{test_settings.mpt_api_base_url}/commerce/orders/{purchase_order['id']}",
        json=purchase_order,
        match_json={"parameters": expected_order["parameters"]},
    )

    httpx_mock.add_response(
        method="POST",
        url=f"{test_settings.mpt_api_base_url}/commerce/orders/{purchase_order['id']}/query",
        json=querying_order,
        match_json={"template": {"id": "TPL-0003"}},
    )
    processor = await order_event_handler.get_processor(object_id=purchase_order["id"])

    with caplog.at_level(logging.INFO):
        result = await processor.validate_and_move_to_querying_if_needed()
    assert result is False
    assert (
        f"{purchase_order['id']}: ordering parameters are invalid, move to querying" in caplog.text
    )


async def test_validate_status_not_valid(
    order_factory: OrderFactory,
    order_event_handler: OrderEventHandler,
    test_settings: Settings,
    httpx_mock: HTTPXMock,
) -> None:
    """`validate` raises `OrderNotValidError` when the order is not in Processing status."""
    order = order_factory(
        order_type="Purchase",
        status="Completed",
        product_id=PRODUCT_ID,
        product_name="SoftwareOne FinOps for Cloud",
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.mpt_api_base_url}/commerce/orders/{order['id']}",
        match_params={"select": "subscriptions.lines"},
        json=order,
    )
    processor = await order_event_handler.get_processor(object_id=order["id"])

    with pytest.raises(OrderNotValidError, match=order["id"]):
        await processor.validate()


async def test_validate_passes_for_valid_processing_order(
    purchase_order: dict[str, Any],
    order_event_handler: OrderEventHandler,
    test_settings: Settings,
    httpx_mock: HTTPXMock,
) -> None:
    """`validate` returns `None` and does not move a valid Processing order to querying."""
    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.mpt_api_base_url}/commerce/orders/{purchase_order['id']}",
        match_params={"select": "subscriptions.lines"},
        json=purchase_order,
    )
    processor = await order_event_handler.get_processor(object_id=purchase_order["id"])

    assert await processor.validate() is None
    assert httpx_mock.get_requests(method="PUT") == []
    assert httpx_mock.get_requests(method="POST") == []


async def test_validate_order_raises_when_moved_to_querying(
    purchase_order: dict[str, Any],
    order_event_handler: OrderEventHandler,
    test_settings: Settings,
    httpx_mock: HTTPXMock,
) -> None:
    """`validate` raises `OrderMovedToQuery` after an invalid order is moved to querying."""
    rows = test_settings.mpt_api_rows_per_page
    get_ordering_parameter(purchase_order, PARAM_ORGANIZATION_NAME)["value"] = None
    querying_order = copy.deepcopy(purchase_order)
    querying_order["status"] = "Querying"
    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.mpt_api_base_url}/commerce/orders/{purchase_order['id']}",
        match_params={"select": "subscriptions.lines"},
        json=purchase_order,
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.mpt_api_base_url}/catalog/products/{PRODUCT_ID}/templates?limit={rows}&offset=0",
        json={
            "data": [
                {"id": "TPL-0003", "type": "OrderQuerying", "name": "Querying", "default": True}
            ],
            "$meta": {"pagination": {"total": 1}},
        },
    )

    expected_order = copy.deepcopy(purchase_order)
    expected_parameter = get_ordering_parameter(expected_order, PARAM_ORGANIZATION_NAME)
    expected_parameter["error"] = ERR_ORGANIZATION_NAME.to_dict()
    expected_parameter["constraints"] = {"hidden": False, "required": True}

    httpx_mock.add_response(
        method="PUT",
        url=f"{test_settings.mpt_api_base_url}/commerce/orders/{purchase_order['id']}",
        json=purchase_order,
        match_json={"parameters": expected_order["parameters"]},
    )
    httpx_mock.add_response(
        method="POST",
        url=f"{test_settings.mpt_api_base_url}/commerce/orders/{purchase_order['id']}/query",
        json=querying_order,
        match_json={"template": {"id": "TPL-0003"}},
    )
    processor = await order_event_handler.get_processor(object_id=purchase_order["id"])

    with pytest.raises(OrderMovedToQuery, match=purchase_order["id"]):
        await processor.validate()


# -- apply_fulfillment_defaults --


async def test_apply_fulfillment_defaults_noop_when_nothing_to_update(
    purchase_order: dict[str, Any],
    order_event_handler: OrderEventHandler,
    test_settings: Settings,
    httpx_mock: HTTPXMock,
) -> None:
    """`apply_fulfillment_defaults` returns the order unchanged when no parameters need defaults."""
    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.mpt_api_base_url}/commerce/orders/{purchase_order['id']}",
        match_params={"select": "subscriptions.lines"},
        json=purchase_order,
    )
    processor = await order_event_handler.get_processor(object_id=purchase_order["id"])

    response = await processor.apply_fulfillment_defaults()
    assert response == purchase_order
    assert httpx_mock.get_requests(method="PUT") == []


@freeze_time("2026-08-11")
async def test_apply_fulfillment_defaults_fills_missing_parameters(
    purchase_order: dict[str, Any],
    order_event_handler: OrderEventHandler,
    test_settings: Settings,
    httpx_mock: HTTPXMock,
) -> None:
    """`apply_fulfillment_defaults` persists the order once defaults are applied."""
    for param in purchase_order["parameters"]["fulfillment"]:
        if param["externalId"] in {
            PARAM_DUE_DATE,
            "billedPercentage",
            "trialStartDate",
            "trialEndDate",
        }:
            param["value"] = None
    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.mpt_api_base_url}/commerce/orders/{purchase_order['id']}",
        match_params={"select": "subscriptions.lines"},
        json=purchase_order,
    )
    updated_order = copy.deepcopy(purchase_order)
    updated_order["parameters"]["fulfillment"] = [
        {**parameter, "value": "filled-by-marketplace"}
        for parameter in updated_order["parameters"]["fulfillment"]
    ]

    expected_values = {
        PARAM_DUE_DATE: "2026-09-10",
        "billedPercentage": "4",
        "trialStartDate": "2026-08-11",
        "trialEndDate": "2026-09-10",
    }
    expected_parameters = copy.deepcopy(purchase_order["parameters"])
    for parameter in expected_parameters["fulfillment"]:
        if parameter["externalId"] in expected_values:
            parameter["value"] = expected_values[parameter["externalId"]]

    httpx_mock.add_response(
        method="PUT",
        url=f"{test_settings.mpt_api_base_url}/commerce/orders/{purchase_order['id']}",
        json=updated_order,
        match_json={"parameters": expected_parameters},
    )
    processor = await order_event_handler.get_processor(object_id=purchase_order["id"])

    response = await processor.apply_fulfillment_defaults()
    assert response == updated_order
    assert processor.order == updated_order


# -- get_or_create_organization --


async def test_get_or_create_organization(
    purchase_order: dict[str, Any],
    test_settings: Settings,
    httpx_mock: HTTPXMock,
    order_event_handler: OrderEventHandler,
    db_session: AsyncSession,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """`get_or_create_organization` provisions a new OptScale org and links the agreement."""
    agreement_id = purchase_order["agreement"]["id"]
    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.mpt_api_base_url}/commerce/orders/{purchase_order['id']}",
        match_params={"select": "subscriptions.lines"},
        json=purchase_order,
    )
    # Only the authorization currency is read from the agreement (the billing currency).
    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.mpt_api_base_url}/commerce/agreements/{agreement_id}",
        match_params={"select": "authorization"},
        json={
            "id": agreement_id,
            "authorization": {
                "id": "AUT-3727-1184",
                "name": "SoftwareOne FinOps for Cloud (USD)",
                "currency": "USD",
            },
        },
    )
    httpx_mock.add_response(
        method="POST",
        url=f"{test_settings.api_modifier_base_url}/organizations",
        json={"id": "OPT-ORG-0001"},
        status_code=201,
        match_json={
            "org_name": "ACME Inc",
            "user_id": "employee-id",
            "currency": "USD",
        },
    )

    httpx_mock.add_response(
        method="PUT",
        url=f"{test_settings.mpt_api_base_url}/commerce/agreements/{agreement_id}",
        json={"id": agreement_id},
    )
    processor = await order_event_handler.get_processor(object_id=purchase_order["id"])

    with caplog.at_level(logging.INFO):
        organization = await processor.get_or_create_organization(employee_id="employee-id")
    assert organization.name == "ACME Inc"
    assert organization.currency == "USD"
    assert organization.billing_currency == "USD"
    assert organization.operations_external_id == agreement_id
    assert organization.linked_organization_id == "OPT-ORG-0001"
    stored = await db_session.scalar(
        select(Organization).where(Organization.operations_external_id == agreement_id)
    )
    assert stored.id == organization.id
    assert stored.linked_organization_id == "OPT-ORG-0001"

    assert httpx_mock.get_request(
        method="PUT",
        url=f"{test_settings.mpt_api_base_url}/commerce/agreements/{agreement_id}",
        match_json={"externalIds": {"vendor": organization.id}},
    )


async def test_get_or_create_organization_already_exists(
    purchase_order: dict[str, Any],
    test_settings: Settings,
    httpx_mock: HTTPXMock,
    order_event_handler: OrderEventHandler,
    db_session: AsyncSession,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """`get_or_create_organization` reuses an already-linked organization without provisioning."""
    agreement_id = purchase_order["agreement"]["id"]
    existing_organization = await OrganizationHandler(db_session).create(
        Organization(
            name="Pre-existing ORG",
            currency="EUR",
            billing_currency="USD",
            operations_external_id=agreement_id,
            linked_organization_id="already-linked-optscale-org-id",
        )
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.mpt_api_base_url}/commerce/orders/{purchase_order['id']}",
        match_params={"select": "subscriptions.lines"},
        json=purchase_order,
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.mpt_api_base_url}/commerce/agreements/{agreement_id}",
        match_params={"select": "authorization"},
        json={
            "id": agreement_id,
            "authorization": {
                "id": "AUT-3727-1184",
                "name": "SoftwareOne FinOps for Cloud (USD)",
                "currency": "USD",
            },
        },
    )
    processor = await order_event_handler.get_processor(object_id=purchase_order["id"])

    with caplog.at_level(logging.INFO):
        organization = await processor.get_or_create_organization("employee-id")

    assert organization.id == existing_organization.id
    assert organization.name == "Pre-existing ORG"
    assert organization.currency == "EUR"
    assert organization.billing_currency == "USD"
    assert organization.linked_organization_id == "already-linked-optscale-org-id"
    assert httpx_mock.get_requests(method="POST") == []
    assert httpx_mock.get_requests(method="PUT") == []
    # the stored row is left exactly as it was: nothing is re-provisioned or re-linked
    await db_session.refresh(existing_organization)
    assert existing_organization.name == "Pre-existing ORG"
    assert existing_organization.currency == "EUR"
    assert existing_organization.billing_currency == "USD"
    assert existing_organization.linked_organization_id == "already-linked-optscale-org-id"
    assert existing_organization.status == OrganizationStatus.ACTIVE
    assert f"Organization already exists with id {existing_organization.id}" in caplog.text
    assert "Organization on OptScale created" not in caplog.text


async def test_get_or_create_organization_links_existing_unlinked_organization(
    purchase_order: dict[str, Any],
    test_settings: Settings,
    httpx_mock: HTTPXMock,
    order_event_handler: OrderEventHandler,
    db_session: AsyncSession,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """`get_or_create_organization` provisions OptScale for a stored organization with no link."""
    agreement_id = purchase_order["agreement"]["id"]
    existing_organization = await OrganizationHandler(db_session).create(
        Organization(
            name="Pre-existing ORG",
            currency="EUR",
            billing_currency="USD",
            operations_external_id=agreement_id,
            linked_organization_id=None,
            status=OrganizationStatus.ACTIVE,
        )
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.mpt_api_base_url}/commerce/orders/{purchase_order['id']}",
        match_params={"select": "subscriptions.lines"},
        json=purchase_order,
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.mpt_api_base_url}/commerce/agreements/{agreement_id}",
        match_params={"select": "authorization"},
        json={
            "id": agreement_id,
            "authorization": {"id": "AUT-3727-1184", "currency": "USD"},
        },
    )
    httpx_mock.add_response(
        method="POST",
        url=f"{test_settings.api_modifier_base_url}/organizations",
        json={"id": "OPT-ORG-0002"},
        match_json={
            "org_name": "ACME Inc",
            "user_id": "employee-id",
            "currency": "USD",
        },
    )
    httpx_mock.add_response(
        method="PUT",
        url=f"{test_settings.mpt_api_base_url}/commerce/agreements/{agreement_id}",
        json={"id": agreement_id},
        match_json={"externalIds": {"vendor": existing_organization.id}},
    )
    processor = await order_event_handler.get_processor(object_id=purchase_order["id"])

    with caplog.at_level(logging.INFO):
        organization = await processor.get_or_create_organization(employee_id="employee-id")

    assert organization.id == existing_organization.id
    assert organization.linked_organization_id == "OPT-ORG-0002"
    await db_session.refresh(existing_organization)
    assert existing_organization.linked_organization_id == "OPT-ORG-0002"
    # the stored row is reused, not replaced: its own fields are untouched
    assert existing_organization.name == "Pre-existing ORG"
    assert existing_organization.currency == "EUR"

    assert "Organization on OptScale created with id OPT-ORG-0002" in caplog.text
    assert "Organization already exists with id" not in caplog.text


# -- create_employee --


async def test_create_employee_with_existing_user(
    purchase_order: dict[str, Any],
    test_settings: Settings,
    httpx_mock: HTTPXMock,
    order_event_handler: OrderEventHandler,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """`create_employee` reuses the existing OptScale user and records `isNewUser`."""
    employee_id = "f0bd0c4a-7c55-45b7-8b58-27740e38789a"
    updated_order = copy.deepcopy(purchase_order)
    for param in updated_order["parameters"]["fulfillment"]:
        if param["externalId"] == "isNewUser":
            param["value"] = None

    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.mpt_api_base_url}/commerce/orders/{purchase_order['id']}",
        match_params={"select": "subscriptions.lines"},
        json=purchase_order,
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.optscale_auth_api_base_url}/user_existence",
        match_params={"email": "pl@example.com", "user_info": "true"},
        json={
            "exists": True,
            "user_info": {
                "id": employee_id,
                "display_name": "Spider Man",
                "email": "pl@example.com",
            },
        },
    )

    httpx_mock.add_response(
        method="PUT",
        url=f"{test_settings.mpt_api_base_url}/commerce/orders/{purchase_order['id']}",
        json=updated_order,
    )
    processor = await order_event_handler.get_processor(object_id=purchase_order["id"])

    with caplog.at_level(logging.INFO):
        employee_id, employee_email = await processor.create_employee()

    assert processor.order == updated_order
    assert employee_id == "f0bd0c4a-7c55-45b7-8b58-27740e38789a"
    assert employee_email == "pl@example.com"
    assert httpx_mock.get_requests(method="POST") == []
    assert f"Employee exists with id {employee_id} for order {purchase_order['id']}" in caplog.text


async def test_create_employee_with_no_existing_user(
    purchase_order: dict[str, Any],
    test_settings: Settings,
    httpx_mock: HTTPXMock,
    order_event_handler: OrderEventHandler,
    caplog: pytest.LogCaptureFixture,
    mocker: MockerFixture,
) -> None:
    """`create_employee` provisions a new OptScale user when none exists and flags `isNewUser`."""
    order_id = purchase_order["id"]
    employee_id = "f0bd0c4a-7c55-45b7-8b58-27740e38789a"
    generated_password = "a-generated-password"
    mocker.patch(
        "app.events.orders.processing.secrets.token_urlsafe",
        return_value=generated_password,
    )
    updated_order = copy.deepcopy(purchase_order)
    for param in updated_order["parameters"]["fulfillment"]:
        if param["externalId"] == "isNewUser":
            param["value"] = ["Yes"]

    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.mpt_api_base_url}/commerce/orders/{order_id}",
        match_params={"select": "subscriptions.lines"},
        json=purchase_order,
    )
    # the user does not exist yet on OptScale
    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.optscale_auth_api_base_url}/user_existence",
        match_params={"email": "pl@example.com", "user_info": "true"},
        json={"exists": False},
    )
    httpx_mock.add_response(
        method="POST",
        url=f"{test_settings.api_modifier_base_url}/users",
        json={
            "id": employee_id,
            "display_name": "Spider Man",
            "email": "peter.parker@iamspiderman.com",
        },
        match_json={
            "email": "pl@example.com",
            "display_name": "PL NN",
            "password": generated_password,
        },
    )
    httpx_mock.add_response(
        method="PUT",
        url=f"{test_settings.mpt_api_base_url}/commerce/orders/{order_id}",
        json=updated_order,
        match_json={"parameters": updated_order["parameters"]},
    )
    processor = await order_event_handler.get_processor(object_id=order_id)

    with caplog.at_level(logging.INFO):
        created_employee_id, employee_email = await processor.create_employee()

    assert created_employee_id == employee_id
    assert employee_email == "pl@example.com"
    assert processor.order == updated_order

    assert f"Employee created with id {employee_id} for order {order_id}" in caplog.text


# -- subscriptions --


async def test_create_order_subscription_skips_when_subscription_already_exists(
    purchase_order: dict[str, Any],
    test_settings: Settings,
    httpx_mock: HTTPXMock,
    order_event_handler: OrderEventHandler,
    db_session: AsyncSession,
) -> None:
    """`create_order_subscription` does nothing when the line already has a subscription."""
    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.mpt_api_base_url}/commerce/orders/{purchase_order['id']}",
        match_params={"select": "subscriptions.lines"},
        json=purchase_order,
    )
    organization = await OrganizationHandler(db_session).create(
        Organization(
            name="ACME Inc",
            currency="USD",
            billing_currency="USD",
            operations_external_id=purchase_order["agreement"]["id"],
            linked_organization_id="OPT-ORG-0001",
        )
    )
    processor = await order_event_handler.get_processor(object_id=purchase_order["id"])
    await processor.create_order_subscription(organization)
    assert organization.id is not None
    assert httpx_mock.get_requests(method="POST") == []


async def test_create_order_subscription_creates_missing_subscription(
    order_factory: OrderFactory,
    test_settings: Settings,
    httpx_mock: HTTPXMock,
    order_event_handler: OrderEventHandler,
    db_session: AsyncSession,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """`create_order_subscription` creates and links a subscription for an uncovered line."""
    order = order_factory(
        order_type="Purchase",
        status="Processing",
        product_id=PRODUCT_ID,
        product_name="SoftwareOne FinOps for Cloud",
        subscriptions=[],
    )
    line = order["lines"][0]
    organization = await OrganizationHandler(db_session).create(
        Organization(
            name="ACME Inc",
            currency="USD",
            billing_currency="USD",
            operations_external_id=order["agreement"]["id"],
            linked_organization_id="OPT-ORG-0001",
        )
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.mpt_api_base_url}/commerce/orders/{order['id']}",
        match_params={"select": "subscriptions.lines"},
        json=order,
    )
    httpx_mock.add_response(
        method="POST",
        url=f"{test_settings.mpt_api_base_url}/commerce/orders/{order['id']}/subscriptions",
        json={"id": "SUB-9999-0001"},
        match_json={
            "name": f"Subscription for {line['item']['name']}",
            "parameters": {},
            "externalIds": {"vendor": organization.id},
            "lines": [{"id": line["id"]}],
        },
    )

    processor = await order_event_handler.get_processor(object_id=order["id"])

    with caplog.at_level(logging.INFO):
        await processor.create_order_subscription(organization)

    assert f"{order['id']}: subscription {line['id']} (SUB-9999-0001) created" in caplog.text


# -- get_complete_template --


@pytest.mark.parametrize(
    ("is_new", "expected_template_id"),
    [(True, "TPL-0005"), (False, "TPL-0006")],
)
async def test_get_complete_template(
    purchase_order: dict[str, Any],
    httpx_mock: HTTPXMock,
    order_event_handler: OrderEventHandler,
    is_new: bool,
    expected_template_id: str,
    test_settings: Settings,
) -> None:
    """`get_complete_template` selects the new/existing completed template by the `is_new` flag."""
    rows = test_settings.mpt_api_rows_per_page
    templates = [
        {
            "id": "TPL-0005",
            "type": COMPLETED_TEMPLATE_TYPE,
            "name": PURCHASE_TEMPLATE_NAME,
            "default": False,
        },
        {
            "id": "TPL-0006",
            "type": COMPLETED_TEMPLATE_TYPE,
            "name": PURCHASE_EXISTING_TEMPLATE_NAME,
            "default": False,
        },
    ]
    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.mpt_api_base_url}/commerce/orders/{purchase_order['id']}",
        match_params={"select": "subscriptions.lines"},
        json=purchase_order,
    )

    httpx_mock.add_response(
        method="GET",
        url=(
            f"{test_settings.mpt_api_base_url}/catalog/products/{PRODUCT_ID}"
            f"/templates?limit={rows}&offset=0"
        ),
        json={"data": templates, "$meta": {"pagination": {"total": len(templates)}}},
    )
    processor = await order_event_handler.get_processor(object_id=purchase_order["id"])

    template_id = await processor.get_complete_template(is_new)
    assert template_id == expected_template_id
    templates_requests = httpx_mock.get_requests(
        method="GET",
        url=(
            f"{test_settings.mpt_api_base_url}/catalog/products/{PRODUCT_ID}"
            f"/templates?limit={rows}&offset=0"
        ),
    )
    assert len(templates_requests) == 1


# -- PurchaseOrderProcessor.send_reset_password --


async def test_send_reset_password_new_user_sends_reset(
    purchase_order: dict[str, Any],
    test_settings: Settings,
    httpx_mock: HTTPXMock,
    order_event_handler: OrderEventHandler,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """`send_reset_password` triggers a password reset for a newly created user."""
    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.mpt_api_base_url}/commerce/orders/{purchase_order['id']}",
        match_params={"select": "subscriptions.lines"},
        json=purchase_order,
    )
    httpx_mock.add_response(
        method="POST",
        url=f"{test_settings.optscale_rest_api_base_url}/restore_password",
        json={"email": "pl@example.com"},
        match_json={"email": "pl@example.com"},
    )
    processor = await order_event_handler.get_processor(object_id=purchase_order["id"])

    with caplog.at_level(logging.INFO):
        await processor.send_reset_password("pl@example.com", is_new=True)
    assert "Employee pl@example.com password reset sent" in caplog.text


async def test_send_reset_password_swallows_reset_failure(
    purchase_order: dict[str, Any],
    test_settings: Settings,
    httpx_mock: HTTPXMock,
    order_event_handler: OrderEventHandler,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """`send_reset_password` logs and swallows a failure raised while sending the reset."""
    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.mpt_api_base_url}/commerce/orders/{purchase_order['id']}",
        match_params={"select": "subscriptions.lines"},
        json=purchase_order,
    )
    processor = await order_event_handler.get_processor(object_id=purchase_order["id"])
    httpx_mock.add_exception(
        httpx.ConnectError("Optscale down"),
        method="POST",
        url=f"{test_settings.optscale_rest_api_base_url}/restore_password",
    )

    with caplog.at_level(logging.ERROR):
        await processor.send_reset_password("pl@example.com", is_new=True)
    assert "Failed to reset password" in caplog.text


async def test_send_reset_password_existing_user_is_noop(
    purchase_order: dict[str, Any],
    test_settings: Settings,
    httpx_mock: HTTPXMock,
    order_event_handler: OrderEventHandler,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """`send_reset_password` does nothing for an existing user."""
    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.mpt_api_base_url}/commerce/orders/{purchase_order['id']}",
        match_params={"select": "subscriptions.lines"},
        json=purchase_order,
    )
    processor = await order_event_handler.get_processor(object_id=purchase_order["id"])

    with caplog.at_level(logging.INFO):
        await processor.send_reset_password("pl@example.com", is_new=False)
    assert httpx_mock.get_requests(method="POST") == []
    assert "No need to send reset password for pl@example.com" in caplog.text


# -- PurchaseOrderProcessor.process --


async def test_purchase_order_process_completes_order(
    purchase_order: dict[str, Any],
    test_settings: Settings,
    httpx_mock: HTTPXMock,
    order_event_handler: OrderEventHandler,
    db_session: AsyncSession,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """`process` runs every step in order and completes an existing-user purchase order."""
    order_id = purchase_order["id"]
    agreement_id = purchase_order["agreement"]["id"]
    rows = test_settings.mpt_api_rows_per_page
    updated_order = copy.deepcopy(purchase_order)
    updated_order["template"]["id"] = "TPL-0001"

    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.mpt_api_base_url}/commerce/orders/{order_id}",
        match_params={"select": "subscriptions.lines"},
        json=purchase_order,
    )
    httpx_mock.add_response(
        method="GET",
        url=(
            f"{test_settings.mpt_api_base_url}/catalog/products/{PRODUCT_ID}"
            f"/templates?limit={rows}&offset=0"
        ),
        json={
            "data": [
                {
                    "id": "TPL-0001",
                    "type": PROCESSING_TEMPLATE_TYPE,
                    "name": PURCHASE_TEMPLATE_NAME,
                    "default": False,
                },
                {
                    "id": "TPL-0006",
                    "type": COMPLETED_TEMPLATE_TYPE,
                    "name": PURCHASE_EXISTING_TEMPLATE_NAME,
                    "default": False,
                },
            ],
            "$meta": {"pagination": {"total": 2}},
        },
    )
    httpx_mock.add_response(
        method="PUT",
        url=f"{test_settings.mpt_api_base_url}/commerce/orders/{order_id}",
        json=updated_order,
        match_json={"template": {"id": "TPL-0001"}},
    )
    expected_parameters = copy.deepcopy(purchase_order["parameters"])
    for parameter in expected_parameters["fulfillment"]:
        if parameter["externalId"] == "isNewUser":
            parameter["value"] = None  # the user already existed
    httpx_mock.add_response(
        method="PUT",
        url=f"{test_settings.mpt_api_base_url}/commerce/orders/{order_id}",
        json=updated_order,
        match_json={"parameters": expected_parameters},
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.optscale_auth_api_base_url}/user_existence",
        match_params={"email": "pl@example.com", "user_info": "true"},
        json={"exists": True, "user_info": {"id": "employee-id"}},
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.mpt_api_base_url}/commerce/agreements/{agreement_id}",
        match_params={"select": "authorization"},
        json={"id": agreement_id, "authorization": {"id": "AUT-3727-1184", "currency": "USD"}},
    )
    httpx_mock.add_response(
        method="POST",
        url=f"{test_settings.api_modifier_base_url}/organizations",
        json={"id": "OPT-ORG-0001"},
        match_json={"org_name": "ACME Inc", "user_id": "employee-id", "currency": "USD"},
    )
    httpx_mock.add_response(
        method="PUT",
        url=f"{test_settings.mpt_api_base_url}/commerce/agreements/{agreement_id}",
        json={"id": agreement_id},
    )
    httpx_mock.add_response(
        method="POST",
        url=f"{test_settings.mpt_api_base_url}/commerce/orders/{order_id}/complete",
        json=updated_order,
        match_json={
            "template": {"id": "TPL-0006"},  # existing user -> PurchaseExisting template
            "parameters": {"fulfillment": [{"externalId": "dueDate", "value": None}]},
        },
    )
    processor = await order_event_handler.get_processor(object_id=order_id)

    with caplog.at_level(logging.INFO):
        result = await processor.process()

    assert result.status is ProcessingStatus.COMPLETE
    assert result.message == f"Order {order_id} has been successfully processed"

    organization = await db_session.scalar(
        select(Organization).where(Organization.operations_external_id == agreement_id)
    )
    assert organization.linked_organization_id == "OPT-ORG-0001"
    assert httpx_mock.get_request(
        method="PUT",
        url=f"{test_settings.mpt_api_base_url}/commerce/agreements/{agreement_id}",
        match_json={"externalIds": {"vendor": organization.id}},
    )
    assert f"Order {order_id} has been completed" in caplog.text
    assert "No need to send reset password for pl@example.com" in caplog.text


async def test_purchase_order_process_new_user_branch(
    purchase_order: dict[str, Any],
    test_settings: Settings,
    httpx_mock: HTTPXMock,
    order_event_handler: OrderEventHandler,
    db_session: AsyncSession,
    caplog: pytest.LogCaptureFixture,
    mocker: MockerFixture,
) -> None:
    """`process` completes with the new-user template and resets the password for new users."""
    order_id = purchase_order["id"]
    agreement_id = purchase_order["agreement"]["id"]
    rows = test_settings.mpt_api_rows_per_page
    generated_password = "a-generated-password"
    mocker.patch(
        "app.events.orders.processing.secrets.token_urlsafe",
        return_value=generated_password,
    )
    for param in purchase_order["parameters"]["fulfillment"]:
        if param["externalId"] == "isNewUser":
            param["value"] = ["Yes"]
    updated_order = copy.deepcopy(purchase_order)
    updated_order["template"]["id"] = "TPL-0001"

    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.mpt_api_base_url}/commerce/orders/{order_id}",
        match_params={"select": "subscriptions.lines"},
        json=purchase_order,
    )
    httpx_mock.add_response(
        method="GET",
        url=(
            f"{test_settings.mpt_api_base_url}/catalog/products/{PRODUCT_ID}"
            f"/templates?limit={rows}&offset=0"
        ),
        json={
            "data": [
                {
                    "id": "TPL-0001",
                    "type": PROCESSING_TEMPLATE_TYPE,
                    "name": PURCHASE_TEMPLATE_NAME,
                    "default": False,
                },
                {
                    "id": "TPL-0005",
                    "type": COMPLETED_TEMPLATE_TYPE,
                    "name": PURCHASE_TEMPLATE_NAME,
                    "default": False,
                },
            ],
            "$meta": {"pagination": {"total": 2}},
        },
    )

    httpx_mock.add_response(
        method="PUT",
        url=f"{test_settings.mpt_api_base_url}/commerce/orders/{order_id}",
        json=updated_order,
        match_json={"template": {"id": "TPL-0001"}},
    )
    expected_parameters = copy.deepcopy(purchase_order["parameters"])
    for parameter in expected_parameters["fulfillment"]:
        if parameter["externalId"] == "isNewUser":
            parameter["value"] = ["Yes"]  # the user was just created
    httpx_mock.add_response(
        method="PUT",
        url=f"{test_settings.mpt_api_base_url}/commerce/orders/{order_id}",
        json=updated_order,
        match_json={"parameters": expected_parameters},
    )
    # The user does not exist yet: create_employee provisions one.
    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.optscale_auth_api_base_url}/user_existence",
        match_params={"email": "pl@example.com", "user_info": "true"},
        json={"exists": False},
    )
    httpx_mock.add_response(
        method="POST",
        url=f"{test_settings.api_modifier_base_url}/users",
        json={"id": "employee-id", "email": "pl@example.com"},
        match_json={
            "email": "pl@example.com",
            "display_name": "PL NN",
            "password": generated_password,
        },
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.mpt_api_base_url}/commerce/agreements/{agreement_id}",
        match_params={"select": "authorization"},
        json={"id": agreement_id, "authorization": {"id": "AUT-3727-1184", "currency": "USD"}},
    )
    httpx_mock.add_response(
        method="POST",
        url=f"{test_settings.api_modifier_base_url}/organizations",
        json={"id": "OPT-ORG-0001"},
        match_json={"org_name": "ACME Inc", "user_id": "employee-id", "currency": "USD"},
    )
    # the vendor external id is the generated organization id, asserted after the call
    httpx_mock.add_response(
        method="PUT",
        url=f"{test_settings.mpt_api_base_url}/commerce/agreements/{agreement_id}",
        json={"id": agreement_id},
    )
    httpx_mock.add_response(
        method="POST",
        url=f"{test_settings.mpt_api_base_url}/commerce/orders/{order_id}/complete",
        json=updated_order,
        match_json={
            "template": {"id": "TPL-0005"},  # new user -> Purchase template
            "parameters": {"fulfillment": [{"externalId": PARAM_DUE_DATE, "value": None}]},
        },
    )
    httpx_mock.add_response(
        method="POST",
        url=f"{test_settings.optscale_rest_api_base_url}/restore_password",
        json={"email": "pl@example.com"},
        match_json={"email": "pl@example.com"},
    )
    processor = await order_event_handler.get_processor(object_id=order_id)

    with caplog.at_level(logging.INFO):
        result = await processor.process()

    assert result.status is ProcessingStatus.COMPLETE
    organization = await db_session.scalar(
        select(Organization).where(Organization.operations_external_id == agreement_id)
    )
    assert organization.linked_organization_id == "OPT-ORG-0001"
    assert httpx_mock.get_request(
        method="PUT",
        url=f"{test_settings.mpt_api_base_url}/commerce/agreements/{agreement_id}",
        match_json={"externalIds": {"vendor": organization.id}},
    )
    assert "Employee created with id employee-id" in caplog.text
    assert "Employee pl@example.com password reset sent" in caplog.text
    assert f"Order {order_id} has been completed" in caplog.text


async def test_purchase_order_process_skips_when_order_moved_to_query(
    purchase_order: dict[str, Any],
    test_settings: Settings,
    httpx_mock: HTTPXMock,
    order_event_handler: OrderEventHandler,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """`process` returns a SKIP result and halts when validation moves the order to querying."""
    order_id = purchase_order["id"]
    rows = test_settings.mpt_api_rows_per_page
    get_ordering_parameter(purchase_order, PARAM_ORGANIZATION_NAME)["value"] = None
    querying_order = copy.deepcopy(purchase_order)
    querying_order["status"] = "Querying"

    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.mpt_api_base_url}/commerce/orders/{order_id}",
        match_params={"select": "subscriptions.lines"},
        json=purchase_order,
    )
    httpx_mock.add_response(
        method="GET",
        url=(
            f"{test_settings.mpt_api_base_url}/catalog/products/{PRODUCT_ID}"
            f"/templates?limit={rows}&offset=0"
        ),
        json={
            "data": [
                {"id": "TPL-0003", "type": QUERYING_TEMPLATE_TYPE, "name": None, "default": True}
            ],
            "$meta": {"pagination": {"total": 1}},
        },
    )
    expected_order = copy.deepcopy(purchase_order)
    expected_parameter = get_ordering_parameter(expected_order, PARAM_ORGANIZATION_NAME)
    expected_parameter["error"] = ERR_ORGANIZATION_NAME.to_dict()
    expected_parameter["constraints"] = {"hidden": False, "required": True}

    httpx_mock.add_response(
        method="PUT",
        url=f"{test_settings.mpt_api_base_url}/commerce/orders/{order_id}",
        json=purchase_order,
        match_json={"parameters": expected_order["parameters"]},
    )
    httpx_mock.add_response(
        method="POST",
        url=f"{test_settings.mpt_api_base_url}/commerce/orders/{order_id}/query",
        json=querying_order,
        match_json={"template": {"id": "TPL-0003"}},
    )
    processor = await order_event_handler.get_processor(object_id=order_id)

    with caplog.at_level(logging.INFO):
        result = await processor.process()

    assert result.status is ProcessingStatus.SKIP
    assert result.severity == "Info"
    assert result.message == f"Order {order_id} parameters are missing or invalid. Order Skipped."
    # processing halts right after validation: no employee is created, no order completed
    assert (
        httpx_mock.get_request(
            method="GET", url=f"{test_settings.optscale_auth_api_base_url}/user_existence"
        )
        is None
    )
    assert (
        httpx_mock.get_request(
            method="POST",
            url=f"{test_settings.mpt_api_base_url}/commerce/orders/{order_id}/complete",
        )
        is None
    )
    assert f"{order_id}: ordering parameters are invalid, move to querying" in caplog.text


@freeze_time("2024-12-01")
async def test_purchase_order_process_reschedules_before_due_date(
    purchase_order: dict[str, Any],
    test_settings: Settings,
    httpx_mock: HTTPXMock,
    order_event_handler: OrderEventHandler,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """`process` returns RESCHEDULE when an error occurs and the due date has not been reached."""
    # The factory order carries a due date of 2025-01-01.
    order_id = purchase_order["id"]
    rows = test_settings.mpt_api_rows_per_page

    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.mpt_api_base_url}/commerce/orders/{order_id}",
        match_params={"select": "subscriptions.lines"},
        json=purchase_order,
    )
    httpx_mock.add_response(
        method="GET",
        url=(
            f"{test_settings.mpt_api_base_url}/catalog/products/{PRODUCT_ID}"
            f"/templates?limit={rows}&offset=0"
        ),
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        json={"errors": {"templates": "boom"}},
    )
    processor = await order_event_handler.get_processor(object_id=order_id)

    with caplog.at_level(logging.ERROR):
        result = await processor.process()

    assert result.status is ProcessingStatus.RESCHEDULE
    assert result.severity == "Warning"
    assert result.message is not None
    assert f"An error occurred while processing the order {order_id}" in result.message
    assert "HTTPStatusError" in result.message
    assert httpx_mock.get_requests(method="POST") == []
    assert f"{order_id}: order processing failed." in caplog.text


async def test_change_order_process_fail(
    test_settings: Settings,
    httpx_mock: HTTPXMock,
    order_event_handler: OrderEventHandler,
    caplog: pytest.LogCaptureFixture,
    change_order: dict[str, Any],
) -> None:
    """`process` fails a Change order because the product does not support that order type."""
    order_id = change_order["id"]
    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.mpt_api_base_url}/commerce/orders/{order_id}",
        match_params={"select": "subscriptions.lines"},
        json=change_order,
    )
    httpx_mock.add_response(
        method="POST",
        url=f"{test_settings.mpt_api_base_url}/commerce/orders/{order_id}/fail",
        json=change_order,
        match_json={"statusNotes": ERR_ORDER_TYPE_NOT_SUPPORTED.to_dict(order_type="Change")},
    )
    with caplog.at_level(logging.INFO):
        processor = await order_event_handler.get_processor(object_id=order_id)
        result = await processor.process()

    assert result.status is ProcessingStatus.COMPLETE
    assert result.severity == "Warning"
    assert result.message == "Change orders are not supported."
    assert "ORDER TYPE: Change" in caplog.text
    assert "Change Order processing failed." not in caplog.text


@freeze_time("2026-08-11")
async def test_change_order_process_handles_a_malformed_order(
    change_order: dict[str, Any],
    test_settings: Settings,
    httpx_mock: HTTPXMock,
    order_event_handler: OrderEventHandler,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """An order missing its `type` key is rescheduled with a traceback, not propagated."""
    change_order = set_due_date(change_order, date(2026, 12, 1))
    order_id = change_order["id"]
    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.mpt_api_base_url}/commerce/orders/{order_id}",
        match_params={"select": "subscriptions.lines"},
        json=change_order,
    )
    processor = await order_event_handler.get_processor(object_id=order_id)
    processor.order = {key: value for key, value in change_order.items() if key != "type"}

    with caplog.at_level(logging.ERROR):
        result = await processor.process()

    assert result.status is ProcessingStatus.RESCHEDULE
    assert result.severity == "Warning"
    assert result.message is not None
    assert f"An error occurred while processing the order {order_id}" in result.message
    assert f"{order_id}: order processing failed." in caplog.text
    assert "KeyError" in caplog.text
    # the order is never failed: the payload could not even be built
    assert httpx_mock.get_requests(method="POST") == []


async def test_purchase_order_process_cancels_when_no_due_date(
    purchase_order: dict[str, Any],
    test_settings: Settings,
    httpx_mock: HTTPXMock,
    order_event_handler: OrderEventHandler,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """`process` fails the order and returns CANCEL when an error occurs and no due date is set."""
    order_id = purchase_order["id"]
    for param in purchase_order["parameters"]["fulfillment"]:
        if param["externalId"] == PARAM_DUE_DATE:
            param["value"] = None

    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.mpt_api_base_url}/commerce/orders/{order_id}",
        match_params={"select": "subscriptions.lines"},
        json=purchase_order,
    )
    httpx_mock.add_response(
        method="PUT",
        url=f"{test_settings.mpt_api_base_url}/commerce/orders/{order_id}",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        json={"errors": {"parameters": "boom"}},
    )
    httpx_mock.add_response(
        method="POST",
        url=f"{test_settings.mpt_api_base_url}/commerce/orders/{order_id}/fail",
        json=purchase_order,
        match_json={"statusNotes": ERR_DUE_DATE_NOT_SET.to_dict()},
    )
    processor = await order_event_handler.get_processor(object_id=order_id)

    with caplog.at_level(logging.ERROR):
        result = await processor.process()

    assert result.status is ProcessingStatus.CANCEL
    assert result.severity == "Error"
    assert result.message == ERR_DUE_DATE_NOT_SET.message
    assert f"{order_id}: order processing failed." in caplog.text


@freeze_time("2025-06-01")
async def test_purchase_order_process_fails_when_due_date_reached(
    purchase_order: dict[str, Any],
    test_settings: Settings,
    httpx_mock: HTTPXMock,
    order_event_handler: OrderEventHandler,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """`process` fails the order and returns COMPLETE when an error occurs past the due date."""
    order_id = purchase_order["id"]
    rows = test_settings.mpt_api_rows_per_page
    # The factory order carries a due date of 2025-01-01.
    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.mpt_api_base_url}/commerce/orders/{order_id}",
        match_params={"select": "subscriptions.lines"},
        json=purchase_order,
    )
    httpx_mock.add_response(
        method="GET",
        url=(
            f"{test_settings.mpt_api_base_url}/catalog/products/{PRODUCT_ID}"
            f"/templates?limit={rows}&offset=0"
        ),
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        json={"errors": {"templates": "boom"}},
    )
    httpx_mock.add_response(
        method="POST",
        url=f"{test_settings.mpt_api_base_url}/commerce/orders/{order_id}/fail",
        json=purchase_order,
        match_json={"statusNotes": ERR_DUE_DATE_IS_REACHED.to_dict(due_date="2025-01-01")},
    )
    processor = await order_event_handler.get_processor(object_id=order_id)

    with caplog.at_level(logging.ERROR):
        result = await processor.process()

    assert result.status is ProcessingStatus.COMPLETE
    assert result.severity == "Error"
    assert f"{order_id}: order processing failed." in caplog.text


# # TerminateOrderProcessor
async def test_terminated_order_process_completes_order(
    terminate_order: dict[str, Any],
    test_settings: Settings,
    httpx_mock: HTTPXMock,
    order_event_handler: OrderEventHandler,
    db_session: AsyncSession,
) -> None:
    """`process` runs every step in order and completes an existing-user purchase order."""
    order_id = terminate_order["id"]
    rows = test_settings.mpt_api_rows_per_page
    agreement_id = terminate_order["agreement"]["id"]

    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.mpt_api_base_url}/commerce/orders/{order_id}",
        match_params={"select": "subscriptions.lines"},
        json=terminate_order,
    )
    processor = await order_event_handler.get_processor(object_id=order_id)

    organization = await OrganizationHandler(db_session).create(
        Organization(
            name="ACME Inc",
            currency="USD",
            billing_currency="USD",
            operations_external_id=terminate_order["agreement"]["id"],
            linked_organization_id="OPT-ORG-0001",
            status=OrganizationStatus.ACTIVE,
        )
    )
    owner = await AccountHandler(db_session).create(
        obj=Account(
            type=AccountType.AFFILIATE,
            name="AWS",
            external_id="EXT-ID",
            status=AccountStatus.ACTIVE,
        )
    )

    ent_1 = await EntitlementHandler(db_session).create(
        obj=Entitlement(
            name="Entitlement 1",
            affiliate_external_id="EXTERNAL_ID_1",
            datasource_id="ds_1",
            owner=owner,
            status=EntitlementStatus.ACTIVE,
            redeemed_by=organization,
        )
    )
    ent_2 = await EntitlementHandler(db_session).create(
        obj=Entitlement(
            name="Entitlement 2",
            affiliate_external_id="EXTERNAL_ID_2",
            datasource_id="ds_2",
            owner=owner,
            status=EntitlementStatus.ACTIVE,
            redeemed_by=organization,
        )
    )
    httpx_mock.add_response(
        method="GET",
        url=(
            f"{test_settings.mpt_api_base_url}/catalog/products/{PRODUCT_ID}"
            f"/templates?limit={rows}&offset=0"
        ),
        json={
            "data": [
                {
                    "id": "TPL-1234-5678-0001",
                    "type": COMPLETED_TEMPLATE_TYPE,
                    "name": TERMINATE_TEMPLATE_NAME,
                    "default": True,
                }
            ],
            "$meta": {"pagination": {"total": 1}},
        },
    )

    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.mpt_api_base_url}/commerce/agreements/{agreement_id}",
        json={
            "externalIds": {"client": "", "vendor": organization.id},
        },
    )

    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.optscale_rest_api_base_url}/organizations/{organization.linked_organization_id}",
        json={
            "deleted_at": 0,
            "created_at": 1784036037,
            "id": "9939c1a3-fd82-4cd4-b749-5e85cf69b606",
            "name": "SPIDERMAN3232",
            "pool_id": "7a496040-46e2-4011-9c76-66a9830c595b",
            "is_demo": False,
            "currency": "USD",
            "cleaned_at": 0,
            "disabled": False,
        },
    )
    httpx_mock.add_response(
        method="PATCH",
        url=f"{test_settings.optscale_rest_api_base_url}/organizations/{organization.linked_organization_id}",
        json={"disabled": True},
        match_json={"disabled": True},
    )
    httpx_mock.add_response(
        method="POST",
        url=f"{test_settings.mpt_api_base_url}/commerce/orders/{order_id}/complete",
        json=terminate_order,
        match_json={
            "template": {"id": "TPL-1234-5678-0001"},
            "parameters": {"fulfillment": [{"externalId": PARAM_DUE_DATE, "value": None}]},
        },
    )

    result = await processor.process()

    assert result.status is ProcessingStatus.COMPLETE
    assert result.severity == "Info"
    assert result.message == f"The Organization {organization.id} was successfully suspended."

    await db_session.refresh(organization)
    assert organization.status == OrganizationStatus.TERMINATED
    assert organization.terminated_at is not None

    for entitlement in (ent_1, ent_2):
        await db_session.refresh(entitlement)
        assert entitlement.status == EntitlementStatus.TERMINATED
        assert entitlement.terminated_at is not None
        assert entitlement.terminated_by_id is None

    replacements = (
        await db_session.scalars(
            select(Entitlement).where(
                Entitlement.status == EntitlementStatus.NEW,
                Entitlement.redeemed_by_id.is_(None),
                Entitlement.owner_id == owner.id,
                Entitlement.datasource_id.in_(["ds_1", "ds_2"]),
            )
        )
    ).all()
    assert len(replacements) == 2
    assert {r.affiliate_external_id for r in replacements} == {"EXTERNAL_ID_1", "EXTERNAL_ID_2"}


async def test_terminate_cancels_when_order_has_no_due_date_parameter(
    terminate_order: dict[str, Any],
    test_settings: Settings,
    httpx_mock: HTTPXMock,
    order_event_handler: OrderEventHandler,
) -> None:
    pass
    """The terminate flow cancels when the order declares no 'dueDate` parameter."""
    order_id = terminate_order["id"]
    terminate_order["parameters"]["fulfillment"] = [
        param
        for param in terminate_order["parameters"]["fulfillment"]
        if param["externalId"] != PARAM_DUE_DATE
    ]
    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.mpt_api_base_url}/commerce/orders/{order_id}",
        match_params={"select": "subscriptions.lines"},
        json=terminate_order,
    )
    httpx_mock.add_response(
        method="POST",
        url=f"{test_settings.mpt_api_base_url}/commerce/orders/{order_id}/fail",
        json={"statusNotes": ERR_DUE_DATE_NOT_SET.to_dict()},
        match_json={"statusNotes": ERR_DUE_DATE_NOT_SET.to_dict()},
    )

    processor = await order_event_handler.get_processor(object_id=order_id)
    result = await processor.process()
    assert result.status is ProcessingStatus.CANCEL
    assert result.severity == "Error"
    assert result.message == ERR_DUE_DATE_NOT_SET.message
    # the order is never updated and no organization is suspended
    assert (
        httpx_mock.get_request(
            method="PUT", url=f"{test_settings.mpt_api_base_url}/commerce/orders/{order_id}"
        )
        is None
    )
    assert httpx_mock.get_requests(method="PATCH") == []


async def test_terminated_order_skip_suspend_when_optscale_org_is_disabled(
    terminate_order: dict[str, Any],
    test_settings: Settings,
    httpx_mock: HTTPXMock,
    order_event_handler: OrderEventHandler,
    db_session: AsyncSession,
) -> None:
    """`process` completes without suspending when the OptScale organization is already disabled."""
    order_id = terminate_order["id"]
    rows = test_settings.mpt_api_rows_per_page
    agreement_id = terminate_order["agreement"]["id"]
    organization = await OrganizationHandler(db_session).create(
        Organization(
            name="ACME Inc",
            currency="USD",
            billing_currency="USD",
            operations_external_id=agreement_id,
            linked_organization_id="OPT-ORG-0001",
            status=OrganizationStatus.ACTIVE,
        )
    )
    optscale_url = (
        f"{test_settings.optscale_rest_api_base_url}"
        f"/organizations/{organization.linked_organization_id}"
    )

    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.mpt_api_base_url}/commerce/orders/{order_id}",
        match_params={"select": "subscriptions.lines"},
        json=terminate_order,
    )
    httpx_mock.add_response(
        method="GET",
        url=(
            f"{test_settings.mpt_api_base_url}/catalog/products/{PRODUCT_ID}"
            f"/templates?limit={rows}&offset=0"
        ),
        json={
            "data": [
                {
                    "id": "TPL-1234-5678-0001",
                    "type": COMPLETED_TEMPLATE_TYPE,
                    "name": TERMINATE_TEMPLATE_NAME,
                    "default": True,
                }
            ],
            "$meta": {"pagination": {"total": 1}},
        },
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.mpt_api_base_url}/commerce/agreements/{agreement_id}",
        json={"externalIds": {"client": "", "vendor": organization.id}},
    )
    httpx_mock.add_response(
        method="GET",
        url=optscale_url,
        json={
            "deleted_at": 0,
            "created_at": 1784036037,
            "id": "9939c1a3-fd82-4cd4-b749-5e85cf69b606",
            "name": "SPIDERMAN3232",
            "pool_id": "7a496040-46e2-4011-9c76-66a9830c595b",
            "is_demo": False,
            "currency": "USD",
            "cleaned_at": 0,
            "disabled": True,
        },
    )
    httpx_mock.add_response(
        method="POST",
        url=f"{test_settings.mpt_api_base_url}/commerce/orders/{order_id}/complete",
        json=terminate_order,
        match_json={
            "template": {"id": "TPL-1234-5678-0001"},
            "parameters": {"fulfillment": [{"externalId": PARAM_DUE_DATE, "value": None}]},
        },
    )
    processor = await order_event_handler.get_processor(object_id=order_id)

    result = await processor.process()

    assert result.status is ProcessingStatus.COMPLETE
    assert result.severity == "Warning"
    assert result.message == f"The Organization {organization.id} was already terminated."
    assert httpx_mock.get_request(method="GET", url=optscale_url) is not None
    assert httpx_mock.get_requests(method="PATCH") == []
    await db_session.refresh(organization)
    assert organization.status == OrganizationStatus.ACTIVE
    assert organization.terminated_at is None


async def test_terminated_order_cancel_when_organization_not_found(
    terminate_order: dict[str, Any],
    test_settings: Settings,
    httpx_mock: HTTPXMock,
    order_event_handler: OrderEventHandler,
) -> None:
    """The terminate flow cancels when the agreement points at an unknown organization."""
    order_id = terminate_order["id"]
    agreement_id = terminate_order["agreement"]["id"]
    # no organization row is created: the repository lookup finds nothing
    unknown_organization_id = "FORG-8077-2461-7285"

    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.mpt_api_base_url}/commerce/orders/{order_id}",
        match_params={"select": "subscriptions.lines"},
        json=terminate_order,
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.mpt_api_base_url}/commerce/agreements/{agreement_id}",
        json={"externalIds": {"client": "", "vendor": unknown_organization_id}},
    )
    processor = await order_event_handler.get_processor(object_id=order_id)

    result = await processor.process()

    assert result.status is ProcessingStatus.CANCEL
    assert result.severity == "Error"
    assert result.message == (
        f"The organization {unknown_organization_id} linked to agreement {agreement_id}"
        f" was not found."
    )
    # the flow stops before OptScale is contacted and before the order is completed
    assert httpx_mock.get_requests(method="POST") == []
    assert httpx_mock.get_requests(method="PATCH") == []
    assert [str(request.url) for request in httpx_mock.get_requests()] == [
        f"{test_settings.mpt_api_base_url}/commerce/orders/{order_id}?select=subscriptions.lines",
        f"{test_settings.mpt_api_base_url}/commerce/agreements/{agreement_id}",
    ]


async def test_terminated_order_cancel_when_organization_not_linked(
    terminate_order: dict[str, Any],
    test_settings: Settings,
    httpx_mock: HTTPXMock,
    order_event_handler: OrderEventHandler,
    db_session: AsyncSession,
) -> None:
    """The terminate flow cancels when the organization has no FinOps for Cloud link."""
    order_id = terminate_order["id"]
    agreement_id = terminate_order["agreement"]["id"]
    organization = await OrganizationHandler(db_session).create(
        Organization(
            name="ACME Inc",
            currency="USD",
            billing_currency="USD",
            operations_external_id=agreement_id,
            linked_organization_id=None,
            status=OrganizationStatus.ACTIVE,
        )
    )

    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.mpt_api_base_url}/commerce/orders/{order_id}",
        match_params={"select": "subscriptions.lines"},
        json=terminate_order,
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.mpt_api_base_url}/commerce/agreements/{agreement_id}",
        json={"externalIds": {"client": "", "vendor": organization.id}},
    )
    processor = await order_event_handler.get_processor(object_id=order_id)

    result = await processor.process()

    assert result.status is ProcessingStatus.CANCEL
    assert result.severity == "Error"
    assert result.message == (
        f"The organization {organization.id} is not linked to a FinOps for Cloud Organization."
    )
    # the flow stops before OptScale is contacted and before the order is completed
    assert httpx_mock.get_requests(method="POST") == []
    assert httpx_mock.get_requests(method="PATCH") == []
    assert [str(request.url) for request in httpx_mock.get_requests()] == [
        f"{test_settings.mpt_api_base_url}/commerce/orders/{order_id}?select=subscriptions.lines",
        f"{test_settings.mpt_api_base_url}/commerce/agreements/{agreement_id}",
    ]
    await db_session.refresh(organization)
    assert organization.status == OrganizationStatus.ACTIVE


@freeze_time("2026-08-06")
async def test_terminated_order_reschedule_before_due_date_is_reached(
    terminate_order: dict[str, Any],
    test_settings: Settings,
    httpx_mock: HTTPXMock,
    order_event_handler: OrderEventHandler,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """`process` returns RESCHEDULE when an error occurs and the due date has not been reached."""
    terminate_order = set_due_date(terminate_order, date(2026, 12, 12))
    order_id = terminate_order["id"]
    agreement_id = terminate_order["agreement"]["id"]

    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.mpt_api_base_url}/commerce/orders/{order_id}",
        match_params={"select": "subscriptions.lines"},
        json=terminate_order,
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.mpt_api_base_url}/commerce/agreements/{agreement_id}",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        json={"errors": {"agreement": "big error"}},
    )
    processor = await order_event_handler.get_processor(object_id=order_id)

    with caplog.at_level(logging.ERROR):
        result = await processor.process()

    assert result.status is ProcessingStatus.RESCHEDULE
    assert result.severity == "Warning"
    assert result.message is not None
    assert f"An error occurred while processing the order {order_id}" in result.message
    assert "HTTPStatusError" in result.message
    # the order is neither failed nor completed and no organization is suspended
    assert httpx_mock.get_requests(method="POST") == []
    assert httpx_mock.get_requests(method="PATCH") == []
    assert f"{order_id}: order processing failed." in caplog.text


@freeze_time("2026-08-06")
async def test_terminated_order_fails_when_before_due_date_is_reached(
    terminate_order: dict[str, Any],
    test_settings: Settings,
    httpx_mock: HTTPXMock,
    order_event_handler: OrderEventHandler,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """`process` fails the order and returns COMPLETE when an error occurs past the due date."""
    terminate_order = set_due_date(terminate_order, date(2026, 7, 12))
    order_id = terminate_order["id"]
    agreement_id = terminate_order["agreement"]["id"]

    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.mpt_api_base_url}/commerce/orders/{order_id}",
        match_params={"select": "subscriptions.lines"},
        json=terminate_order,
    )
    # the marketplace errors while the agreement is fetched
    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.mpt_api_base_url}/commerce/agreements/{agreement_id}",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        json={"errors": {"agreement": "big error"}},
    )
    httpx_mock.add_response(
        method="POST",
        url=f"{test_settings.mpt_api_base_url}/commerce/orders/{order_id}/fail",
        json=terminate_order,
        match_json={"statusNotes": ERR_DUE_DATE_IS_REACHED.to_dict(due_date="2026-07-12")},
    )
    processor = await order_event_handler.get_processor(object_id=order_id)

    with caplog.at_level(logging.ERROR):
        result = await processor.process()

    assert result.status is ProcessingStatus.COMPLETE
    assert result.severity == "Error"
    assert result.message == ERR_DUE_DATE_IS_REACHED.to_dict(due_date="2026-07-12")["message"]
    # the order is never completed and no organization is suspended
    assert (
        httpx_mock.get_request(
            method="POST",
            url=f"{test_settings.mpt_api_base_url}/commerce/orders/{order_id}/complete",
        )
        is None
    )
    assert httpx_mock.get_requests(method="PATCH") == []
    assert f"{order_id}: order processing failed." in caplog.text


@freeze_time("2026-08-06")
async def test_terminated_order_cancel_when_no_due_date_is_set(
    terminate_order: dict[str, Any],
    test_settings: Settings,
    httpx_mock: HTTPXMock,
    order_event_handler: OrderEventHandler,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """`process` fails the order and returns CANCEL when an error occurs and no due date is set."""
    terminate_order = set_due_date(terminate_order, None)
    order_id = terminate_order["id"]
    agreement_id = terminate_order["agreement"]["id"]

    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.mpt_api_base_url}/commerce/orders/{order_id}",
        match_params={"select": "subscriptions.lines"},
        json=terminate_order,
    )
    httpx_mock.add_response(
        method="PUT",
        url=f"{test_settings.mpt_api_base_url}/commerce/orders/{order_id}",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        json={"errors": {"parameters": "big error"}},
    )
    httpx_mock.add_response(
        method="POST",
        url=f"{test_settings.mpt_api_base_url}/commerce/orders/{order_id}/fail",
        json=terminate_order,
        match_json={"statusNotes": ERR_DUE_DATE_NOT_SET.to_dict()},
    )
    processor = await order_event_handler.get_processor(object_id=order_id)

    with caplog.at_level(logging.ERROR):
        result = await processor.process()

    assert result.status is ProcessingStatus.CANCEL
    assert result.severity == "Error"
    assert result.message == ERR_DUE_DATE_NOT_SET.message
    # the flow stops before the agreement is read, nothing is suspended or completed
    assert (
        httpx_mock.get_request(
            method="GET",
            url=f"{test_settings.mpt_api_base_url}/commerce/agreements/{agreement_id}",
        )
        is None
    )
    assert (
        httpx_mock.get_request(
            method="POST",
            url=f"{test_settings.mpt_api_base_url}/commerce/orders/{order_id}/complete",
        )
        is None
    )
    assert httpx_mock.get_requests(method="PATCH") == []
    assert f"{order_id}: order processing failed." in caplog.text
