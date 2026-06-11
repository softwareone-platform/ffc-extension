import copy
from unittest.mock import AsyncMock, Mock

from app.api_clients.optscale import UserDoesNotExist
from app.db.handlers import OrganizationHandler
from app.db.models import Organization
from app.fulfilment.provisioning import create_employee, get_or_create_organization


async def test_get_or_create_organization(mocker, order_factory, db_session):
    ext_client = AsyncMock()
    organization_repo = OrganizationHandler(db_session)
    api_modifier_client = AsyncMock()
    agreement_body = {
        "$meta": {"omitted": ["split"]},
        "id": "AGR-2234-7614-1678",
        "name": "SoftwareOne FinOps for Cloud for Stuart Meeks Corp",
        "revision": 1,
        "status": "Active",
        "listing": {"id": "LST-9168-7963", "name": "LST-9168-7963", "revision": 1},
        "authorization": {
            "id": "AUT-3727-1184",
            "name": "SoftwareOne FinOps for Cloud (USD)",
            "revision": 1,
            "externalIds": {"operations": "sfc-auth-us-01"},
            "currency": "USD",
            "notes": "",
            "product": {
                "id": "PRD-7208-0459",
                "name": "SoftwareOne FinOps for Cloud",
                "icon": "/v1/catalog/products/PRD-7208-0459/icon",
                "revision": 1,
                "externalIds": {},
                "status": "Published",
            },
            "vendor": {
                "id": "ACC-3805-2089",
                "name": "SoftwareOne Vendor",
                "icon": "/v1/accounts/accounts/ACC-3805-2089/icon",
                "revision": 3,
                "type": "Vendor",
                "status": "Active",
            },
            "owner": {
                "id": "SEL-7282-9889",
                "name": "SoftwareOne, Inc.",
                "icon": "/v1/accounts/sellers/SEL-7282-9889/icon",
                "revision": 2,
                "externalId": "78ADB9DA-BC69-4CBF-BAA0-CDBC28619EF7",
            },
            "statistics": {"subscriptions": 21, "agreements": 23, "sellers": 1, "listings": 1},
            "journal": {"firstInvoiceDate": "2025-02-01T00:00:00.000Z", "frequency": "1m"},
            "eligibility": {"client": True, "partner": False},
            "audit": {
                "created": {
                    "at": "2024-10-25T04:41:00.053Z",
                    "by": {"id": "USR-0249-0848", "name": "Stuart Meeks", "revision": 1},
                },
                "updated": {
                    "at": "2024-10-25T04:41:30.649Z",
                    "by": {"id": "USR-0249-0848", "name": "Stuart Meeks", "revision": 1},
                },
            },
        },
        "vendor": {
            "id": "ACC-3805-2089",
            "name": "SoftwareOne Vendor",
            "icon": "/v1/accounts/accounts/ACC-3805-2089/icon",
            "revision": 3,
            "type": "Vendor",
            "status": "Active",
        },
        "client": {
            "id": "ACC-3131-4670",
            "name": "Stuart Meeks Corp",
            "revision": 1,
            "type": "Client",
            "status": "Enabled",
        },
        "price": {"PPxY": 0.00000, "PPxM": 0.00000, "currency": "USD"},
        "template": {"id": "TPL-7208-0459-0003", "name": "Default", "revision": 1},
        "lines": [],
        "assets": [],
        "subscriptions": [
            {
                "id": "SUB-1467-4028-7539",
                "name": "Subscription for SoftwareOne FinOps for Cloud",
                "revision": 0,
            }
        ],
        "parameters": {
            "ordering": [
                {
                    "id": "PAR-7208-0459-0001",
                    "externalId": "organizationName",
                    "name": "Organization name",
                    "type": "SingleLineText",
                    "phase": "Order",
                    "scope": "Agreement",
                    "multiple": False,
                    "displayValue": "Avengers Inc",
                    "value": "Avengers Inc",
                },
                {
                    "id": "PAR-7208-0459-0002",
                    "externalId": "organizationAdmin",
                    "name": "Administrator email",
                    "type": "SingleLineText",
                    "phase": "Order",
                    "scope": "Agreement",
                    "multiple": False,
                    "displayValue": "will.smith@avengersinc.com",
                    "value": "will.smith@avengersinc.com",
                },
            ],
            "fulfillment": [
                {
                    "id": "PAR-7208-0459-0003",
                    "externalId": "organizationId",
                    "name": "Organization ID",
                    "type": "SingleLineText",
                    "phase": "Fulfillment",
                    "scope": "Agreement",
                    "multiple": False,
                    "displayValue": "bc4cd95d-ca9c-45d9-a774-8ecd12ddab05",
                    "value": "bc4cd95d-ca9c-45d9-a774-8ecd12ddab05",
                }
            ],
        },
        "licensee": {
            "id": "LCE-4895-5875-2075",
            "name": "Meeks Corp HQ - Seller SEL-7282-9889",
            "revision": 1,
        },
        "buyer": {"id": "BUY-5975-3862", "name": "Meeks Corp HQ", "revision": 1},
        "seller": {
            "id": "SEL-7282-9889",
            "name": "SoftwareOne, Inc.",
            "icon": "/v1/accounts/sellers/SEL-7282-9889/icon",
            "revision": 2,
            "externalId": "78ADB9DA-BC69-4CBF-BAA0-CDBC28619EF7",
        },
        "product": {
            "id": "PRD-7208-0459",
            "name": "SoftwareOne FinOps for Cloud",
            "icon": "/v1/catalog/products/PRD-7208-0459/icon",
            "revision": 1,
            "externalIds": {},
            "status": "Published",
        },
        "externalIds": {"client": ""},
        "termsAndConditions": [
            {
                "id": "TCS-7208-0459-0001",
                "name": "SoftwareOne FinOps for Cloud - Terms and Conditions",
                "revision": 1,
                "accepted": "2024-10-25T05:02:05.677Z",
                "acceptedBy": {"id": "USR-0249-0848", "name": "Stuart Meeks", "revision": 1},
            }
        ],
        "certificates": [],
        "audit": {
            "created": {
                "at": "2024-10-25T04:57:10.241Z",
                "by": {"id": "USR-0249-0848", "name": "Stuart Meeks", "revision": 1},
            },
            "updated": {
                "at": "2024-10-25T05:02:05.481Z",
                "by": {"id": "USR-0249-0848", "name": "Stuart Meeks", "revision": 1},
            },
        },
    }
    api_modifier_client.create_organization.return_value = Mock(
        json=Mock(return_value={"id": "optscale-org-id"})
    )
    order = order_factory(
        order_type="Purchase",
        status="Processing",
        product_id="PRD-4141-4379",
        product_name="SoftwareOne FinOps for Cloud",
    )
    agreement_id = order["agreement"]["id"]
    mocker.patch.object(ext_client, "get_agreement", return_value=agreement_body)
    mocked_update_agreement = mocker.patch.object(ext_client, "update_agreement")

    result = await get_or_create_organization(
        ext_client, api_modifier_client, order, organization_repo, "employee-id"
    )
    assert result.operations_external_id == agreement_id
    assert result.name == "ACME Inc"
    assert result.currency == "USD"
    assert result.billing_currency == "USD"
    assert result.linked_organization_id == "optscale-org-id"

    api_modifier_client.create_organization.assert_called_once_with(
        org_name="ACME Inc", user_id="employee-id", currency="USD"
    )
    mocked_update_agreement.assert_called_once_with(agreement_id, externalIds={"vendor": result.id})


