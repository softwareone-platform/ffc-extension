import pytest
from httpx import AsyncClient
from pytest_httpx import HTTPXMock
from pytest_mock import MockerFixture
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.conf import Settings
from app.db.models import Organization, System
from app.enums import OrganizationStatus
from tests.types import ModelFactory

# =================
# Get Organizations
# =================


async def test_get_all_organizations_empty_db(api_client: AsyncClient, ffc_jwt_token: str):
    response = await api_client.get(
        "/organizations", headers={"Authorization": f"Bearer {ffc_jwt_token}"}
    )

    assert response.status_code == 200
    assert response.json()["total"] == 0
    assert response.json()["items"] == []


async def test_get_organization_with_name_filter(
    organization_factory: ModelFactory[Organization], api_client: AsyncClient, ffc_jwt_token: str
):
    organization_1 = await organization_factory(
        operations_external_id="EXTERNAL_ID_1", name="Spider Man"
    )
    await organization_factory(operations_external_id="EXTERNAL_ID_2")
    response = await api_client.get(
        f"/organizations?eq(name,{organization_1.name})",
        headers={"Authorization": f"Bearer {ffc_jwt_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["name"] == organization_1.name
    assert len(data["items"]) == data["total"]


async def test_get_organization_with_name_filter_like_op(
    organization_factory: ModelFactory[Organization], api_client: AsyncClient, ffc_jwt_token: str
):
    organization_1 = await organization_factory(
        operations_external_id="EXTERNAL_ID_1", name="Spider Man"
    )
    organization_2 = await organization_factory(
        operations_external_id="EXTERNAL_ID_2", name="Spider Car"
    )
    response = await api_client.get(
        "/organizations?like(name,*Spider *)",
        headers={"Authorization": f"Bearer {ffc_jwt_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert sorted([data["items"][0]["name"], data["items"][1]["name"]]) == sorted(
        [organization_1.name, organization_2.name]
    )
    assert len(data["items"]) == data["total"]


async def test_get_organization_with_not_found_name_filter(
    organization_factory: ModelFactory[Organization], api_client: AsyncClient, ffc_jwt_token: str
):
    organization_1 = await organization_factory(
        operations_external_id="EXTERNAL_ID_1", name="Pippo"
    )
    await organization_factory(operations_external_id="EXTERNAL_ID_2", name="SpiderMan")
    response = await api_client.get(
        f"/organizations?ne(name,{organization_1.name})",
        headers={"Authorization": f"Bearer {ffc_jwt_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["name"] == "SpiderMan"
    assert len(data["items"]) == data["total"]


async def test_get_organization_with_updated_at_filter(
    organization_factory: ModelFactory[Organization], api_client: AsyncClient, ffc_jwt_token: str
):
    organization_1 = await organization_factory(operations_external_id="EXTERNAL_ID_1")
    response = await api_client.get(
        f"/organizations?eq(events.updated.at,{organization_1.updated_at.isoformat()})",
        headers={"Authorization": f"Bearer {ffc_jwt_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["events"]["updated"]["at"] == organization_1.updated_at.strftime(
        "%Y-%m-%dT%H:%M:%S.%fZ"
    )  # noqa: E501
    assert len(data["items"]) == data["total"]


async def test_get_organization_with_created_at_filter(
    organization_factory: ModelFactory[Organization], api_client: AsyncClient, ffc_jwt_token: str
):
    organization_1 = await organization_factory(operations_external_id="EXTERNAL_ID_1")
    response = await api_client.get(
        f"/organizations?eq(events.created.at,{organization_1.created_at.isoformat()})",
        headers={"Authorization": f"Bearer {ffc_jwt_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["events"]["created"]["at"] == organization_1.created_at.strftime(
        "%Y-%m-%dT%H:%M:%S.%fZ"
    )  # noqa: E501
    assert len(data["items"]) == data["total"]


async def test_get_organization_with_currency_filter(
    organization_factory: ModelFactory[Organization], api_client: AsyncClient, ffc_jwt_token: str
):
    organization_1 = await organization_factory(operations_external_id="EXTERNAL_ID_1")
    response = await api_client.get(
        f"/organizations?eq(currency,{organization_1.currency})",
        headers={"Authorization": f"Bearer {ffc_jwt_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["currency"] == organization_1.currency
    assert len(data["items"]) == data["total"]


async def test_get_organization_with_billing_currency_filter(
    organization_factory: ModelFactory[Organization], api_client: AsyncClient, ffc_jwt_token: str
):
    organization_1 = await organization_factory(operations_external_id="EXTERNAL_ID_1")
    response = await api_client.get(
        f"/organizations?eq(billing_currency,{organization_1.billing_currency})",
        headers={"Authorization": f"Bearer {ffc_jwt_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["billing_currency"] == organization_1.billing_currency
    assert len(data["items"]) == data["total"]


async def test_get_organization_with_status_filter(
    organization_factory: ModelFactory[Organization], api_client: AsyncClient, ffc_jwt_token: str
):
    await organization_factory(operations_external_id="EXTERNAL_ID_1")
    response = await api_client.get(
        "/organizations?eq(status,active)",
        headers={"Authorization": f"Bearer {ffc_jwt_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["status"] == "active"
    assert len(data["items"]) == data["total"]


async def test_get_organization_with_operations_external_id_filter(
    organization_factory: ModelFactory[Organization], api_client: AsyncClient, ffc_jwt_token: str
):
    tmp_org = await organization_factory(operations_external_id="EXTERNAL_ID_1")
    response = await api_client.get(
        f"/organizations?eq(operations_external_id,{tmp_org.operations_external_id})",
        headers={"Authorization": f"Bearer {ffc_jwt_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["status"] == "active"
    assert len(data["items"]) == data["total"]


async def test_get_organization_with_not_valid_filter(
    organization_factory: ModelFactory[Organization], api_client: AsyncClient, ffc_jwt_token: str
):
    await organization_factory(operations_external_id="EXTERNAL_ID_1")
    response = await api_client.get(
        "/organizations?eq(ciaociao,active)",
        headers={"Authorization": f"Bearer {ffc_jwt_token}"},
    )
    assert response.status_code == 400


async def test_get_all_organizations_single_page(
    organization_factory: ModelFactory[Organization], api_client: AsyncClient, ffc_jwt_token: str
):
    organization_1 = await organization_factory(operations_external_id="EXTERNAL_ID_1")
    organization_2 = await organization_factory(operations_external_id="EXTERNAL_ID_2")

    response = await api_client.get(
        "/organizations",
        headers={"Authorization": f"Bearer {ffc_jwt_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["items"]) == data["total"]
    assert {organization_1.id, organization_2.id} == {item["id"] for item in data["items"]}


async def test_get_all_organizations_multiple_pages(
    organization_factory: ModelFactory[Organization], api_client: AsyncClient, ffc_jwt_token: str
):
    for index in range(10):
        await organization_factory(
            name=f"Organization {index}",
            operations_external_id=f"EXTERNAL_ID_{index}",
        )

    first_page_response = await api_client.get(
        "/organizations",
        headers={"Authorization": f"Bearer {ffc_jwt_token}"},
        params={"limit": 5},
    )
    first_page_data = first_page_response.json()

    assert first_page_response.status_code == 200
    assert first_page_data["total"] == 10
    assert len(first_page_data["items"]) == 5
    assert first_page_data["limit"] == 5
    assert first_page_data["offset"] == 0

    second_page_response = await api_client.get(
        "/organizations",
        headers={"Authorization": f"Bearer {ffc_jwt_token}"},
        params={"limit": 3, "offset": 5},
    )
    second_page_data = second_page_response.json()

    assert second_page_response.status_code == 200
    assert second_page_data["total"] == 10
    assert len(second_page_data["items"]) == 3
    assert second_page_data["limit"] == 3
    assert second_page_data["offset"] == 5

    third_page_response = await api_client.get(
        "/organizations",
        headers={"Authorization": f"Bearer {ffc_jwt_token}"},
        params={"offset": 8},
    )
    third_page_data = third_page_response.json()

    assert third_page_response.status_code == 200
    assert third_page_data["total"] == 10
    assert len(third_page_data["items"]) == 2
    assert third_page_data["limit"] > 2
    assert third_page_data["offset"] == 8

    all_items = first_page_data["items"] + second_page_data["items"] + third_page_data["items"]
    all_external_ids = {item["operations_external_id"] for item in all_items}
    assert len(all_items) == 10
    assert sorted(all_external_ids) == sorted({f"EXTERNAL_ID_{index}" for index in range(10)})


# ====================
# Create Organizations
# ====================


async def test_can_create_organizations(
    mocker: MockerFixture,
    httpx_mock: HTTPXMock,
    api_client: AsyncClient,
    db_session: AsyncSession,
    ffc_jwt_token: str,
    ffc_extension: System,
):
    mocker.patch("app.api_clients.api_modifier.jwt.encode", return_value="test_token")

    httpx_mock.add_response(
        method="POST",
        headers={"Authorization": f"Bearer {ffc_jwt_token}"},
        url="https://api-modifier.ffc.com/organizations",
        json={"id": "UUID-yyyy-yyyy-yyyy-yyyy"},
        match_headers={"Authorization": "Bearer test_token"},
    )

    response = await api_client.post(
        "/organizations",
        headers={"Authorization": f"Bearer {ffc_jwt_token}"},
        json={
            "name": "My Organization",
            "operations_external_id": "ACC-1234-5678",
            "user_id": "UUID-xxxx-xxxx-xxxx-xxxx",
            "currency": "USD",
            "billing_currency": "EUR",
        },
    )

    assert response.status_code == 201
    data = response.json()

    assert data["id"] is not None
    assert data["name"] == "My Organization"
    assert data["currency"] == "USD"
    assert data["billing_currency"] == "EUR"
    assert data["operations_external_id"] == "ACC-1234-5678"
    assert data["linked_organization_id"] == "UUID-yyyy-yyyy-yyyy-yyyy"
    assert data["events"]["created"]["at"] is not None
    assert data["events"]["created"]["by"]["id"] == str(ffc_extension.id)
    assert data["events"]["created"]["by"]["type"] == ffc_extension.type
    assert data["events"]["created"]["by"]["name"] == ffc_extension.name
    assert data["events"]["updated"]["at"] is not None
    assert data["events"]["updated"]["by"]["id"] == str(ffc_extension.id)
    assert data["events"]["updated"]["by"]["type"] == ffc_extension.type
    assert data["events"]["updated"]["by"]["name"] == ffc_extension.name

    result = await db_session.execute(select(Organization).where(Organization.id == data["id"]))
    assert result.one_or_none() is not None


@pytest.mark.parametrize(
    "missing_field", ["name", "operations_external_id", "user_id", "currency", "billing_currency"]
)
async def test_create_organization_with_incomplete_data(
    api_client: AsyncClient, missing_field: str, ffc_jwt_token: str
):
    payload = {
        "name": "My Organization",
        "operations_external_id": "ACC-1234-5678",
        "user_id": "UUID-xxxx-xxxx-xxxx-xxxx",
        "currency": "USD",
        "billing_currency": "USD",
    }
    payload.pop(missing_field)

    response = await api_client.post(
        "/organizations",
        json=payload,
        headers={"Authorization": f"Bearer {ffc_jwt_token}"},
    )

    assert response.status_code == 422
    [detail] = response.json()["detail"]

    assert detail["type"] == "missing"
    assert detail["loc"] == ["body", missing_field]


async def test_create_organization_with_existing_db_organization(
    mocker: MockerFixture,
    httpx_mock: HTTPXMock,
    api_client: AsyncClient,
    organization_factory: ModelFactory[Organization],
    ffc_jwt_token: str,
):
    mocker.patch("app.api_clients.api_modifier.jwt.encode", return_value="test_token")

    existing_org = await organization_factory(operations_external_id="ACC-1234-5678")
    payload = {
        "name": existing_org.name,
        "operations_external_id": "ACC-1234-5678",
        "user_id": "UUID-xxxx-xxxx-xxxx-xxxx",
        "currency": "USD",
        "billing_currency": "USD",
    }

    httpx_mock.add_response(
        method="POST",
        headers={"Authorization": f"Bearer {ffc_jwt_token}"},
        url="https://api-modifier.ffc.com/organizations",
        json={"id": "UUID-yyyy-yyyy-yyyy-yyyy"},
        match_headers={"Authorization": "Bearer test_token"},
    )

    response = await api_client.post(
        "/organizations",
        json=payload,
        headers={"Authorization": f"Bearer {ffc_jwt_token}"},
    )

    assert response.status_code == 201
    data = response.json()

    assert data["id"] == str(existing_org.id)
    assert data["name"] == existing_org.name
    assert data["operations_external_id"] == "ACC-1234-5678"
    assert data["linked_organization_id"] == "UUID-yyyy-yyyy-yyyy-yyyy"
    assert data["events"]["created"]["at"] is not None


async def test_create_organization_with_existing_db_organization_name_mismatch(
    mocker: MockerFixture,
    httpx_mock: HTTPXMock,
    api_client: AsyncClient,
    organization_factory: ModelFactory[Organization],
    ffc_jwt_token: str,
):
    mocker.patch("app.api_clients.api_modifier.jwt.encode", return_value="test_token")

    existing_org = await organization_factory(operations_external_id="ACC-1234-5678")
    payload = {
        "name": f"{existing_org.name} Existing",
        "operations_external_id": "ACC-1234-5678",
        "user_id": "UUID-xxxx-xxxx-xxxx-xxxx",
        "currency": "USD",
        "billing_currency": "USD",
    }

    response = await api_client.post(
        "/organizations",
        json=payload,
        headers={"Authorization": f"Bearer {ffc_jwt_token}"},
    )

    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail == (
        f"The name of a partially created Organization with "
        f"external ID {existing_org.operations_external_id}  doesn't match the "
        f"current request: {existing_org.name}."
    )


async def test_create_organization_already_created(
    api_client: AsyncClient, organization_factory: ModelFactory[Organization], ffc_jwt_token: str
):
    payload = {
        "name": "My Organization",
        "operations_external_id": "ACC-1234-5678",
        "user_id": "UUID-xxxx-xxxx-xxxx-xxxx",
        "currency": "USD",
        "billing_currency": "USD",
    }

    await organization_factory(
        operations_external_id="ACC-1234-5678",
        linked_organization_id="957c9a0a-2d18-4015-b7b0-e1b4259b3167",
    )

    response = await api_client.post(
        "/organizations",
        json=payload,
        headers={"Authorization": f"Bearer {ffc_jwt_token}"},
    )

    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail == "An Organization with external ID `ACC-1234-5678` already exists."


async def test_create_organization_api_modifier_error(
    mocker: MockerFixture,
    httpx_mock: HTTPXMock,
    api_client: AsyncClient,
    ffc_jwt_token: str,
):
    httpx_mock.add_response(
        method="POST",
        url="https://api-modifier.ffc.com/organizations",
        status_code=500,
        text="Internal Server Error",
    )

    response = await api_client.post(
        "/organizations",
        json={
            "name": "My Organization",
            "operations_external_id": "ACC-1234-5678",
            "user_id": "UUID-xxxx-xxxx-xxxx-xxxx",
            "currency": "USD",
            "billing_currency": "AUD",
        },
        headers={"Authorization": f"Bearer {ffc_jwt_token}"},
    )

    assert response.status_code == 502

    detail = response.json()["detail"]
    assert detail == "Error creating organization in FinOps for Cloud: 500 - Internal Server Error."


async def test_create_employee_affiliate_forbidden(
    api_client: AsyncClient,
    gcp_jwt_token: str,
):
    response = await api_client.post(
        "/organizations",
        json={
            "name": "My Organization",
            "operations_external_id": "ACC-1234-5678",
            "user_id": "UUID-xxxx-xxxx-xxxx-xxxx",
            "currency": "USD",
            "billing_currency": "GBP",
        },
        headers={"Authorization": f"Bearer {gcp_jwt_token}"},
    )
    assert response.status_code == 403
    assert response.json() == {
        "detail": "You've found the door, but you don't have the key.",
    }


# =====================
# Get Organization by ID
# ======================


async def test_get_organization_by_id(
    organization_factory: ModelFactory[Organization],
    api_client: AsyncClient,
    ffc_jwt_token: str,
    ffc_extension: System,
):
    org = await organization_factory(
        created_by=ffc_extension,
        updated_by=ffc_extension,
    )
    response = await api_client.get(
        f"/organizations/{org.id}", headers={"Authorization": f"Bearer {ffc_jwt_token}"}
    )

    assert response.status_code == 200
    data = response.json()

    assert data["id"] == str(org.id)
    assert data["name"] == org.name
    assert data["operations_external_id"] == org.operations_external_id
    assert data["events"]["created"]["at"] is not None
    assert data["events"]["created"]["by"]["id"] == str(ffc_extension.id)
    assert data["events"]["created"]["by"]["type"] == ffc_extension.type
    assert data["events"]["created"]["by"]["name"] == ffc_extension.name
    assert data["events"]["updated"]["at"] is not None
    assert data["events"]["updated"]["by"]["id"] == str(ffc_extension.id)
    assert data["events"]["updated"]["by"]["type"] == ffc_extension.type
    assert data["events"]["updated"]["by"]["name"] == ffc_extension.name


async def test_get_non_existant_organization(api_client: AsyncClient, ffc_jwt_token: str):
    not_found_id = "FORG-1234-5678-9012"
    response = await api_client.get(
        f"/organizations/{not_found_id}", headers={"Authorization": f"Bearer {ffc_jwt_token}"}
    )

    assert response.status_code == 404
    assert response.json()["detail"] == f"Organization with ID `{not_found_id}` wasn't found."


async def test_get_invalid_id_format(api_client: AsyncClient, ffc_jwt_token: str):
    response = await api_client.get(
        "/organizations/this-is-not-a-valid-uuid",
        headers={"Authorization": f"Bearer {ffc_jwt_token}"},
    )

    assert response.status_code == 422

    [detail] = response.json()["detail"]
    assert detail["loc"] == ["path", "organization_id"]
    assert detail["type"] == "string_pattern_mismatch"


# ===================
# Update Organization
# ===================


@pytest.mark.parametrize(
    ("updated_external_id", "expected_status_code"),
    [
        pytest.param("", 422, id="too_short"),
        pytest.param("super_long_ext_id" * 20, 422, id="too_long"),
        pytest.param("updated_external_id", 200, id="just_right"),
    ],
)
async def test_update_organization_external_id(
    organization_factory: ModelFactory[Organization],
    operations_client: AsyncClient,
    httpx_mock: HTTPXMock,
    db_session: AsyncSession,
    updated_external_id: str,
    expected_status_code: int,
):
    db_org = await organization_factory(
        name="initial_name",
        currency="EUR",
        operations_external_id="initial_external_id",
    )

    response = await operations_client.put(
        f"/organizations/{db_org.id}",
        json={"operations_external_id": updated_external_id},
    )

    assert response.status_code == expected_status_code

    # If we want to only update the operations_external_id,
    # we should not make requests to an external API
    assert not httpx_mock.get_request()

    await db_session.refresh(db_org)

    if response.is_error:
        assert db_org.operations_external_id == "initial_external_id"
    else:
        response_data = response.json()

        assert response_data["id"] == db_org.id
        assert response_data["operations_external_id"] == updated_external_id
        assert db_org.operations_external_id == updated_external_id


@pytest.mark.parametrize(
    ("org_to_update_status", "existing_org_status", "expected_status_code"),
    [
        pytest.param(OrganizationStatus.ACTIVE, OrganizationStatus.ACTIVE, 400),
        pytest.param(OrganizationStatus.ACTIVE, OrganizationStatus.CANCELLED, 400),
        pytest.param(OrganizationStatus.CANCELLED, OrganizationStatus.CANCELLED, 400),
        pytest.param(OrganizationStatus.ACTIVE, OrganizationStatus.DELETED, 200),
        pytest.param(OrganizationStatus.DELETED, OrganizationStatus.ACTIVE, 200),
        pytest.param(OrganizationStatus.DELETED, OrganizationStatus.DELETED, 200),
    ],
)
async def test_update_organization_external_id_unique_for_non_deleted_objects(
    organization_factory: ModelFactory[Organization],
    operations_client: AsyncClient,
    httpx_mock: HTTPXMock,
    db_session: AsyncSession,
    org_to_update_status: OrganizationStatus,
    existing_org_status: OrganizationStatus,
    expected_status_code: int,
):
    db_org = await organization_factory(
        name="organization_to_update",
        currency="EUR",
        operations_external_id="initial_external_id",
        status=org_to_update_status,
    )

    # creating another organization to test the operations_external_id uniqueness
    await organization_factory(
        name="existing_organization",
        currency="GBP",
        operations_external_id="existing_external_id",
        status=existing_org_status,
    )

    response = await operations_client.put(
        f"/organizations/{db_org.id}",
        json={"name": "organization_to_update", "operations_external_id": "existing_external_id"},
    )

    assert response.status_code == expected_status_code
    response_data = response.json()

    # If we want to only update the operations_external_id,
    # we should not make requests to an external API
    assert not httpx_mock.get_request()

    await db_session.refresh(db_org)

    if response.is_error:
        assert db_org.operations_external_id == "initial_external_id"
        assert (
            response_data["detail"]
            == "An organization with the same operations_external_id already exists."
        )
    else:
        assert response_data["id"] == db_org.id
        assert response_data["operations_external_id"] == "existing_external_id"
        assert db_org.operations_external_id == "existing_external_id"


@pytest.mark.parametrize(
    (
        "updated_name",
        "expected_status_code",
        "should_call_api_modifier",
        "api_modifier_status_code",
    ),
    [
        pytest.param("", 422, False, None, id="too_short"),
        pytest.param("super_long_name" * 20, 422, False, None, id="too_long"),
        pytest.param("updated_name", 502, True, 500, id="api_modifier_error"),
        pytest.param("updated_name", 200, True, 200, id="just_right"),
    ],
)
async def test_update_organization_name(
    organization_factory: ModelFactory[Organization],
    operations_client: AsyncClient,
    httpx_mock: HTTPXMock,
    db_session: AsyncSession,
    updated_name: str,
    expected_status_code: int,
    should_call_api_modifier: bool,
    api_modifier_status_code: int | None,
):
    db_org = await organization_factory(
        name="initial_name",
        currency="EUR",
        operations_external_id="initial_external_id",
        linked_organization_id="ORG-123",
    )

    if should_call_api_modifier:
        assert api_modifier_status_code is not None

        httpx_mock.add_response(
            method="PATCH",
            headers={"Authorization": operations_client.headers["Authorization"]},
            url=f"https://opt-api.ffc.com/organizations/{db_org.linked_organization_id}",
            status_code=api_modifier_status_code,
            json={
                "id": db_org.linked_organization_id,
                "name": updated_name,
            },
        )

    response = await operations_client.put(
        f"/organizations/{db_org.id}",
        json={"name": updated_name},
    )

    assert bool(httpx_mock.get_request()) == should_call_api_modifier
    assert response.status_code == expected_status_code
    await db_session.refresh(db_org)

    if response.is_error:
        assert db_org.name == "initial_name"
    else:
        response_data = response.json()

        assert response_data["id"] == db_org.id
        assert response_data["name"] == updated_name
        assert db_org.name == updated_name


@pytest.mark.parametrize(
    ("api_modifier_status_code", "expected_status_code"),
    [
        pytest.param(500, 502, id="api_modifier_error"),
        pytest.param(200, 200, id="success"),
    ],
)
async def test_update_organization_both_fields(
    organization_factory: ModelFactory[Organization],
    operations_client: AsyncClient,
    httpx_mock: HTTPXMock,
    db_session: AsyncSession,
    api_modifier_status_code: int,
    expected_status_code: int,
):
    db_org = await organization_factory(
        name="initial_name",
        currency="EUR",
        operations_external_id="initial_external_id",
        linked_organization_id="ORG-123",
    )

    httpx_mock.add_response(
        method="PATCH",
        headers={"Authorization": operations_client.headers["Authorization"]},
        url=f"https://opt-api.ffc.com/organizations/{db_org.linked_organization_id}",
        status_code=api_modifier_status_code,
        json={
            "id": db_org.linked_organization_id,
            "name": "updated_name",
        },
    )

    response = await operations_client.put(
        f"/organizations/{db_org.id}",
        json={"name": "updated_name", "operations_external_id": "updated_external_id"},
    )

    assert response.status_code == expected_status_code
    await db_session.refresh(db_org)

    if response.is_error:
        # Make sure that the organization hasn't been updated
        # (most notably the operations_external_id change has been rolled back)
        assert db_org.name == "initial_name"
        assert db_org.operations_external_id == "initial_external_id"
    else:
        response_data = response.json()

        assert response_data["id"] == db_org.id
        assert response_data["name"] == "updated_name"
        assert response_data["operations_external_id"] == "updated_external_id"

        assert db_org.name == "updated_name"
        assert db_org.operations_external_id == "updated_external_id"


@pytest.mark.parametrize(
    "set_operations_external_id",
    [
        pytest.param(True, id="only_name"),
        pytest.param(False, id="name_and_operations_external_id"),
    ],
)
async def test_try_update_name_for_organization_without_linked_organization_id(
    organization_factory: ModelFactory[Organization],
    operations_client: AsyncClient,
    db_session: AsyncSession,
    httpx_mock: HTTPXMock,
    set_operations_external_id: bool,
):
    db_org = await organization_factory(
        name="initial_name",
        currency="EUR",
        operations_external_id="initial_external_id",
        linked_organization_id=None,
    )

    json_payload = {"name": "updated_name"}
    if set_operations_external_id:
        json_payload["operations_external_id"] = "updated_external_id"

    response = await operations_client.put(f"/organizations/{db_org.id}", json=json_payload)

    assert not httpx_mock.get_request()

    await db_session.refresh(db_org)

    assert response.status_code == 400
    assert (
        response.json()["detail"]
        == "Organization initial_name has no associated FinOps for Cloud organization."
    )

    assert db_org.name == "initial_name"
    assert db_org.operations_external_id == "initial_external_id"


# ====================
# Create Organizations
# ====================


async def test_delete_organization(
    test_settings: Settings,
    organization_factory: ModelFactory[Organization],
    operations_client: AsyncClient,
    httpx_mock: HTTPXMock,
    db_session: AsyncSession,
):
    db_org = await organization_factory(
        name="Test organization",
        linked_organization_id="UUID-1234-5678-9098-7654",
    )
    httpx_mock.add_response(
        method="PATCH",
        headers={"Authorization": operations_client.headers["Authorization"]},
        url=f"{test_settings.optscale_rest_api_base_url}/organizations/{db_org.linked_organization_id}",
        status_code=200,
        json={
            "id": db_org.linked_organization_id,
            "disabled": True,
        },
    )

    assert db_org.status == OrganizationStatus.ACTIVE
    assert db_org.deleted_at is None

    response = await operations_client.delete(f"/organizations/{db_org.id}")
    assert response.status_code == 204
    assert bool(httpx_mock.get_request())

    await db_session.refresh(db_org)
    assert db_org.status == OrganizationStatus.DELETED
    assert db_org.deleted_at is not None

    response = await operations_client.delete(f"/organizations/{db_org.id}")
    assert response.status_code == 400
    assert response.json()["detail"] == f"Organization {db_org.name} is already deleted."


async def test_delete_organization_optscale_issue(
    test_settings: Settings,
    organization_factory: ModelFactory[Organization],
    operations_client: AsyncClient,
    httpx_mock: HTTPXMock,
    db_session: AsyncSession,
):
    db_org = await organization_factory(
        name="Test organization",
        linked_organization_id="UUID-1234-5678-9098-7654",
    )
    httpx_mock.add_response(
        method="PATCH",
        headers={"Authorization": operations_client.headers["Authorization"]},
        url=f"{test_settings.optscale_rest_api_base_url}/organizations/{db_org.linked_organization_id}",
        status_code=500,
        text="Internal Server Error",
    )

    assert db_org.status == OrganizationStatus.ACTIVE
    assert db_org.deleted_at is None

    response = await operations_client.delete(f"/organizations/{db_org.id}")

    await db_session.refresh(db_org)

    assert db_org.status == OrganizationStatus.ACTIVE
    assert db_org.deleted_at is None

    assert response.status_code == 502
    assert (
        f"Error deleting organization {db_org.linked_organization_id} in FinOps for Cloud."
    ) in response.json()["detail"]


async def test_get_organization_with_linked_organization_id_filter(
    organization_factory: ModelFactory[Organization], api_client: AsyncClient, ffc_jwt_token: str
):
    await organization_factory(
        name="First Test Organization",
        operations_external_id="EXTERNAL_ID_1",
        linked_organization_id="UUID-1234-5678-9098-7654",
    )
    await organization_factory(
        name="Second Test Organization",
        operations_external_id="EXTERNAL_ID_2",
        linked_organization_id="UUID-5678-1234-9098-7654",
    )
    response = await api_client.get(
        "/organizations?eq(linked_organization_id,UUID-1234-5678-9098-7654)",
        headers={"Authorization": f"Bearer {ffc_jwt_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["name"] == "First Test Organization"
