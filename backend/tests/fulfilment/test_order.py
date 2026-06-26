import copy
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from pytest_mock import MockerFixture

from app.api_clients.mpt import MPTClient, MPTExtensionAuth
from app.conf import Settings
from app.db.handlers import OrganizationHandler
from app.fulfilment import templates as templates_module
from app.fulfilment.constants import (
    COMPLETED_TEMPLATE_TYPE,
    PROCESSING_TEMPLATE_TYPE,
    PURCHASE_EXISTING_TEMPLATE_NAME,
    PURCHASE_TEMPLATE_NAME,
    QUERYING_TEMPLATE_TYPE,
)
from app.fulfilment.order import (
    apply_fulfillment_defaults,
    fulfill_order,
    start_task_and_get_order,
    validate_and_move_to_querying_if_needed,
)
from app.schemas.core import EventResponse

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


# -- apply_fulfillment_defaults_if_needed --


async def test_do_not_apply_fulfillment_defaults(mocker, order_factory, test_settings: Settings):
    ext_client = AsyncMock()
    order = order_factory(
        order_type="Purchase",
        status="Processing",
        product_id="PRD-4141-4379",
        product_name="SoftwareOne FinOps for Cloud",
    )
    mocker.patch.object(ext_client, "get_templates_by_product_id", return_value=order)
    response = await apply_fulfillment_defaults(ext_client, order, test_settings)
    assert response == order


async def test_apply_fulfillment_defaults(mocker, order_factory, test_settings: Settings):
    ext_client = AsyncMock()
    order = order_factory(
        order_type="Purchase",
        status="Processing",
        product_id="PRD-4141-4379",
        product_name="SoftwareOne FinOps for Cloud",
    )
    for param in order["parameters"]["fulfillment"]:
        if param["externalId"] in {
            "dueDate",
            "billedPercentage",
            "trialStartDate",
            "trialEndDate",
        }:
            param["value"] = None
    expected_order = copy.deepcopy(order)
    mocker.patch.object(ext_client, "update_order", return_value=expected_order)
    response = await apply_fulfillment_defaults(ext_client, order, test_settings)
    assert response == expected_order


async def test_apply_fulfillment_defaults_should_return_same_order_when_no_parameter_changes_needed(
    mocker, order_factory, test_settings: Settings
):
    ext_client = AsyncMock()
    order = order_factory(
        order_type="Purchase",
        status="Processing",
        product_id="PRD-4141-4379",
        product_name="SoftwareOne FinOps for Cloud",
    )

    order["parameters"].pop("fulfillment", None)
    mocked_update = mocker.patch.object(ext_client, "update_order")

    with pytest.raises(KeyError):
        await apply_fulfillment_defaults(ext_client, order, test_settings)

    mocked_update.assert_not_called()


# -- start_task_and_get_order --
async def test_start_task_and_get_order(mocker, order_factory):
    ext_client = AsyncMock()
    order = order_factory(
        order_type="Purchase",
        status="Processing",
        product_id="PRD-4141-4379",
        product_name="SoftwareOne FinOps for Cloud",
    )
    task_id = "TSK-1234-1234-1234-4527"
    order_id = order["id"]
    ext_ctx = SimpleNamespace(instance_id="INS-4321-4321-4321")
    client = MPTClient(MPTExtensionAuth())

    mocked_start_task = mocker.patch.object(ext_client, "start_task")
    mocked_get_order = mocker.patch.object(client, "get_order", return_value=order)

    response = await start_task_and_get_order(
        task_id=task_id,
        order_id=order_id,
        ext_ctx=ext_ctx,
        ext_client=ext_client,
        client=client,
    )

    assert response == order
    mocked_start_task.assert_called_once_with(task_id, ext_ctx.instance_id)
    mocked_get_order.assert_called_once_with(order_id)


# -- validate_and_move_to_querying_if_needed --


async def test_valid_order_doesnot_need_to_move_to_querying(order_factory):
    ext_client = AsyncMock()
    order = order_factory(
        order_type="Purchase",
        status="Processing",
        product_id="PRD-4141-4379",
        product_name="SoftwareOne FinOps for Cloud",
    )
    response, validated = await validate_and_move_to_querying_if_needed(
        order=order, ext_client=ext_client
    )
    assert validated
    assert response == order


async def test_invalid_order_moved_to_querying(mocker, order_factory):
    ext_client = AsyncMock()
    order = order_factory(
        order_type="Purchase",
        status="Processing",
        product_id="PRD-4141-4379",
        product_name="SoftwareOne FinOps for Cloud",
    )
    order["parameters"]["ordering"][0]["value"] = None
    mocker.patch.object(
        ext_client, "get_templates_by_product_id", Mock(side_effect=lambda **_: _templates_gen())
    )
    expected_order = copy.deepcopy(order)
    expected_order["status"] = "Querying"
    expected_order["parameters"]["ordering"][0]["externalId"] = "organizationName"
    mocker.patch.object(ext_client, "update_order", return_value=expected_order)
    mocker.patch.object(ext_client, "set_status_to_querying", return_value=expected_order)

    response, validated = await validate_and_move_to_querying_if_needed(
        order=order, ext_client=ext_client
    )
    assert not validated
    assert "error" in response["parameters"]["ordering"][0]
    assert response == expected_order
    assert response["parameters"]["ordering"][0]["error"].message == "Organization name is required"