async def test_get_or_create_organization_already_exists(mocker, order_factory, db_session):
    ext_client = AsyncMock()
    organization_repo = OrganizationHandler(db_session)
    api_modifier_client = AsyncMock()

    order = order_factory(
        order_type="Purchase",
        status="Processing",
        product_id="PRD-4141-4379",
        product_name="SoftwareOne FinOps for Cloud",
    )
    agreement_id = order["agreement"]["id"]

    # Seed the organization the function should find — same key get_or_create filters on.
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
        ext_client, "get_agreement", return_value={"authorization": {"currency": "USD"}}
    )
    mocked_update_agreement = mocker.patch.object(ext_client, "update_agreement")

    result = await get_or_create_organization(
        ext_client, api_modifier_client, order, organization_repo, "employee-id"
    )

    assert result.id == existing.id
    assert result.name == "Pre-existing ORG"
    assert result.currency == "EUR"
    assert result.linked_organization_id == "already-linked-optscale-org-id"

    api_modifier_client.create_organization.assert_not_called()
    mocked_update_agreement.assert_not_called()


async def test_create_employee_with_existing_user(mocker, order_factory, db_session):
    ext_client = AsyncMock()
    api_modifier_client = AsyncMock()
    optscale_auth_client = AsyncMock()
    order = order_factory(
        order_type="Purchase",
        status="Processing",
        product_id="PRD-4141-4379",
        product_name="SoftwareOne FinOps for Cloud",
    )

    mock_response = Mock()
    mock_response.json.return_value = {
        "user_info": {
            "id": "f0bd0c4a-7c55-45b7-8b58-27740e38789a",
            "display_name": "Spider Man",
            "email": "peter.parker@iamspiderman.com",
        }
    }
    mocker.patch.object(
        optscale_auth_client,
        "get_existing_user_info",
        return_value=mock_response,
    )
    expected_order = copy.deepcopy(order)
    for param in expected_order["parameters"]["fulfillment"]:
        if param["externalId"] == "isNewUser":
            param["value"] = None

    expected_parameters = expected_order["parameters"]
    mocked_update_order = mocker.patch.object(
        ext_client, "update_order", return_value=expected_order
    )

    response, employee_id, employee_email = await create_employee(
        ext_client=ext_client,
        api_modifier_client=api_modifier_client,
        optscale_auth_client=optscale_auth_client,
        order=order,
    )
    assert response is expected_order
    assert employee_id == "f0bd0c4a-7c55-45b7-8b58-27740e38789a"
    optscale_auth_client.get_existing_user_info.assert_called_once_with("pl@example.com")
    mocked_update_order.assert_called_once_with(order["id"], parameters=expected_parameters)
    api_modifier_client.create_user.assert_not_called()


