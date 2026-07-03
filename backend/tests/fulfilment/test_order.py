import copy
import logging
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from pytest_mock import MockerFixture

from app.api_clients.optscale import UserDoesNotExist
from app.conf import Settings
from app.db.handlers import OrganizationHandler
from app.db.models import Organization
from app.fulfilment.constants import (
    COMPLETED_TEMPLATE_TYPE,
    ORDER_TYPE_TERMINATE,
    PROCESSING_TEMPLATE_TYPE,
    PURCHASE_EXISTING_TEMPLATE_NAME,
    PURCHASE_TEMPLATE_NAME,
    QUERYING_TEMPLATE_TYPE,
)
from app.fulfilment.exceptions import (
    OrderMovedToQuery,
    OrderNotValidError,
    UnsupportedOrderTypeError,
)
from app.fulfilment.processing import OrderProcessor, OrderProcessorFactory, PurchaseOrderProcessor

PRODUCT_ID = "PRD-4141-4379"


PRODUCT_TEMPLATES = [
    {"id": "TPL-0001", "type": PROCESSING_TEMPLATE_TYPE, "name": "Purchase", "default": False},
    {"id": "TPL-0002", "type": PROCESSING_TEMPLATE_TYPE, "name": "Standard", "default": True},
    {"id": "TPL-0003", "type": QUERYING_TEMPLATE_TYPE, "name": None, "default": True},
    {"id": "TPL-0004", "type": COMPLETED_TEMPLATE_TYPE, "name": None, "default": False},
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


@pytest.fixture(autouse=True)
def mock_get_settings(mocker: MockerFixture) -> None:
    mocker.patch(
        "app.conf.get_settings",
        return_value=SimpleNamespace(mpt_product_id=PRODUCT_ID),
    )


async def _templates_gen():
    for template in PRODUCT_TEMPLATES:
        yield template


@pytest.fixture
def make_processor(order_factory, test_settings):
    def _make(order):
        return OrderProcessor(
            api_modifier_client=AsyncMock(),
            client=AsyncMock(),
            ext_client=AsyncMock(),
            optscale_auth_client=AsyncMock(),
            optscale_client=AsyncMock(),
            organization_repo=AsyncMock(),
            order=order,
            settings=test_settings,
        )

    return _make


def _make_factory(order: dict, settings) -> OrderProcessorFactory:
    client = AsyncMock()
    client.get_order = AsyncMock(return_value=order)
    return OrderProcessorFactory(
        api_modifier_client=AsyncMock(),
        client=client,
        ext_client=AsyncMock(),
        optscale_auth_client=AsyncMock(),
        optscale_client=AsyncMock(),
        organization_repo=AsyncMock(),
        settings=settings,
    )


# -- get_order_type_processor --


async def test_get_order_type_processor(order_factory, test_settings: Settings, make_processor):
    order = order_factory(
        order_type="Purchase",
        status="Processing",
        product_id="PRD-4141-4379",
        product_name="SoftwareOne FinOps for Cloud",
    )
    factory = _make_factory(order, test_settings)
    processor = await factory.get_order_type_processor(order_id=order["id"])
    assert processor.order == order
    assert isinstance(processor, PurchaseOrderProcessor)
    factory.client.get_order.assert_awaited_once_with(order["id"])


async def test_get_order_type_processor_raises_for_unsupported_type(
    order_factory, test_settings: Settings
):
    order = order_factory(
        order_type=ORDER_TYPE_TERMINATE,  # not registered in PROCESSOR_BY_TYPE
        status="Processing",
        product_id=PRODUCT_ID,
        product_name="SoftwareOne FinOps for Cloud",
    )
    factory = _make_factory(order, test_settings)
    with pytest.raises(UnsupportedOrderTypeError) as exc_info:
        await factory.get_order_type_processor(order_id=order["id"])
    assert exc_info.value.order_type == ORDER_TYPE_TERMINATE
    factory.client.get_order.assert_awaited_once_with(order["id"])


# -- OrderProcessor.set_template --


async def test_set_template_assigns_id_and_returns_copy(order_factory, make_processor):
    order = order_factory(
        order_type="Purchase",
        status="Processing",
        product_id="PRD-4141-4379",
        product_name="SoftwareOne FinOps for Cloud",
    )
    processor = make_processor(order)
    result = processor.set_template(order=order, template_id="TPL-1234-5678-0001")
    assert processor.order is result
    assert result["template"]["id"] == "TPL-1234-5678-0001"
    assert order["template"]["id"] == "TPL-1234-1234-4321"
    assert order["template"]["name"] == "Default Template"


async def test_set_template_raises_when_template_id_is_missing(order_factory, make_processor):
    order = order_factory(
        order_type="Purchase",
        status="Processing",
        product_id="PRD-4141-4379",
        product_name="SoftwareOne FinOps for Cloud",
    )
    processor = make_processor(order)
    with pytest.raises(ValueError, match="Template id is required"):
        processor.set_template(order=order, template_id="")


async def test_set_template_raises_when_order_malformed(order_factory, make_processor):
    order = order_factory(
        order_type="Purchase",
        status="Processing",
        product_id="PRD-4141-4379",
        product_name="SoftwareOne FinOps for Cloud",
    )
    order.pop("template", None)
    processor = make_processor(order)
    with pytest.raises(KeyError, match="Order is malformed"):
        processor.set_template(order=order, template_id="TPL-1234-5678-0001")


# -- get_product_template_id / fetch_product_templates  --


async def test_get_product_template_returns_specific_by_name(mocker, order_factory, make_processor):
    order = order_factory(
        order_type="Purchase",
        status="Processing",
        product_id="PRD-4141-4379",
        product_name="SoftwareOne FinOps for Cloud",
    )
    processor = make_processor(order)
    mocker.patch.object(
        processor.ext_client,
        "get_templates_by_product_id",
        Mock(side_effect=lambda **_: _templates_gen()),
    )
    template_id = await processor.get_product_template_id(PROCESSING_TEMPLATE_TYPE, "Purchase")
    assert template_id == "TPL-0001"
    processor.ext_client.get_templates_by_product_id.assert_called_once_with(product_id=PRODUCT_ID)


async def test_get_product_template_fails_back_to_default(mocker, order_factory, make_processor):
    order = order_factory(
        order_type="Purchase",
        status="Processing",
        product_id="PRD-4141-4379",
        product_name="SoftwareOne FinOps for Cloud",
    )
    processor = make_processor(order)
    mocker.patch.object(
        processor.ext_client,
        "get_templates_by_product_id",
        Mock(side_effect=lambda **_: _templates_gen()),
    )
    template_id = await processor.get_product_template_id(PROCESSING_TEMPLATE_TYPE, "DoesNotExist")
    assert template_id == "TPL-0002"
    processor.ext_client.get_templates_by_product_id.assert_called_once_with(product_id=PRODUCT_ID)


async def test_get_product_template_returns_default_when_name_is_none(
    mocker, order_factory, make_processor
):
    order = order_factory(
        order_type="Purchase",
        status="Processing",
        product_id="PRD-4141-4379",
        product_name="SoftwareOne FinOps for Cloud",
    )
    processor = make_processor(order)
    mocker.patch.object(
        processor.ext_client,
        "get_templates_by_product_id",
        Mock(side_effect=lambda **_: _templates_gen()),
    )
    template_id = await processor.get_product_template_id(QUERYING_TEMPLATE_TYPE, None)
    assert template_id == "TPL-0003"


async def test_get_product_template_uses_cache_without_http_call(
    mocker, order_factory, make_processor
):
    order = order_factory(
        order_type="Purchase",
        status="Processing",
        product_id="PRD-4141-4379",
        product_name="SoftwareOne FinOps for Cloud",
    )
    processor = make_processor(order)
    mocker.patch.object(
        processor.ext_client,
        "get_templates_by_product_id",
        Mock(side_effect=lambda **_: _templates_gen()),
    )
    processor.template_cache[(PROCESSING_TEMPLATE_TYPE, PURCHASE_TEMPLATE_NAME)] = "TPL-CACHED"
    processor.template_cache[(PROCESSING_TEMPLATE_TYPE, None)] = "TPL-DEFAULT"
    template_id = await processor.get_product_template_id(
        PROCESSING_TEMPLATE_TYPE, PURCHASE_TEMPLATE_NAME
    )

    assert template_id == "TPL-CACHED"
    processor.ext_client.get_templates_by_product_id.assert_not_called()


async def test_fetch_product_template_builds_cache(mocker, order_factory, make_processor):
    order = order_factory(
        order_type="Purchase",
        status="Processing",
        product_id="PRD-4141-4379",
        product_name="SoftwareOne FinOps for Cloud",
    )
    processor = make_processor(order)
    mocker.patch.object(
        processor.ext_client,
        "get_templates_by_product_id",
        Mock(side_effect=lambda **_: _templates_gen()),
    )
    await processor.fetch_product_templates(PRODUCT_ID)
    assert processor.template_cache == {
        (PROCESSING_TEMPLATE_TYPE, PURCHASE_TEMPLATE_NAME): "TPL-0001",
        (PROCESSING_TEMPLATE_TYPE, None): "TPL-0002",
        (QUERYING_TEMPLATE_TYPE, None): "TPL-0003",
        (COMPLETED_TEMPLATE_TYPE, None): "TPL-0004",
        (COMPLETED_TEMPLATE_TYPE, PURCHASE_TEMPLATE_NAME): "TPL-0005",
        (COMPLETED_TEMPLATE_TYPE, PURCHASE_EXISTING_TEMPLATE_NAME): "TPL-0006",
    }
    processor.ext_client.get_templates_by_product_id.assert_called_once_with(product_id=PRODUCT_ID)


async def test_fetch_product_templates_with_no_templates_leaves_cache_empty(
    mocker, order_factory, make_processor
):
    async def _empty_gen():
        yield

    order = order_factory(
        order_type="Purchase",
        status="Processing",
        product_id="PRD-4141-4379",
        product_name="SoftwareOne FinOps for Cloud",
    )
    processor = make_processor(order)
    mocker.patch.object(
        processor.ext_client,
        "get_templates_by_product_id",
        Mock(side_effect=lambda **_: _empty_gen()),
    )
    await processor.fetch_product_templates(PRODUCT_ID)
    assert processor.template_cache == {}


# -- set_processing_order_template --


async def test_start_processing_order_template(mocker, make_processor, order_factory, caplog):
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
    processor = make_processor(order)
    mocker.patch.object(
        processor.ext_client,
        "get_templates_by_product_id",
        Mock(side_effect=lambda **_: _templates_gen()),
    )

    updated_order = copy.deepcopy(order)
    updated_order["template"]["id"] = "TPL-0001"
    mocker.patch.object(processor.ext_client, "update_order", return_value=updated_order)
    with caplog.at_level(logging.INFO):
        response = await processor.set_processing_order_template(order)
        assert response == updated_order
        assert f"{order['id']}: processing template set to Purchase (TPL-0001)" in caplog.text


async def test_set_processing_order_template_switches_template(
    mocker, make_processor, order_factory, caplog
):
    order = order_factory(
        order_type="Purchase",
        status="Processing",
        product_id="PRD-4141-4379",
        product_name="SoftwareOne FinOps for Cloud",
    )
    processor = make_processor(order)
    mocker.patch.object(
        processor.ext_client,
        "get_templates_by_product_id",
        Mock(side_effect=lambda **_: _templates_gen()),
    )
    updated_order = copy.deepcopy(order)
    updated_order["template"]["id"] = "TPL-0001"
    processor.ext_client.update_order.return_value = updated_order
    with caplog.at_level(logging.INFO):
        response = await processor.set_processing_order_template(order)
    assert response == updated_order
    assert processor.order == updated_order
    processor.ext_client.update_order.assert_awaited_once_with(
        order_id=order["id"], template={"id": "TPL-0001"}
    )
    assert f"{order['id']}: processing template set to Purchase (TPL-0001)" in caplog.text
    assert f"{order['id']}: processing template is ok, continue" in caplog.text


async def test_start_processing_order_template_with_same_template(
    mocker, order_factory, make_processor, caplog
):
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
    processor = make_processor(order)
    mocker.patch.object(
        processor.ext_client,
        "get_templates_by_product_id",
        Mock(side_effect=lambda **_: _templates_gen()),
    )

    mocker.patch.object(processor.ext_client, "update_order", return_value=order)
    with caplog.at_level(logging.INFO):
        response = await processor.set_processing_order_template(order)
        assert response == order
        assert f"{order['id']}: processing template is ok, continue" in caplog.text


async def test_test_validate_returns_true_for_valid_order(make_processor, order_factory, caplog):
    order = order_factory(
        order_type="Purchase",
        status="Processing",
        product_id="PRD-4141-4379",
        product_name="SoftwareOne FinOps for Cloud",
    )
    processor = make_processor(order)
    result = await processor.validate_and_move_to_querying_if_needed()
    assert result is True
    processor.ext_client.update_order.assert_not_awaited()
    processor.ext_client.set_status_to_querying.assert_not_awaited()


async def test_validate_moves_invalid_order_to_querying(
    mocker, order_factory, make_processor, caplog
):
    order = order_factory(
        order_type="Purchase",
        status="Processing",
        product_id="PRD-4141-4379",
        product_name="SoftwareOne FinOps for Cloud",
    )
    processor = make_processor(order)
    order["parameters"]["ordering"][0]["value"] = None
    mocker.patch.object(
        processor.ext_client,
        "get_templates_by_product_id",
        Mock(side_effect=lambda **_: _templates_gen()),
    )
    querying_order = copy.deepcopy(order)
    querying_order["status"] = "Querying"
    processor.ext_client.set_status_to_querying.return_value = querying_order
    with caplog.at_level(logging.INFO):
        result = await processor.validate_and_move_to_querying_if_needed()
    assert result is False
    update_call = processor.ext_client.update_order.await_args
    assert update_call.kwargs["order_id"] == order["id"]
    assert "error" in update_call.kwargs["parameters"]["ordering"][0]
    # Validation errors are written back to the order parameters.
    update_call = processor.ext_client.update_order.await_args
    assert update_call.kwargs["order_id"] == order["id"]
    assert "error" in update_call.kwargs["parameters"]["ordering"][0]
    # The order is moved to querying with the querying (default) template.
    processor.ext_client.set_status_to_querying.assert_awaited_once_with(
        order_id=order["id"], payload={"template": {"id": "TPL-0003"}}
    )
    assert querying_order["parameters"]["ordering"][0]["error"].message == (
        "Organization name is required"
    )
    assert f"{order['id']}: ordering parameters are invalid, move to querying" in caplog.text


async def test_validate_order_status_not_valid(order_factory, make_processor, test_settings):
    order = order_factory(
        order_type="Purchase",
        status="Completed",
        product_id="PRD-4141-4379",
        product_name="SoftwareOne FinOps for Cloud",
    )
    processor = make_processor(order)
    with pytest.raises(OrderNotValidError):
        await processor.validate_order()


async def test_validate_order_passes_for_valid_processing_order(
    make_processor, order_factory, test_settings
):
    order = order_factory(
        order_type="Purchase",
        status="Processing",
        product_id="PRD-4141-4379",
        product_name="SoftwareOne FinOps for Cloud",
    )
    processor = make_processor(order)
    assert await processor.validate_order() is None
    processor.ext_client.set_status_to_querying.assert_not_awaited()


async def test_validate_order_raises_when_moved_to_querying(mocker, order_factory, make_processor):
    order = order_factory(
        order_type="Purchase",
        status="Processing",
        product_id="PRD-4141-4379",
        product_name="SoftwareOne FinOps for Cloud",
    )
    order["parameters"]["ordering"][0]["value"] = None
    processor = make_processor(order)
    mocker.patch.object(
        processor.ext_client,
        "get_templates_by_product_id",
        Mock(side_effect=lambda **_: _templates_gen()),
    )
    querying_order = copy.deepcopy(order)
    querying_order["status"] = "Querying"
    processor.ext_client.set_status_to_querying.return_value = querying_order
    with pytest.raises(OrderMovedToQuery, match=order["id"]):
        await processor.validate_order()
    processor.ext_client.set_status_to_querying.assert_awaited_once()


async def test_do_not_apply_fulfillment_defaults(mocker, make_processor, order_factory):
    order = order_factory(
        order_type="Purchase",
        status="Processing",
        product_id="PRD-4141-4379",
        product_name="SoftwareOne FinOps for Cloud",
    )
    processor = make_processor(order)
    mocker.patch.object(
        processor.ext_client,
        "get_templates_by_product_id",
        Mock(side_effect=lambda **_: _templates_gen()),
    )
    response = await processor.apply_fulfillment_defaults()
    assert response == order


async def test_apply_fulfillment_defaults(mocker, make_processor, order_factory):
    order = order_factory(
        order_type="Purchase",
        status="Processing",
        product_id="PRD-4141-4379",
        product_name="SoftwareOne FinOps for Cloud",
    )
    processor = make_processor(order)
    for param in order["parameters"]["fulfillment"]:
        if param["externalId"] in {
            "dueDate",
            "billedPercentage",
            "trialStartDate",
            "trialEndDate",
        }:
            param["value"] = None
    expected_order = copy.deepcopy(order)
    mocker.patch.object(processor.ext_client, "update_order", return_value=expected_order)
    response = await processor.apply_fulfillment_defaults()
    assert response == expected_order


async def test_get_or_create_organization(mocker, make_processor, caplog, order_factory):
    order = order_factory(
        order_type="Purchase",
        status="Processing",
        product_id="PRD-4141-4379",
        product_name="SoftwareOne FinOps for Cloud",
    )
    processor = make_processor(order)
    agreement_id = order["agreement"]["id"]

    # Only the authorization currency is read from the agreement (the billing currency).
    agreement_body = {
        "authorization": {
            "id": "AUT-3727-1184",
            "name": "SoftwareOne FinOps for Cloud (USD)",
            "currency": "USD",
        },
    }
    mocker.patch.object(processor.ext_client, "get_agreement", return_value=agreement_body)
    mocked_update_agreement = mocker.patch.object(processor.ext_client, "update_agreement")
    processor.api_modifier_client.create_organization.return_value = Mock(
        json=Mock(return_value={"id": "OPT-ORG-0001"})
    )
    # created=True with no link yet -> takes the OptScale creation path.
    organization = Mock(
        id="b57b9964-7046-4e20-812c-01ab52cf4661",
        linked_organization_id=None,
    )
    processor.organization_repo.get_or_create.return_value = (organization, True)

    with caplog.at_level(logging.INFO):
        result = await processor.get_or_create_organization(employee_id="employee-id")

    assert result is organization
    # The agreement is read to resolve the billing currency.
    processor.ext_client.get_agreement.assert_awaited_once_with(
        agreement_id, select=["authorization"]
    )
    # name / currency / billing_currency were passed as defaults to get_or_create.
    processor.organization_repo.get_or_create.assert_awaited_once_with(
        operations_external_id=agreement_id,
        defaults={"name": "ACME Inc", "currency": "USD", "billing_currency": "USD"},
    )
    # A fresh org is provisioned on OptScale...
    processor.api_modifier_client.create_organization.assert_awaited_once_with(
        org_name="ACME Inc", user_id="employee-id", currency="USD"
    )
    # ...the agreement is linked back to it...
    mocked_update_agreement.assert_awaited_once_with(
        agreement_id, externalIds={"vendor": organization.id}
    )
    # ...and the OptScale org id is persisted locally via update().
    processor.organization_repo.update.assert_awaited_once_with(
        organization.id,
        {"linked_organization_id": "OPT-ORG-0001"},
    )


async def test_get_or_create_organization_already_exists(
    mocker, order_factory, db_session, make_processor, caplog
):
    order = order_factory(
        order_type="Purchase",
        status="Processing",
        product_id="PRD-4141-4379",
        product_name="SoftwareOne FinOps for Cloud",
    )
    processor = make_processor(order)
    agreement_id = order["agreement"]["id"]
    organization_repo = OrganizationHandler(db_session)
    processor.organization_repo = organization_repo
    existing = await organization_repo.create(
        Organization(
            name="Pre-existing ORG",
            currency="EUR",
            billing_currency="USD",
            operations_external_id=agreement_id,
            linked_organization_id="already-linked-optscale-org-id",
        )
    )

    mocker.patch.object(
        processor.ext_client, "get_agreement", return_value={"authorization": {"currency": "USD"}}
    )
    mocked_update_agreement = mocker.patch.object(processor.ext_client, "update_agreement")
    with caplog.at_level(logging.INFO):
        result = await processor.get_or_create_organization("employee-id")

    assert result.id == existing.id
    assert result.name == "Pre-existing ORG"
    assert result.currency == "EUR"
    assert result.linked_organization_id == "already-linked-optscale-org-id"

    processor.api_modifier_client.create_organization.assert_not_called()
    mocked_update_agreement.assert_not_called()
    assert f"Organization already exists with id {existing.id}" in caplog.text
    assert "Organization on OptScale created" not in caplog.text


async def test_create_employee_with_existing_user(
    mocker, order_factory, db_session, make_processor, caplog
):
    order = order_factory(
        order_type="Purchase",
        status="Processing",
        product_id="PRD-4141-4379",
        product_name="SoftwareOne FinOps for Cloud",
    )
    processor = make_processor(order)
    mock_response = Mock()
    mock_response.json.return_value = {
        "user_info": {
            "id": "f0bd0c4a-7c55-45b7-8b58-27740e38789a",
            "display_name": "Spider Man",
            "email": "peter.parker@iamspiderman.com",
        }
    }
    mocker.patch.object(
        processor.optscale_auth_client,
        "get_existing_user_info",
        return_value=mock_response,
    )
    expected_order = copy.deepcopy(order)
    for param in expected_order["parameters"]["fulfillment"]:
        if param["externalId"] == "isNewUser":
            param["value"] = None

    expected_parameters = expected_order["parameters"]
    mocked_update_order = mocker.patch.object(
        processor.ext_client, "update_order", return_value=expected_order
    )

    with caplog.at_level(logging.INFO):
        employee_id, employee_email = await processor.create_employee()
    # create_employee stores the updated order on self.order and returns (id, email).
    assert processor.order is expected_order
    assert employee_id == "f0bd0c4a-7c55-45b7-8b58-27740e38789a"
    assert employee_email == "pl@example.com"
    processor.optscale_auth_client.get_existing_user_info.assert_called_once_with("pl@example.com")
    mocked_update_order.assert_called_once_with(order["id"], parameters=expected_parameters)
    processor.api_modifier_client.create_user.assert_not_called()
    assert (
        f"Employee exists with id f0bd0c4a-7c55-45b7-8b58-27740e38789a for order {order['id']}"
        in caplog.text
    )


async def test_create_employee_with_no_existing_user(
    mocker, order_factory, make_processor, db_session, caplog
):
    order = order_factory(
        order_type="Purchase",
        status="Processing",
        product_id="PRD-4141-4379",
        product_name="SoftwareOne FinOps for Cloud",
    )
    processor = make_processor(order)
    mock_response = Mock()
    mock_response.json.return_value = {
        "id": "f0bd0c4a-7c55-45b7-8b58-27740e38789a",
        "display_name": "Spider Man",
        "email": "peter.parker@iamspiderman.com",
    }
    mocker.patch.object(
        processor.optscale_auth_client,
        "get_existing_user_info",
        side_effect=UserDoesNotExist("pl@example.com"),
    )

    expected_order = copy.deepcopy(order)
    for param in expected_order["parameters"]["fulfillment"]:
        if param["externalId"] == "isNewUser":
            param["value"] = ["Yes"]

    expected_parameters = expected_order["parameters"]
    mocked_update_order = mocker.patch.object(
        processor.ext_client, "update_order", return_value=expected_order
    )

    processor.api_modifier_client.create_user.return_value = mock_response
    with caplog.at_level(logging.INFO):
        employee_id, employee_email = await processor.create_employee()
    assert employee_id == "f0bd0c4a-7c55-45b7-8b58-27740e38789a"
    assert employee_email == "pl@example.com"
    processor.optscale_auth_client.get_existing_user_info.assert_called_once_with("pl@example.com")
    mocked_update_order.assert_called_once_with(order["id"], parameters=expected_parameters)
    processor.api_modifier_client.create_user.assert_called_once_with(
        email="pl@example.com",
        display_name="PL NN",
        password=mocker.ANY,
    )
    assert (
        f"Employee created with id f0bd0c4a-7c55-45b7-8b58-27740e38789a for order {order['id']}"
        in caplog.text
    )


async def test_create_employee_with__already_new_user_eq_yes(
    mocker, order_factory, make_processor, caplog
):
    """Retry: user now exists, but order already recorded isNewUser=['Yes']."""
    order = order_factory(
        order_type="Purchase",
        status="Processing",
        product_id="PRD-4141-4379",
        product_name="SoftwareOne FinOps for Cloud",
    )
    processor = make_processor(order)

    for param in order["parameters"]["fulfillment"]:
        if param["externalId"] == "isNewUser":
            param["value"] = None

    mock_response = Mock()
    mock_response.json.return_value = {"user_info": {"id": "f0bd0c4a-7c55-45b7-8b58-27740e38789a"}}
    processor.optscale_auth_client.get_existing_user_info.return_value = mock_response

    expected_order = copy.deepcopy(order)
    mocked_update_order = mocker.patch.object(
        processor.ext_client, "update_order", return_value=expected_order
    )

    employee_id, employee_email = await processor.create_employee()
    assert employee_id == "f0bd0c4a-7c55-45b7-8b58-27740e38789a"
    mocked_update_order.assert_called_once_with(
        order["id"], parameters=expected_order["parameters"]
    )


# -- subscriptions --


async def test_create_order_subscription_skips_when_subscription_already_exists(
    order_factory, make_processor
):
    order = order_factory(
        order_type="Purchase",
        status="Processing",
        product_id="PRD-4141-4379",
        product_name="SoftwareOne FinOps for Cloud",
    )
    processor = make_processor(order)

    organization = Mock(id="b57b9964-7046-4e20-812c-01ab52cf4661")

    await processor.create_order_subscription(organization)

    processor.ext_client.create_subscription.assert_not_awaited()


async def test_create_order_subscription_creates_missing_subscription(
    order_factory, make_processor, caplog
):
    # No pre-existing subscription for the line -> a new one is created and linked to the org.
    order = order_factory(
        order_type="Purchase",
        status="Processing",
        product_id="PRD-4141-4379",
        product_name="SoftwareOne FinOps for Cloud",
        subscriptions=[],
    )
    processor = make_processor(order)
    processor.ext_client.create_subscription.return_value = {"id": "SUB-9999-0001"}
    organization = Mock(id="b57b9964-7046-4e20-812c-01ab52cf4661")

    with caplog.at_level(logging.INFO):
        await processor.create_order_subscription(organization)

    line = order["lines"][0]
    processor.ext_client.create_subscription.assert_awaited_once_with(
        order_id=order["id"],
        subscription={
            "name": f"Subscription for {line['item']['name']}",
            "parameters": {},
            "externalIds": {"vendor": organization.id},
            "lines": [{"id": line["id"]}],
        },
    )
    assert f"{order['id']}: subscription {line['id']} (SUB-9999-0001) created" in caplog.text


# -- get_complete_template --


@pytest.mark.parametrize(
    ("is_new", "expected_template_id"),
    [(True, "TPL-0005"), (False, "TPL-0006")],  # PurchaseExisting is the not-new template
)
async def test_get_complete_template(
    mocker, order_factory, make_processor, is_new, expected_template_id
):
    order = order_factory(
        order_type="Purchase",
        status="Processing",
        product_id="PRD-4141-4379",
        product_name="SoftwareOne FinOps for Cloud",
    )
    processor = make_processor(order)
    mocker.patch.object(
        processor.ext_client,
        "get_templates_by_product_id",
        Mock(side_effect=lambda **_: _templates_gen()),
    )
    template_id = await processor.get_complete_template(is_new)
    assert template_id == expected_template_id


# -- OrderProcessor.handle_exception (base) --


async def test_base_handle_exception_is_a_noop(order_factory, make_processor):
    # The base processor has no recovery behaviour; subclasses override it.
    order = order_factory(
        order_type="Purchase",
        status="Processing",
        product_id="PRD-4141-4379",
        product_name="SoftwareOne FinOps for Cloud",
    )
    processor = make_processor(order)
    assert await processor.handle_exception(RuntimeError("boom"), now=None) is None


# -- PurchaseOrderProcessor.send_reset_password --


async def test_send_reset_password_new_user_sends_reset(order_factory, test_settings, caplog):
    order = order_factory(
        order_type="Purchase",
        status="Processing",
        product_id="PRD-4141-4379",
        product_name="SoftwareOne FinOps for Cloud",
    )
    processor = _make_purchase_processor(order, test_settings)

    with caplog.at_level(logging.INFO):
        await processor.send_reset_password("pl@example.com", is_new=True)

    processor.optscale_client.reset_password.assert_awaited_once_with("pl@example.com")
    assert "Employee pl@example.com password reset sent" in caplog.text


async def test_send_reset_password_swallows_reset_failure(order_factory, test_settings, caplog):
    # A failure while sending the reset is logged and swallowed (does not propagate).
    order = order_factory(
        order_type="Purchase",
        status="Processing",
        product_id="PRD-4141-4379",
        product_name="SoftwareOne FinOps for Cloud",
    )
    processor = _make_purchase_processor(order, test_settings)
    processor.optscale_client.reset_password.side_effect = Exception("OptScale down")

    with caplog.at_level(logging.ERROR):
        await processor.send_reset_password("pl@example.com", is_new=True)

    assert "Failed to reset password" in caplog.text


async def test_send_reset_password_existing_user_is_noop(order_factory, test_settings, caplog):
    order = order_factory(
        order_type="Purchase",
        status="Processing",
        product_id="PRD-4141-4379",
        product_name="SoftwareOne FinOps for Cloud",
    )
    processor = _make_purchase_processor(order, test_settings)

    with caplog.at_level(logging.INFO):
        await processor.send_reset_password("pl@example.com", is_new=False)

    processor.optscale_client.reset_password.assert_not_awaited()
    assert "No need to send reset password for pl@example.com" in caplog.text


# -- PurchaseOrderProcessor.process --


async def test_purchase_order_process_completes_order(mocker, order_factory, test_settings, caplog):
    order = order_factory(
        order_type="Purchase",
        status="Processing",
        product_id="PRD-4141-4379",
        product_name="SoftwareOne FinOps for Cloud",
    )
    processor = _make_purchase_processor(order, test_settings)
    organization = Mock(id="b57b9964-7046-4e20-812c-01ab52cf4661")

    mocked_validate = mocker.patch.object(processor, "validate_order", AsyncMock())
    mocked_defaults = mocker.patch.object(processor, "apply_fulfillment_defaults", AsyncMock())
    mocked_set_template = mocker.patch.object(
        processor, "set_processing_order_template", AsyncMock()
    )
    mocked_create_employee = mocker.patch.object(
        processor, "create_employee", AsyncMock(return_value=("employee-id", "pl@example.com"))
    )
    mocked_get_or_create_org = mocker.patch.object(
        processor, "get_or_create_organization", AsyncMock(return_value=organization)
    )
    mocked_create_subscription = mocker.patch.object(
        processor, "create_order_subscription", AsyncMock()
    )
    mocked_get_complete_template = mocker.patch.object(
        processor, "get_complete_template", AsyncMock(return_value="TPL-0006")
    )
    mocked_send_reset_password = mocker.patch.object(processor, "send_reset_password", AsyncMock())

    with caplog.at_level(logging.INFO):
        result = await processor.process()

    assert result is processor.order

    # Each step runs once, in order, with the expected arguments.
    mocked_validate.assert_awaited_once_with()
    mocked_defaults.assert_awaited_once_with()
    mocked_set_template.assert_awaited_once_with(order=processor.order)
    mocked_create_employee.assert_awaited_once_with()
    mocked_get_or_create_org.assert_awaited_once_with("employee-id")
    mocked_create_subscription.assert_awaited_once_with(organization)
    # isNewUser has no value in the factory order -> existing-user  (is_new is False).
    mocked_get_complete_template.assert_awaited_once_with(False)
    processor.ext_client.complete_order.assert_awaited_once_with(
        order_id=order["id"], payload={"template": {"id": "TPL-0006"}}
    )
    mocked_send_reset_password.assert_awaited_once_with("pl@example.com", False)
    assert f"Order {order['id']} has been completed" in caplog.text


async def test_purchase_order_process_new_user_branch(mocker, order_factory, test_settings):
    order = order_factory(
        order_type="Purchase",
        status="Processing",
        product_id="PRD-4141-4379",
        product_name="SoftwareOne FinOps for Cloud",
    )
    # isNewUser == ["Yes"] -> new-user (is_new is True).
    for param in order["parameters"]["fulfillment"]:
        if param["externalId"] == "isNewUser":
            param["value"] = ["Yes"]
    processor = _make_purchase_processor(order, test_settings)
    organization = Mock(id="b57b9964-7046-4e20-812c-01ab52cf4661")

    mocker.patch.object(processor, "validate_order", AsyncMock())
    mocker.patch.object(processor, "apply_fulfillment_defaults", AsyncMock())
    mocker.patch.object(processor, "set_processing_order_template", AsyncMock())
    mocker.patch.object(
        processor, "create_employee", AsyncMock(return_value=("employee-id", "new@example.com"))
    )
    mocker.patch.object(
        processor, "get_or_create_organization", AsyncMock(return_value=organization)
    )
    mocker.patch.object(processor, "create_order_subscription", AsyncMock())
    mocked_get_complete_template = mocker.patch.object(
        processor, "get_complete_template", AsyncMock(return_value="TPL-0005")
    )
    mocked_send_reset_password = mocker.patch.object(processor, "send_reset_password", AsyncMock())

    result = await processor.process()

    assert result is processor.order
    # New user -> completes with the new-user template and triggers a password reset.
    mocked_get_complete_template.assert_awaited_once_with(True)
    processor.ext_client.complete_order.assert_awaited_once_with(
        order_id=order["id"], payload={"template": {"id": "TPL-0005"}}
    )
    mocked_send_reset_password.assert_awaited_once_with("new@example.com", True)


async def test_purchase_order_process_short_circuits_when_validation_fails(
    mocker, order_factory, test_settings
):
    order = order_factory(
        order_type="Purchase",
        status="Processing",
        product_id="PRD-4141-4379",
        product_name="SoftwareOne FinOps for Cloud",
    )
    processor = _make_purchase_processor(order, test_settings)

    mocker.patch.object(
        processor, "validate_order", AsyncMock(side_effect=OrderMovedToQuery(order["id"]))
    )
    mocked_defaults = mocker.patch.object(processor, "apply_fulfillment_defaults", AsyncMock())
    mocked_create_employee = mocker.patch.object(processor, "create_employee", AsyncMock())

    with pytest.raises(OrderMovedToQuery, match=order["id"]):
        await processor.process()

    # Nothing past validation runs, and the order is never completed.
    mocked_defaults.assert_not_awaited()
    mocked_create_employee.assert_not_awaited()
    processor.ext_client.complete_order.assert_not_awaited()