@pytest.mark.parametrize(
    ("is_new_user_value", "expected_completed_template_id"),
    [
        pytest.param(["Yes"], "TPL-0005", id="new-user"),
        pytest.param(None, "TPL-0006", id="existing-user"),
    ],
)
async def test_fulfill_order_success(
    mocker,
    order_factory,
    is_new_user_value,
    expected_completed_template_id,
    db_session,
):
    ext_client = AsyncMock()
    organization_repo = OrganizationHandler(db_session)
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
        # No pre-existing subscriptions -> forces the subscription creation path.
        subscriptions=[],
    )
    for param in order["parameters"]["fulfillment"]:
        if param["externalId"] == "isNewUser":
            param["value"] = is_new_user_value

    processing_order = copy.deepcopy(order)
    processing_order["template"]["id"] = "TPL-0001"
    organization = Mock(
        id="b57b9964-7046-4e20-812c-01ab52cf4661", currency="USD", name="My Big ORG"
    )
    api_modifier_client = AsyncMock()
    optscale_auth_client = AsyncMock()
    optscale_client = AsyncMock()
    task_id = "TSK-1234-1234-1234"

    mocker.patch.object(
        ext_client,
        "get_templates_by_product_id",
        Mock(side_effect=lambda **_: _templates_gen()),
    )
    mocked_update_order = mocker.patch.object(
        ext_client, "update_order", return_value=processing_order
    )
    mocked_create_employee = mocker.patch(
        "app.fulfilment.order.create_employee",
        return_value=(processing_order, "employee-id", "peter.parker@spiderman.com"),
    )
    mocked_get_or_create_organization = mocker.patch(
        "app.fulfilment.order.get_or_create_organization",
        return_value=organization,
    )
    mocked_create_subscription = mocker.patch.object(
        ext_client, "create_subscription", return_value={"id": "SUB-0001"}
    )
    mocked_complete_order = mocker.patch.object(ext_client, "complete_order")
    mocked_complete_task = mocker.patch.object(ext_client, "complete_task")

    response = await fulfill_order(
        api_modifier_client=api_modifier_client,
        ext_client=ext_client,
        optscale_auth_client=optscale_auth_client,
        optscale_client=optscale_client,
        order=order,
        order_id=order["id"],
        organization_repo=organization_repo,
        task_id=task_id,
    )

    assert response == EventResponse.ok()

    # The processing template was switched to the "Purchase" one.
    mocked_update_order.assert_called_once_with(order_id=order["id"], template={"id": "TPL-0001"})
    mocked_create_employee.assert_called_once_with(
        ext_client, api_modifier_client, optscale_auth_client, processing_order
    )
    mocked_get_or_create_organization.assert_called_once_with(
        ext_client, api_modifier_client, processing_order, organization_repo, "employee-id"
    )
    # A subscription was created for the order line, bound to the organization.
    line = order["lines"][0]
    mocked_create_subscription.assert_called_once_with(
        order_id=order["id"],
        subscription={
            "name": f"Subscription for {line['item']['name']}",
            "parameters": {},
            "externalIds": {"vendor": organization.id},
            "lines": [{"id": line["id"]}],
        },
    )
    # The order was completed with the template matching the new/existing-user branch.
    mocked_complete_order.assert_called_once_with(
        order_id=order["id"], payload={"template": {"id": expected_completed_template_id}}
    )
    mocked_complete_task.assert_called_once_with(task_id)
    if is_new_user_value == ["Yes"]:
        optscale_client.reset_password.assert_awaited_once_with("peter.parker@spiderman.com")
    else:
        optscale_client.reset_password.assert_not_awaited()


async def test_fulfill_order_new_user_password_reset_failure_is_swallowed(
    mocker,
    order_factory,
    db_session,
    caplog,
):
    # New-user order whose password reset fails: the error must be logged and
    # swallowed, the order/task still completed, and the response still OK.
    ext_client = AsyncMock()
    organization_repo = OrganizationHandler(db_session)
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
        subscriptions=[],
    )
    for param in order["parameters"]["fulfillment"]:
        if param["externalId"] == "isNewUser":
            param["value"] = ["Yes"]

    processing_order = copy.deepcopy(order)
    processing_order["template"]["id"] = "TPL-0001"
    organization = Mock(
        id="b57b9964-7046-4e20-812c-01ab52cf4661", currency="USD", name="My Big ORG"
    )
    api_modifier_client = AsyncMock()
    optscale_auth_client = AsyncMock()
    optscale_client = AsyncMock()
    task_id = "TSK-1234-1234-1234"

    mocker.patch.object(
        ext_client,
        "get_templates_by_product_id",
        Mock(side_effect=lambda **_: _templates_gen()),
    )
    mocker.patch.object(ext_client, "update_order", return_value=processing_order)
    mocker.patch(
        "app.fulfilment.order.create_employee",
        return_value=(processing_order, "employee-id", "peter.parker@spiderman.com"),
    )
    mocker.patch(
        "app.fulfilment.order.get_or_create_organization",
        return_value=organization,
    )
    mocker.patch.object(ext_client, "create_subscription", return_value={"id": "SUB-0001"})
    mocked_complete_order = mocker.patch.object(ext_client, "complete_order")
    mocked_complete_task = mocker.patch.object(ext_client, "complete_task")
    optscale_client.reset_password.side_effect = Exception("boom")

    response = await fulfill_order(
        api_modifier_client=api_modifier_client,
        ext_client=ext_client,
        optscale_auth_client=optscale_auth_client,
        optscale_client=optscale_client,
        order=order,
        order_id=order["id"],
        organization_repo=organization_repo,
        task_id=task_id,
    )

    assert response == EventResponse.ok()
    optscale_client.reset_password.assert_awaited_once_with("peter.parker@spiderman.com")
    mocked_complete_order.assert_called_once_with(
        order_id=order["id"], payload={"template": {"id": "TPL-0005"}}
    )
    mocked_complete_task.assert_called_once_with(task_id)
    assert "Failed to reset password" in caplog.messages
