import copy
import logging
from collections.abc import Callable
from datetime import date
from typing import Any

import pytest
from freezegun import freeze_time
from pytest_mock import MockerFixture

from app.api_clients.optscale import UserDoesNotExist
from app.db.handlers import OrganizationHandler
from app.db.models import Organization
from app.fulfilment.constants import (
    COMPLETED_TEMPLATE_TYPE,
    PROCESSING_TEMPLATE_TYPE,
    PURCHASE_EXISTING_TEMPLATE_NAME,
    PURCHASE_TEMPLATE_NAME,
    QUERYING_TEMPLATE_TYPE,
)
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
from app.fulfilment.processing import (
    ProcessingStatus,
    PurchaseOrderProcessor,
)
from app.parameters import PARAM_DUE_DATE, set_due_date
from tests.types import FactoryBuilder, ProcessorBuilder, TemplatesMocker

PRODUCT_ID = "PRD-4141-4379"


# -- get_order_type_processor --


async def test_get_order_type_processor(
    purchase_order: dict[str, Any], make_order_processor_factory: FactoryBuilder
) -> None:
    """`get_order_type_processor` builds a `PurchaseOrderProcessor` from the fetched order."""
    factory = make_order_processor_factory(purchase_order)
    processor = await factory.get_order_type_processor(order_id=purchase_order["id"])
    assert processor.order == purchase_order
    assert isinstance(processor, PurchaseOrderProcessor)
    factory.client.get_order.assert_awaited_once_with(purchase_order["id"])


async def test_process_order_without_due_date(
    make_processor: ProcessorBuilder,
    purchase_order: dict[str, Any],
    caplog,
    mocker: MockerFixture,
) -> None:
    """A fail_order error is logged and swallowed when the order has no due date"""
    purchase_order = set_due_date(purchase_order, None)
    processor = make_processor(purchase_order)
    mocker.patch.object(processor, "validate_order", side_effect=RuntimeError("big error"))
    processor.ext_client.fail_order.side_effect = RuntimeError("order is already Failed")
    with pytest.raises(RuntimeError, match="order is already Failed"):
        await processor.process()