async def test_create_employee_with_no_existing_user(mocker, order_factory, db_session):
    ext_client = AsyncMock()
    api_modifier_client = AsyncMock()
    optscale_auth_client = AsyncMock()
    order = order_factory(
        order_type="Purchase",
        status="Processing",
        product_id="PRD-4141-4379",
        product_name="SoftwareOne FinOps for Cloud",
    )

    mock_response = Mock()
    mock_response.json.return_value = {
        "id": "f0bd0c4a-7c55-45b7-8b58-27740e38789a",
        "display_name": "Spider Man",
        "email": "peter.parker@iamspiderman.com",
    }
    mocker.patch.object(
        optscale_auth_client,
        "get_existing_user_info",
        side_effect=UserDoesNotExist("pl@example.com"),
    )

    expected_order = copy.deepcopy(order)
    for param in expected_order["parameters"]["fulfillment"]:
        if param["externalId"] == "isNewUser":
            param["value"] = ["Yes"]

    expected_parameters = expected_order["parameters"]
    mocked_update_order = mocker.patch.object(
        ext_client, "update_order", return_value=expected_order
    )

    api_modifier_client.create_user.return_value = mock_response
    response, employee_id, employee_email = await create_employee(
        ext_client=ext_client,
        api_modifier_client=api_modifier_client,
        optscale_auth_client=optscale_auth_client,
        order=order,
    )
    assert response is expected_order
    assert employee_id == "f0bd0c4a-7c55-45b7-8b58-27740e38789a"
    optscale_auth_client.get_existing_user_info.assert_called_once_with("pl@example.com")
    mocked_update_order.assert_called_once_with(order["id"], parameters=expected_parameters)
    api_modifier_client.create_user.assert_called_once_with(
        email="pl@example.com",
        display_name="PL NN",
        password=mocker.ANY,
    )


async def test_create_employee_with_(mocker, order_factory):
    """Retry: user now exists, but order already recorded isNewUser=['Yes']."""
    order = order_factory(
        order_type="Purchase",
        status="Processing",
        product_id="PRD-4141-4379",
        product_name="SoftwareOne FinOps for Cloud",
    )
    for param in order["parameters"]["fulfillment"]:
        if param["externalId"] == "isNewUser":
            param["value"] = None

    ext_client = AsyncMock()
    api_modifier_client = AsyncMock()
    optscale_auth_client = AsyncMock()

    mock_response = Mock()
    mock_response.json.return_value = {"user_info": {"id": "f0bd0c4a-7c55-45b7-8b58-27740e38789a"}}
    optscale_auth_client.get_existing_user_info.return_value = mock_response

    expected_order = copy.deepcopy(order)
    mocked_update_order = mocker.patch.object(
        ext_client, "update_order", return_value=expected_order
    )

    response, employee_id, employee_email = await create_employee(
        ext_client=ext_client,
        api_modifier_client=api_modifier_client,
        optscale_auth_client=optscale_auth_client,
        order=order,
    )

    assert response is expected_order
    assert employee_id == "f0bd0c4a-7c55-45b7-8b58-27740e38789a"
    mocked_update_order.assert_called_once_with(
        order["id"], parameters=expected_order["parameters"]
    )
