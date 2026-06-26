import copy
import logging
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from pytest_mock import MockerFixture

from app.fulfilment import templates as templates_module
from app.fulfilment.constants import PROCESSING_TEMPLATE_TYPE, PURCHASE_TEMPLATE_NAME
from app.fulfilment.templates import (
    get_product_template_id,
    set_template,
    start_processing_order_template,
)

PRODUCT_ID = "PRD-4141-4379"

PRODUCT_TEMPLATES = [
    {"id": "TPL-0001", "type": PROCESSING_TEMPLATE_TYPE, "name": "Purchase", "default": False},
    {"id": "TPL-0002", "type": PROCESSING_TEMPLATE_TYPE, "name": "Standard", "default": True},
    {"id": "TPL-0003", "type": "OrderQuerying", "name": "Querying", "default": True},
]


@pytest.fixture(autouse=True)
def clear_template_cache():
    # template_cache is module-level global state, so it leaks between tests unless reset.
    templates_module.template_cache.clear()
    yield
    templates_module.template_cache.clear()


@pytest.fixture(autouse=True)
def mock_get_settings(mocker: MockerFixture) -> None:
    mocker.patch(
        "app.fulfilment.templates.get_settings",
        return_value=SimpleNamespace(mpt_product_id=PRODUCT_ID),
    )


async def _templates_gen():
    for template in PRODUCT_TEMPLATES:
        yield template


def test_set_template_success(order_factory):
    order = order_factory(
        order_type="Purchase",
        status="Processing",
        product_id="PRD-4141-4379",
        product_name="SoftwareOne FinOps for Cloud",
    )
    update_order = set_template(order, "TPL-1234-5678-0001")
    assert update_order["template"]["id"] == "TPL-1234-5678-0001"


def test_set_template_no_template_id(order_factory):
    order = order_factory(
        order_type="Purchase",
        status="Processing",
        product_id="PRD-4141-4379",
        product_name="SoftwareOne FinOps for Cloud",
    )
    with pytest.raises(ValueError):
        set_template(order, "")


def test_set_template_malformed_order(order_factory):
    with pytest.raises(KeyError):
        set_template({}, "TPL-1234-5678-0001")


async def test_get_product_template_returns_specific_by_name(mocker):
    # cache is cleared by the autouse fixture, but be explicit since we assert call count
    ext_client = AsyncMock()
    mocked_call = mocker.patch.object(
        ext_client,
        "get_templates_by_product_id",
        Mock(side_effect=lambda **_: _templates_gen()),
    )
    template_id = await get_product_template_id(ext_client, PROCESSING_TEMPLATE_TYPE, "Purchase")
    assert template_id == "TPL-0001"
    mocked_call.assert_called_once_with(product_id=PRODUCT_ID)


async def test_get_product_template_falls_back_to_default(mocker):
    ext_client = AsyncMock()
    mocker.patch.object(
        ext_client,
        "get_templates_by_product_id",
        Mock(side_effect=lambda **_: _templates_gen()),
    )
    template_id = await get_product_template_id(
        ext_client, PROCESSING_TEMPLATE_TYPE, "DoesNotExist"
    )

    assert template_id == "TPL-0002"


async def test_get_product_template_returns_default_when_name_is_none(mocker):
    ext_client = AsyncMock()
    mocker.patch.object(
        ext_client,
        "get_templates_by_product_id",
        Mock(side_effect=lambda **_: _templates_gen()),
    )
    template_id = await get_product_template_id(ext_client, "OrderQuerying", None)

    assert template_id == "TPL-0003"


async def test_get_product_template_uses_cache_without_http_call(mocker):
    templates_module.template_cache[(PROCESSING_TEMPLATE_TYPE, PURCHASE_TEMPLATE_NAME)] = (
        "TPL-CACHED"
    )
    templates_module.template_cache[(PROCESSING_TEMPLATE_TYPE, None)] = "TPL-DEFAULT"
    ext_client = AsyncMock()
    mocked_call = mocker.patch.object(
        ext_client,
        "get_templates_by_product_id",
        Mock(side_effect=lambda **_: _templates_gen()),
    )
    template_id = await get_product_template_id(
        ext_client, PROCESSING_TEMPLATE_TYPE, PURCHASE_TEMPLATE_NAME
    )

    assert template_id == "TPL-CACHED"
    mocked_call.assert_not_called()


async def test_start_processing_order_template(mocker, order_factory, caplog):
    ext_client = AsyncMock()
    order = order_factory(
        order_type="Purchase",
        status="Processing",
        product_id="PRD-4141-4379",
        product_name="SoftwareOne FinOps for Cloud",
        template={
            "id": "TPL-1234-1234-0001",
            "name": "CurrentTemplate",
            "revision": 1,
        },
    )
    mocker.patch.object(
        ext_client,
        "get_templates_by_product_id",
        Mock(side_effect=lambda **_: _templates_gen()),
    )

    updated_order = copy.deepcopy(order)
    updated_order["template"]["id"] = "TPL-0001"
    mocker.patch.object(ext_client, "update_order", return_value=updated_order)
    with caplog.at_level(logging.INFO):
        response = await start_processing_order_template(ext_client, order)
        assert response == updated_order
        assert f"{order['id']}: processing template set to Purchase (TPL-0001)" in caplog.text


async def test_start_processing_order_template_with_same_template(mocker, order_factory, caplog):
    ext_client = AsyncMock()
    order = order_factory(
        order_type="Purchase",
        status="Processing",
        product_id="PRD-4141-4379",
        product_name="SoftwareOne FinOps for Cloud",
        template={
            "id": "TPL-0001",
            "name": "Purchase",
            "revision": 1,
        },
    )
    mocker.patch.object(
        ext_client,
        "get_templates_by_product_id",
        Mock(side_effect=lambda **_: _templates_gen()),
    )

    mocker.patch.object(ext_client, "update_order", return_value=order)
    with caplog.at_level(logging.INFO):
        response = await start_processing_order_template(ext_client, order)
        assert response == order
        assert f"{order['id']}: processing template is ok, continue" in caplog.text