@freeze_time("2026-08-11")
async def test_change_order_process_handles_a_malformed_order(
    make_processor: ProcessorBuilder,
    change_order: dict[str, Any],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """An order missing its `type` key is rescheduled with a traceback, not propagated."""
    change_order = set_due_date(change_order, date(2026, 12, 1))
    order_id = change_order["id"]
    processor = make_processor(change_order)
    processor.order = {key: value for key, value in change_order.items() if key != "type"}

    with caplog.at_level(logging.ERROR):
        result = await processor.process()
    assert result.status is ProcessingStatus.RESCHEDULE
    assert result.severity == "Warning"
    assert result.message == "An error occurred while processing the order: 'type'"
    assert f"{order_id}: Change Order processing failed." in caplog.text
    assert "KeyError" in caplog.text
    processor.ext_client.fail_order.assert_not_awaited()


async def test_get_order_type_processor_rejects_unsupported_type(
    order_factory: Callable[..., dict[str, Any]],
    make_order_processor_factory: FactoryBuilder,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """`get_order_type_processor` raises and warns for an order type with no processor."""
    order = order_factory(
        order_type="Configuration",
        status="Processing",
        product_id="PRD-4141-4379",
        product_name="SoftwareOne FinOps for Cloud",
    )
    factory = make_order_processor_factory(order)
    with caplog.at_level(logging.WARNING):
        with pytest.raises(UnsupportedOrderTypeError, match="Configuration"):
            await factory.get_order_type_processor(order_id=order["id"])

    assert "The order type Configuration is not supported." in caplog.text
    factory.client.get_order.assert_awaited_once_with(order["id"])


# -- OrderProcessor.set_template --


async def test_set_template_assigns_id_and_returns_copy(
    purchase_order: dict[str, Any], make_processor: ProcessorBuilder
) -> None:
    """`set_template` returns a copy with the new template id, leaving the original untouched."""
    processor = make_processor(purchase_order)
    result = processor.set_template(order=purchase_order, template_id="TPL-1234-5678-0001")
    assert processor.order is result
    assert result["template"]["id"] == "TPL-1234-5678-0001"
    assert purchase_order["template"]["id"] == "TPL-1234-1234-4321"
    assert purchase_order["template"]["name"] == "Default Template"


async def test_set_template_raises_when_template_id_is_missing(
    purchase_order: dict[str, Any], make_processor: ProcessorBuilder
) -> None:
    """`set_template` raises `ValueError` when no template id is provided."""
    processor = make_processor(purchase_order)
    with pytest.raises(ValueError, match="Template id is required"):
        processor.set_template(order=purchase_order, template_id="")


async def test_set_template_raises_when_order_malformed(
    purchase_order: dict[str, Any], make_processor: ProcessorBuilder
) -> None:
    """`set_template` raises `KeyError` when the order is missing its template key."""
    purchase_order.pop("template", None)
    processor = make_processor(purchase_order)
    with pytest.raises(KeyError, match="Order is malformed"):
        processor.set_template(order=purchase_order, template_id="TPL-1234-5678-0001")


# -- get_product_template_id / fetch_product_templates --


async def test_get_product_template_returns_specific_by_name(
    purchase_order: dict[str, Any],
    make_processor: ProcessorBuilder,
    mock_product_templates: TemplatesMocker,
) -> None:
    """`get_product_template_id` returns the id of the template matching the type and name."""
    processor = make_processor(purchase_order)
    mock_product_templates(processor)
    template_id = await processor.get_product_template_id(PROCESSING_TEMPLATE_TYPE, "Purchase")
    assert template_id == "TPL-0001"
    processor.ext_client.get_templates_by_product_id.assert_called_once_with(product_id=PRODUCT_ID)


async def test_get_product_template_fails_back_to_default(
    purchase_order: dict[str, Any],
    make_processor: ProcessorBuilder,
    mock_product_templates: TemplatesMocker,
) -> None:
    """`get_product_template_id` falls back to the default template when the name is unknown."""
    processor = make_processor(purchase_order)
    mock_product_templates(processor)
    template_id = await processor.get_product_template_id(PROCESSING_TEMPLATE_TYPE, "DoesNotExist")
    assert template_id == "TPL-0002"
    processor.ext_client.get_templates_by_product_id.assert_called_once_with(product_id=PRODUCT_ID)


async def test_get_product_template_returns_default_when_name_is_none(
    purchase_order: dict[str, Any],
    make_processor: ProcessorBuilder,
    mock_product_templates: TemplatesMocker,
) -> None:
    """`get_product_template_id` returns the default template when the requested name is `None`."""
    processor = make_processor(purchase_order)
    mock_product_templates(processor)
    template_id = await processor.get_product_template_id(QUERYING_TEMPLATE_TYPE, None)
    assert template_id == "TPL-0003"


async def test_get_product_template_uses_cache_without_http_call(
    purchase_order: dict[str, Any],
    make_processor: ProcessorBuilder,
    mock_product_templates: TemplatesMocker,
) -> None:
    """`get_product_template_id` serves a cached template without hitting the marketplace."""
    processor = make_processor(purchase_order)
    mock_product_templates(processor)
    processor.template_cache[(PROCESSING_TEMPLATE_TYPE, PURCHASE_TEMPLATE_NAME)] = "TPL-CACHED"
    processor.template_cache[(PROCESSING_TEMPLATE_TYPE, None)] = "TPL-DEFAULT"
    template_id = await processor.get_product_template_id(
        PROCESSING_TEMPLATE_TYPE, PURCHASE_TEMPLATE_NAME
    )
    assert template_id == "TPL-CACHED"
    processor.ext_client.get_templates_by_product_id.assert_not_called()


async def test_get_product_template_raises_exception(
    purchase_order: dict[str, Any],
    make_processor: ProcessorBuilder,
    mock_product_templates: TemplatesMocker,
) -> None:
    processor = make_processor(purchase_order)
    mock_product_templates(processor)
    processor.template_cache[(PROCESSING_TEMPLATE_TYPE, PURCHASE_TEMPLATE_NAME)] = None
    with pytest.raises(OrderNotValidError, match="has no template type"):
        await processor.get_product_template_id(PROCESSING_TEMPLATE_TYPE, PURCHASE_TEMPLATE_NAME)


async def test_fetch_product_template_builds_cache(
    purchase_order: dict[str, Any],
    make_processor: ProcessorBuilder,
    mock_product_templates: TemplatesMocker,
) -> None:
    """`fetch_product_templates` caches every template keyed by type and name."""
    processor = make_processor(purchase_order)
    mock_product_templates(processor)
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
    purchase_order: dict[str, Any],
    make_processor: ProcessorBuilder,
    mock_product_templates: TemplatesMocker,
) -> None:
    """`fetch_product_templates` leaves the cache empty when no templates are returned."""
    processor = make_processor(purchase_order)
    mock_product_templates(processor, templates=[])
    await processor.fetch_product_templates(PRODUCT_ID)
    assert processor.template_cache == {}


# -- set_processing_order_template --


async def test_set_processing_order_template_switches_template(
    make_processor: ProcessorBuilder,
    purchase_order: dict[str, Any],
    mock_product_templates: TemplatesMocker,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """`set_processing_order_template` swaps in the purchase template when it differs."""
    processor = make_processor(purchase_order)
    mock_product_templates(processor)
    updated_order = copy.deepcopy(purchase_order)
    updated_order["template"]["id"] = "TPL-0001"
    processor.ext_client.update_order.return_value = updated_order
    with caplog.at_level(logging.INFO):
        response = await processor.set_processing_order_template()
    assert response == updated_order
    assert processor.order == updated_order
    processor.ext_client.update_order.assert_awaited_once_with(
        order_id=purchase_order["id"], template={"id": "TPL-0001"}
    )
    assert f"{purchase_order['id']}: processing template set to Purchase (TPL-0001)" in caplog.text
    assert f"{purchase_order['id']}: processing template is ok, continue" in caplog.text


async def test_set_processing_order_template_keeps_matching_template(
    make_processor: ProcessorBuilder,
    order_factory: Callable[..., dict[str, Any]],
    mock_product_templates: TemplatesMocker,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """`set_processing_order_template` leaves the order untouched when it already matches."""
    order = order_factory(
        order_type="Purchase",
        status="Processing",
        product_id="PRD-4141-4379",
        product_name="SoftwareOne FinOps for Cloud",
        template={"id": "TPL-0001", "name": "Purchase", "revision": 1},
    )
    processor = make_processor(order)
    mock_product_templates(processor)
    processor.ext_client.update_order.return_value = order
    with caplog.at_level(logging.INFO):
        response = await processor.set_processing_order_template()
    assert response == order
    processor.ext_client.update_order.assert_not_awaited()
    assert f"{order['id']}: processing template is ok, continue" in caplog.text


# -- validate_and_move_to_querying_if_needed / validate_order --


async def test_validate_returns_true_for_valid_order(
    make_processor: ProcessorBuilder, purchase_order: dict[str, Any]
) -> None:
    """`validate_and_move_to_querying_if_needed` returns `True` and touches nothing when valid."""
    processor = make_processor(purchase_order)
    result = await processor.validate_and_move_to_querying_if_needed()
    assert result is True
    processor.ext_client.update_order.assert_not_awaited()
    processor.ext_client.set_status_to_querying.assert_not_awaited()


async def test_validate_moves_invalid_order_to_querying(
    purchase_order: dict[str, Any],
    make_processor: ProcessorBuilder,
    mock_product_templates: TemplatesMocker,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """`validate_and_move_to_querying_if_needed` writes back errors and moves invalid orders."""
    purchase_order["parameters"]["ordering"][0]["value"] = None
    processor = make_processor(purchase_order)
    mock_product_templates(processor)
    querying_order = copy.deepcopy(purchase_order)
    querying_order["status"] = "Querying"
    processor.ext_client.set_status_to_querying.return_value = querying_order
    with caplog.at_level(logging.INFO):
        result = await processor.validate_and_move_to_querying_if_needed()
    assert result is False
    update_call = processor.ext_client.update_order.await_args
    assert update_call.kwargs["order_id"] == purchase_order["id"]
    assert "error" in update_call.kwargs["parameters"]["ordering"][0]
    processor.ext_client.set_status_to_querying.assert_awaited_once_with(
        order_id=purchase_order["id"], payload={"template": {"id": "TPL-0003"}}
    )
    assert querying_order["parameters"]["ordering"][0]["error"].message == (
        "Organization name is required"
    )
    assert (
        f"{purchase_order['id']}: ordering parameters are invalid, move to querying" in caplog.text
    )


async def test_validate_order_status_not_valid(
    order_factory: Callable[..., dict[str, Any]], make_processor: ProcessorBuilder
) -> None:
    """`validate_order` raises `OrderNotValidError` when the order is not in Processing status."""
    order = order_factory(
        order_type="Purchase",
        status="Completed",
        product_id="PRD-4141-4379",
        product_name="SoftwareOne FinOps for Cloud",
    )
    processor = make_processor(order)
    with pytest.raises(OrderNotValidError, match=order["id"]):
        await processor.validate_order()


async def test_validate_order_passes_for_valid_processing_order(
    make_processor: ProcessorBuilder, purchase_order: dict[str, Any]
) -> None:
    """`validate_order` returns `None` and does not move a valid Processing order to querying."""
    processor = make_processor(purchase_order)
    assert await processor.validate_order() is None
    processor.ext_client.set_status_to_querying.assert_not_awaited()


async def test_validate_order_raises_when_moved_to_querying(
    purchase_order: dict[str, Any],
    make_processor: ProcessorBuilder,
    mock_product_templates: TemplatesMocker,
) -> None:
    """`validate_order` raises `OrderMovedToQuery` after an invalid order is moved to querying."""
    purchase_order["parameters"]["ordering"][0]["value"] = None
    processor = make_processor(purchase_order)
    mock_product_templates(processor)
    querying_order = copy.deepcopy(purchase_order)
    querying_order["status"] = "Querying"
    processor.ext_client.set_status_to_querying.return_value = querying_order
    with pytest.raises(OrderMovedToQuery, match=purchase_order["id"]):
        await processor.validate_order()
    processor.ext_client.set_status_to_querying.assert_awaited_once()


# -- apply_fulfillment_defaults --


async def test_apply_fulfillment_defaults_noop_when_nothing_to_update(
    make_processor: ProcessorBuilder, purchase_order: dict[str, Any]
) -> None:
    """`apply_fulfillment_defaults` returns the order unchanged when no parameters need defaults."""
    processor = make_processor(purchase_order)
    response = await processor.apply_fulfillment_defaults()
    assert response == purchase_order


async def test_apply_fulfillment_defaults_fills_missing_parameters(
    make_processor: ProcessorBuilder, purchase_order: dict[str, Any]
) -> None:
    """`apply_fulfillment_defaults` persists the order once defaults are applied."""
    processor = make_processor(purchase_order)
    for param in purchase_order["parameters"]["fulfillment"]:
        if param["externalId"] in {
            PARAM_DUE_DATE,
            "billedPercentage",
            "trialStartDate",
            "trialEndDate",
        }:
            param["value"] = None
    expected_order = copy.deepcopy(purchase_order)
    processor.ext_client.update_order.return_value = expected_order
    response = await processor.apply_fulfillment_defaults()
    assert response == expected_order


# -- get_or_create_organization --


async def test_get_or_create_organization(
    make_processor: ProcessorBuilder,
    caplog: pytest.LogCaptureFixture,
    purchase_order: dict[str, Any],
    mocker: MockerFixture,
) -> None:
    """`get_or_create_organization` provisions a new OptScale org and links the agreement."""
    processor = make_processor(purchase_order)
    agreement_id = purchase_order["agreement"]["id"]
    # Only the authorization currency is read from the agreement (the billing currency).
    processor.ext_client.get_agreement.return_value = {
        "authorization": {
            "id": "AUT-3727-1184",
            "name": "SoftwareOne FinOps for Cloud (USD)",
            "currency": "USD",
        },
    }
    processor.api_modifier_client.create_organization.return_value = mocker.Mock(
        json=mocker.Mock(return_value={"id": "OPT-ORG-0001"})
    )
    # created=True with no link yet -> takes the OptScale creation path.
    organization = mocker.Mock(
        id="b57b9964-7046-4e20-812c-01ab52cf4661",
        linked_organization_id=None,
    )
    processor.organization_repo.get_or_create.return_value = (organization, True)

    with caplog.at_level(logging.INFO):
        result = await processor.get_or_create_organization(employee_id="employee-id")

    assert result is organization
    processor.ext_client.get_agreement.assert_awaited_once_with(
        agreement_id, select=["authorization"]
    )
    processor.organization_repo.get_or_create.assert_awaited_once_with(
        operations_external_id=agreement_id,
        defaults={"name": "ACME Inc", "currency": "USD", "billing_currency": "USD"},
    )
    processor.api_modifier_client.create_organization.assert_awaited_once_with(
        org_name="ACME Inc", user_id="employee-id", currency="USD"
    )
    processor.ext_client.update_agreement.assert_awaited_once_with(
        agreement_id, externalIds={"vendor": organization.id}
    )
    processor.organization_repo.update.assert_awaited_once_with(
        organization.id,
        {"linked_organization_id": "OPT-ORG-0001"},
    )


async def test_get_or_create_organization_already_exists(
    order_factory: Callable[..., dict[str, Any]],
    db_session: Any,
    make_processor: ProcessorBuilder,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """`get_or_create_organization` reuses an already-linked organization without provisioning."""
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
    processor.ext_client.get_agreement.return_value = {"authorization": {"currency": "USD"}}

    with caplog.at_level(logging.INFO):
        result = await processor.get_or_create_organization("employee-id")

    assert result.id == existing.id
    assert result.name == "Pre-existing ORG"
    assert result.currency == "EUR"
    assert result.linked_organization_id == "already-linked-optscale-org-id"
    processor.api_modifier_client.create_organization.assert_not_called()
    processor.ext_client.update_agreement.assert_not_called()
    assert f"Organization already exists with id {existing.id}" in caplog.text
    assert "Organization on OptScale created" not in caplog.text


# -- create_employee --


async def test_create_employee_with_existing_user(
    make_processor: ProcessorBuilder,
    caplog: pytest.LogCaptureFixture,
    purchase_order: dict[str, Any],
    mocker: MockerFixture,
) -> None:
    """`create_employee` reuses the existing OptScale user and records `isNewUser`."""
    processor = make_processor(purchase_order)
    processor.optscale_auth_client.get_existing_user_info.return_value = mocker.Mock(
        json=mocker.Mock(
            return_value={
                "user_info": {
                    "id": "f0bd0c4a-7c55-45b7-8b58-27740e38789a",
                    "display_name": "Spider Man",
                    "email": "peter.parker@iamspiderman.com",
                }
            }
        )
    )
    expected_order = copy.deepcopy(purchase_order)
    for param in expected_order["parameters"]["fulfillment"]:
        if param["externalId"] == "isNewUser":
            param["value"] = None
    expected_parameters = expected_order["parameters"]
    processor.ext_client.update_order.return_value = expected_order

    with caplog.at_level(logging.INFO):
        employee_id, employee_email = await processor.create_employee()

    assert processor.order is expected_order
    assert employee_id == "f0bd0c4a-7c55-45b7-8b58-27740e38789a"
    assert employee_email == "pl@example.com"
    processor.optscale_auth_client.get_existing_user_info.assert_awaited_once_with("pl@example.com")
    processor.ext_client.update_order.assert_awaited_once_with(
        purchase_order["id"], parameters=expected_parameters
    )
    processor.api_modifier_client.create_user.assert_not_called()
    assert (
        "Employee exists with id f0bd0c4a-7c55-45b7-8b58-27740e38789a "
        f"for order {purchase_order['id']}"
    ) in caplog.text


async def test_create_employee_with_no_existing_user(
    make_processor: ProcessorBuilder,
    caplog: pytest.LogCaptureFixture,
    purchase_order: dict[str, Any],
    mocker: MockerFixture,
) -> None:
    """`create_employee` provisions a new OptScale user when none exists and flags `isNewUser`."""
    processor = make_processor(purchase_order)
    processor.optscale_auth_client.get_existing_user_info.side_effect = UserDoesNotExist(
        "pl@example.com"
    )
    created_user = mocker.Mock(
        json=mocker.Mock(
            return_value={
                "id": "f0bd0c4a-7c55-45b7-8b58-27740e38789a",
                "display_name": "Spider Man",
                "email": "peter.parker@iamspiderman.com",
            }
        )
    )
    processor.api_modifier_client.create_user.return_value = created_user
    expected_order = copy.deepcopy(purchase_order)
    for param in expected_order["parameters"]["fulfillment"]:
        if param["externalId"] == "isNewUser":
            param["value"] = ["Yes"]
    expected_parameters = expected_order["parameters"]
    processor.ext_client.update_order.return_value = expected_order

    with caplog.at_level(logging.INFO):
        employee_id, employee_email = await processor.create_employee()

    assert employee_id == "f0bd0c4a-7c55-45b7-8b58-27740e38789a"
    assert employee_email == "pl@example.com"
    processor.optscale_auth_client.get_existing_user_info.assert_awaited_once_with("pl@example.com")
    processor.ext_client.update_order.assert_awaited_once_with(
        purchase_order["id"], parameters=expected_parameters
    )
    processor.api_modifier_client.create_user.assert_awaited_once_with(
        email="pl@example.com",
        display_name="PL NN",
        password=mocker.ANY,
    )
    assert (
        "Employee created with id f0bd0c4a-7c55-45b7-8b58-27740e38789a "
        f"for order {purchase_order['id']}"
    ) in caplog.text


async def test_create_employee_keeps_recorded_new_user_flag_on_retry(
    make_processor: ProcessorBuilder, purchase_order: dict[str, Any], mocker: MockerFixture
) -> None:
    """`create_employee` keeps the recorded `isNewUser` value when the user now already exists."""
    for param in purchase_order["parameters"]["fulfillment"]:
        if param["externalId"] == "isNewUser":
            param["value"] = None
    processor = make_processor(purchase_order)
    processor.optscale_auth_client.get_existing_user_info.return_value = mocker.Mock(
        json=mocker.Mock(return_value={"user_info": {"id": "f0bd0c4a-7c55-45b7-8b58-27740e38789a"}})
    )
    expected_order = copy.deepcopy(purchase_order)
    processor.ext_client.update_order.return_value = expected_order

    employee_id, _ = await processor.create_employee()

    assert employee_id == "f0bd0c4a-7c55-45b7-8b58-27740e38789a"
    processor.ext_client.update_order.assert_awaited_once_with(
        purchase_order["id"], parameters=expected_order["parameters"]
    )


# -- subscriptions --


async def test_create_order_subscription_skips_when_subscription_already_exists(
    purchase_order: dict[str, Any], make_processor: ProcessorBuilder, mocker: MockerFixture
) -> None:
    """`create_order_subscription` does nothing when the line already has a subscription."""
    processor = make_processor(purchase_order)
    organization = mocker.Mock(id="b57b9964-7046-4e20-812c-01ab52cf4661")
    await processor.create_order_subscription(organization)
    processor.ext_client.create_subscription.assert_not_awaited()


async def test_create_order_subscription_creates_missing_subscription(
    order_factory: Callable[..., dict[str, Any]],
    make_processor: ProcessorBuilder,
    caplog: pytest.LogCaptureFixture,
    mocker: MockerFixture,
) -> None:
    """`create_order_subscription` creates and links a subscription for an uncovered line."""
    order = order_factory(
        order_type="Purchase",
        status="Processing",
        product_id="PRD-4141-4379",
        product_name="SoftwareOne FinOps for Cloud",
        subscriptions=[],
    )
    processor = make_processor(order)
    processor.ext_client.create_subscription.return_value = {"id": "SUB-9999-0001"}
    organization = mocker.Mock(id="b57b9964-7046-4e20-812c-01ab52cf4661")

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
    purchase_order: dict[str, Any],
    make_processor: ProcessorBuilder,
    mock_product_templates: TemplatesMocker,
    is_new: bool,
    expected_template_id: str,
) -> None:
    """`get_complete_template` selects the new/existing completed template by the `is_new` flag."""
    processor = make_processor(purchase_order)
    mock_product_templates(processor)
    template_id = await processor.get_complete_template(is_new)
    assert template_id == expected_template_id


# -- PurchaseOrderProcessor.send_reset_password --


async def test_send_reset_password_new_user_sends_reset(
    purchase_order: dict[str, Any],
    make_processor: ProcessorBuilder,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """`send_reset_password` triggers a password reset for a newly created user."""
    processor = make_processor(purchase_order)
    with caplog.at_level(logging.INFO):
        await processor.send_reset_password("pl@example.com", is_new=True)
    processor.optscale_client.reset_password.assert_awaited_once_with("pl@example.com")
    assert "Employee pl@example.com password reset sent" in caplog.text


async def test_send_reset_password_swallows_reset_failure(
    purchase_order: dict[str, Any],
    make_processor: ProcessorBuilder,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """`send_reset_password` logs and swallows a failure raised while sending the reset."""
    processor = make_processor(purchase_order)
    processor.optscale_client.reset_password.side_effect = Exception("OptScale down")
    with caplog.at_level(logging.ERROR):
        await processor.send_reset_password("pl@example.com", is_new=True)
    assert "Failed to reset password" in caplog.text


async def test_send_reset_password_existing_user_is_noop(
    purchase_order: dict[str, Any],
    make_processor: ProcessorBuilder,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """`send_reset_password` does nothing for an existing user."""
    processor = make_processor(purchase_order)
    with caplog.at_level(logging.INFO):
        await processor.send_reset_password("pl@example.com", is_new=False)
    processor.optscale_client.reset_password.assert_not_awaited()
    assert "No need to send reset password for pl@example.com" in caplog.text


# -- PurchaseOrderProcessor.process --


async def test_purchase_order_process_completes_order(
    make_processor: ProcessorBuilder,
    purchase_order: dict[str, Any],
    caplog: pytest.LogCaptureFixture,
    mocker: MockerFixture,
) -> None:
    """`process` runs every step in order and completes an existing-user purchase order."""
    processor = make_processor(purchase_order)
    organization = mocker.Mock(id="b57b9964-7046-4e20-812c-01ab52cf4661")

    mocked_validate = mocker.patch.object(processor, "validate_order")
    mocked_defaults = mocker.patch.object(processor, "apply_fulfillment_defaults")
    mocked_set_template = mocker.patch.object(processor, "set_processing_order_template")
    mocked_create_employee = mocker.patch.object(
        processor, "create_employee", return_value=("employee-id", "pl@example.com")
    )
    mocked_get_or_create_org = mocker.patch.object(
        processor, "get_or_create_organization", return_value=organization
    )
    mocked_create_subscription = mocker.patch.object(processor, "create_order_subscription")
    mocked_get_complete_template = mocker.patch.object(
        processor, "get_complete_template", return_value="TPL-0006"
    )
    mocked_send_reset_password = mocker.patch.object(processor, "send_reset_password")

    with caplog.at_level(logging.INFO):
        result = await processor.process()

    assert result.status is ProcessingStatus.COMPLETE
    mocked_validate.assert_awaited_once_with()
    mocked_defaults.assert_awaited_once_with()
    mocked_set_template.assert_awaited_once_with()
    mocked_create_employee.assert_awaited_once_with()
    mocked_get_or_create_org.assert_awaited_once_with("employee-id")
    mocked_create_subscription.assert_awaited_once_with(organization)
    # isNewUser has no value in the factory order -> existing user (is_new is False).
    mocked_get_complete_template.assert_awaited_once_with(False)
    processor.ext_client.complete_order.assert_awaited_once_with(
        order_id=purchase_order["id"],
        payload={
            "template": {"id": "TPL-0006"},
            "parameters": {"fulfillment": [{"externalId": "dueDate", "value": None}]},
        },
    )
    mocked_send_reset_password.assert_awaited_once_with("pl@example.com", False)
    assert f"Order {purchase_order['id']} has been completed" in caplog.text


async def test_purchase_order_process_new_user_branch(
    make_processor: ProcessorBuilder, purchase_order: dict[str, Any], mocker: MockerFixture
) -> None:
    """`process` completes with the new-user template and resets the password for new users."""
    for param in purchase_order["parameters"]["fulfillment"]:
        if param["externalId"] == "isNewUser":
            param["value"] = ["Yes"]
    processor = make_processor(purchase_order)
    organization = mocker.Mock(id="b57b9964-7046-4e20-812c-01ab52cf4661")

    mocker.patch.object(processor, "validate_order")
    mocker.patch.object(processor, "apply_fulfillment_defaults")
    mocker.patch.object(processor, "set_processing_order_template")
    mocker.patch.object(
        processor, "create_employee", return_value=("employee-id", "new@example.com")
    )
    mocker.patch.object(processor, "get_or_create_organization", return_value=organization)
    mocker.patch.object(processor, "create_order_subscription")
    mocked_get_complete_template = mocker.patch.object(
        processor, "get_complete_template", return_value="TPL-0005"
    )
    mocked_send_reset_password = mocker.patch.object(processor, "send_reset_password")

    await processor.process()

    mocked_get_complete_template.assert_awaited_once_with(True)
    processor.ext_client.complete_order.assert_awaited_once_with(
        order_id=purchase_order["id"],
        payload={
            "template": {"id": "TPL-0005"},
            "parameters": {"fulfillment": [{"externalId": PARAM_DUE_DATE, "value": None}]},
        },
    )
    mocked_send_reset_password.assert_awaited_once_with("new@example.com", True)


async def test_purchase_order_process_skips_when_order_moved_to_query(
    make_processor: ProcessorBuilder, purchase_order: dict[str, Any], mocker: MockerFixture
) -> None:
    """`process` returns a SKIP result and halts when validation moves the order to querying."""
    processor = make_processor(purchase_order)
    mocker.patch.object(
        processor, "validate_order", side_effect=OrderMovedToQuery(purchase_order["id"])
    )
    mocked_defaults = mocker.patch.object(processor, "apply_fulfillment_defaults")
    mocked_create_employee = mocker.patch.object(processor, "create_employee")

    result = await processor.process()

    assert result.status is ProcessingStatus.SKIP
    mocked_defaults.assert_not_awaited()
    mocked_create_employee.assert_not_awaited()
    processor.ext_client.complete_order.assert_not_awaited()


async def test_purchase_order_process_cancels_when_no_due_date(
    make_processor: ProcessorBuilder, purchase_order: dict[str, Any], mocker: MockerFixture
) -> None:
    """`process` fails the order and returns CANCEL when an error occurs and no due date is set."""
    for param in purchase_order["parameters"]["fulfillment"]:
        if param["externalId"] == PARAM_DUE_DATE:
            param["value"] = None
    processor = make_processor(purchase_order)
    mocker.patch.object(processor, "validate_order", side_effect=RuntimeError("boom"))

    result = await processor.process()

    assert result.status is ProcessingStatus.CANCEL
    processor.ext_client.fail_order.assert_awaited_once_with(
        order_id=purchase_order["id"], payload={"statusNotes": ERR_DUE_DATE_NOT_SET.to_dict()}
    )
    processor.ext_client.complete_order.assert_not_awaited()


@freeze_time("2024-12-01")
async def test_purchase_order_process_reschedules_before_due_date(
    make_processor: ProcessorBuilder, purchase_order: dict[str, Any], mocker: MockerFixture
) -> None:
    """`process` returns RESCHEDULE when an error occurs and the due date has not been reached."""
    # The factory order carries a due date of 2025-01-01.
    processor = make_processor(purchase_order)
    mocker.patch.object(processor, "validate_order", side_effect=RuntimeError("boom"))

    result = await processor.process()

    assert result.status is ProcessingStatus.RESCHEDULE
    assert result.message is not None
    assert "boom" in result.message
    processor.ext_client.fail_order.assert_not_awaited()


async def test_purchase_order_process_fails_when_due_date_reached(
    make_processor: ProcessorBuilder, purchase_order: dict[str, Any], mocker: MockerFixture
) -> None:
    """`process` fails the order and returns COMPLETE when an error occurs past the due date."""
    # The factory order carries a due date of 2025-01-01.
    processor = make_processor(purchase_order)
    mocker.patch.object(processor, "validate_order", side_effect=RuntimeError("boom"))
    mocker.patch("app.fulfilment.processing.date").today.return_value = date(2025, 6, 1)

    result = await processor.process()

    assert result.status is ProcessingStatus.COMPLETE
    processor.ext_client.fail_order.assert_awaited_once_with(
        order_id=purchase_order["id"],
        payload={"statusNotes": ERR_DUE_DATE_IS_REACHED.to_dict(due_date="2025-01-01")},
    )


async def test_change_order_process_fail(
    make_processor: ProcessorBuilder, change_order: dict[str, Any]
) -> None:
    processor = make_processor(change_order)
    result = await processor.process()
    assert result.status is ProcessingStatus.COMPLETE
    processor.ext_client.fail_order.assert_awaited_once_with(  # ty:ignore[unresolved-attribute]
        order_id=change_order["id"],
        payload={"statusNotes": ERR_ORDER_TYPE_NOT_SUPPORTED.to_dict(order_type="Change")},
    )


# TerminateOrderProcessor
async def test_terminated_order_process_completes_order(
    make_processor: ProcessorBuilder,
    terminate_order: dict[str, Any],
    mocker: MockerFixture,
) -> None:
    """`process` runs every step in order and completes an existing-user purchase order."""
    processor = make_processor(terminate_order)
    mocker.patch.object(processor, "get_product_template_id", return_value="TPL-1234-5678-0001")
    organization = mocker.Mock(id="FORG-8077-2461-7285", linked_organization_id="OPT-ORG-001")
    processor.ext_client.get_agreement.return_value = {
        "externalIds": {"client": "", "vendor": "FORG-8077-2461-7285"},
    }
    processor.organization_repo.first.return_value = organization
    processor.optscale_client.get_organization.return_value = mocker.Mock(
        json=mocker.Mock(
            return_value={
                "deleted_at": 0,
                "created_at": 1784036037,
                "id": "9939c1a3-fd82-4cd4-b749-5e85cf69b606",
                "name": "SPIDERMAN3232",
                "pool_id": "7a496040-46e2-4011-9c76-66a9830c595b",
                "is_demo": False,
                "currency": "USD",
                "cleaned_at": 0,
                "disabled": False,
            }
        )
    )
    result = await processor.process()
    assert result.status is ProcessingStatus.COMPLETE
    assert result.severity == "Info"
    assert result.message is not None
    assert "The Organization FORG-8077-2461-7285 was successfully suspended." in result.message
    processor.ext_client.complete_order.assert_awaited_once_with(
        order_id=terminate_order["id"],
        payload={
            "template": {"id": "TPL-1234-5678-0001"},
            "parameters": {"fulfillment": [{"externalId": PARAM_DUE_DATE, "value": None}]},
        },
    )
    processor.ext_client.get_agreement.assert_awaited_once_with(
        terminate_order["agreement"]["id"],
    )
    processor.optscale_client.get_organization.assert_awaited_once_with("OPT-ORG-001")
    processor.optscale_client.suspend_organization.assert_awaited_once_with("OPT-ORG-001")


async def test_terminate_cancels_when_order_has_no_due_date_parameter(
    make_processor: ProcessorBuilder,
    terminate_order: dict[str, Any],
) -> None:
    pass
    """The terminate flow cancels when the order declares no 'dueDate` parameter."""
    terminate_order["parameters"]["fulfillment"] = [
        param
        for param in terminate_order["parameters"]["fulfillment"]
        if param["externalId"] != PARAM_DUE_DATE
    ]
    processor = make_processor(terminate_order)
    result = await processor.process()
    assert result.status is ProcessingStatus.CANCEL
    assert result.message is not None
    assert result.message == ERR_DUE_DATE_NOT_SET.message
    processor.ext_client.update_order.assert_not_awaited()
    processor.optscale_client.suspend_organization.assert_not_awaited()


async def test_terminated_order_skip_suspend_when_optscale_org_is_disabled(
    make_processor: ProcessorBuilder,
    terminate_order: dict[str, Any],
    mocker: MockerFixture,
) -> None:
    """`process` runs every step in order and completes an existing-user purchase order."""
    processor = make_processor(terminate_order)
    mocker.patch.object(processor, "get_product_template_id", return_value="TPL-1234-5678-0001")
    organization = mocker.Mock(id="FORG-8077-2461-7285", linked_organization_id="OPT-ORG-001")
    processor.ext_client.get_agreement.return_value = {
        "externalIds": {"client": "", "vendor": "FORG-8077-2461-7285"},
    }
    processor.organization_repo.first.return_value = organization
    processor.optscale_client.get_organization.return_value = mocker.Mock(
        json=mocker.Mock(
            return_value={
                "deleted_at": 0,
                "created_at": 1784036037,
                "id": "9939c1a3-fd82-4cd4-b749-5e85cf69b606",
                "name": "SPIDERMAN3232",
                "pool_id": "7a496040-46e2-4011-9c76-66a9830c595b",
                "is_demo": False,
                "currency": "USD",
                "cleaned_at": 0,
                "disabled": True,
            }
        )
    )
    result = await processor.process()
    assert result.status is ProcessingStatus.COMPLETE
    assert result.severity == "Warning"
    assert result.message is not None
    assert "The Organization FORG-8077-2461-7285 was already terminated." in result.message
    processor.ext_client.complete_order.assert_awaited_once_with(
        order_id=terminate_order["id"],
        payload={
            "template": {"id": "TPL-1234-5678-0001"},
            "parameters": {"fulfillment": [{"externalId": PARAM_DUE_DATE, "value": None}]},
        },
    )
    processor.ext_client.get_agreement.assert_awaited_once_with(
        terminate_order["agreement"]["id"],
    )
    processor.optscale_client.get_organization.assert_awaited_once_with("OPT-ORG-001")
    processor.optscale_client.suspend_organization.assert_not_awaited()


async def test_terminated_order_cancel_when_organization_not_found(
    make_processor: ProcessorBuilder,
    terminate_order: dict[str, Any],
) -> None:
    processor = make_processor(terminate_order)

    processor.ext_client.get_agreement.return_value = {
        "externalIds": {"client": "", "vendor": "FORG-8077-2461-7285"},
    }
    processor.organization_repo.first.return_value = None

    result = await processor.process()
    assert result.status is ProcessingStatus.CANCEL
    assert result.severity == "Error"
    assert result.message is not None
    assert (
        "The organization FORG-8077-2461-7285 linked to agreement AGR-2119-4550-8674-5962 "
        "was not found." in result.message
    )

    processor.optscale_client.get_organization.assert_not_awaited()
    processor.optscale_client.suspend_organization.assert_not_awaited()
    processor.ext_client.complete_order.assert_not_awaited()


async def test_terminated_order_cancel_when_organization_not_linked(
    make_processor: ProcessorBuilder,
    terminate_order: dict[str, Any],
    mocker: MockerFixture,
) -> None:
    processor = make_processor(terminate_order)

    processor.ext_client.get_agreement.return_value = {
        "externalIds": {"client": "", "vendor": "FORG-8077-2461-7285"},
    }
    processor.organization_repo.first.return_value = mocker.Mock(
        id="FORG-8077-2461-7285", linked_organization_id=None
    )

    result = await processor.process()
    assert result.status is ProcessingStatus.CANCEL
    assert result.severity == "Error"
    assert result.message is not None
    assert (
        "The organization FORG-8077-2461-7285 is not linked to a FinOps for Cloud Organization."
        in result.message
    )

    processor.optscale_client.get_organization.assert_not_awaited()
    processor.optscale_client.suspend_organization.assert_not_awaited()
    processor.ext_client.complete_order.assert_not_awaited()


@freeze_time("2026-08-06")
async def test_terminated_order_reschedule_before_due_date_is_reached(
    make_processor: ProcessorBuilder,
    terminate_order: dict[str, Any],
) -> None:
    """process's returns RESCHEDULE when an error occurs and the due date has
    not been reached"""
    terminate_order = set_due_date(terminate_order, date(2026, 12, 12))
    processor = make_processor(terminate_order)
    processor.ext_client.get_agreement.side_effect = Exception("big error")

    result = await processor.process()
    assert result.status is ProcessingStatus.RESCHEDULE
    assert result.severity == "Warning"
    assert result.message is not None
    assert "An error occurred while processing the order: big error" in result.message
    processor.ext_client.fail_order.assert_not_awaited()
    processor.optscale_client.suspend_organization.assert_not_awaited()
    processor.ext_client.complete_order.assert_not_awaited()


@freeze_time("2026-08-06")
async def test_terminated_order_fails_when_before_due_date_is_reached(
    make_processor: ProcessorBuilder,
    terminate_order: dict[str, Any],
) -> None:
    """process fails the order and return COMPLETE when an error occurs and the
    due is in the past"""
    terminate_order = set_due_date(terminate_order, date(2026, 7, 12))
    processor = make_processor(terminate_order)
    processor.ext_client.get_agreement.side_effect = Exception("big error")

    result = await processor.process()
    assert result.status is ProcessingStatus.COMPLETE
    assert result.severity == "Error"
    assert result.message is not None
    processor.ext_client.fail_order.assert_awaited_once_with(
        order_id=terminate_order["id"],
        payload={"statusNotes": ERR_DUE_DATE_IS_REACHED.to_dict(due_date="2026-07-12")},
    )
    processor.optscale_client.suspend_organization.assert_not_awaited()
    processor.ext_client.complete_order.assert_not_awaited()


@freeze_time("2026-08-06")
async def test_terminated_order_cancel_when_no_due_date_is_set(
    make_processor: ProcessorBuilder,
    terminate_order: dict[str, Any],
) -> None:
    """process fails the order and return CANCEL when an error occurs and no due is set"""
    terminate_order = set_due_date(terminate_order, None)
    processor = make_processor(terminate_order)
    processor.ext_client.update_order.side_effect = Exception("big error")

    result = await processor.process()
    assert result.status is ProcessingStatus.CANCEL
    assert result.severity == "Error"
    assert result.message is not None
    assert "No due date fulfillment parameter found." in result.message
    processor.ext_client.fail_order.assert_awaited_once_with(
        order_id=terminate_order["id"],
        payload={"statusNotes": ERR_DUE_DATE_NOT_SET.to_dict()},
    )
    processor.ext_client.get_agreement.assert_not_awaited()
    processor.optscale_client.suspend_organization.assert_not_awaited()
    processor.ext_client.complete_order.assert_not_awaited()
