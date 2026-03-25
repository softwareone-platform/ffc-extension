from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from pytest_httpx import HTTPXMock
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.conf import Settings
from app.db.models import Account, Entitlement, System
from app.enums import AccountStatus, DatasourceType, EntitlementStatus, OrganizationStatus
from tests.types import JWTTokenFactory, ModelFactory

# ====================
# Authentication Tests
# ====================


async def test_get_entitlements_without_token(api_client: AsyncClient):
    response = await api_client.get("/entitlements")

    assert response.status_code == 401
    assert response.json()["detail"] == "Unauthorized."


async def test_get_entitlements_with_invalid_token(api_client: AsyncClient):
    response = await api_client.get(
        "/entitlements",
        headers={"Authorization": "Bearer invalid.token.here"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Unauthorized."


async def test_get_entitlements_with_expired_token(
    api_client: AsyncClient,
    jwt_token_factory: JWTTokenFactory,
    gcp_extension: System,
):
    expired_time = datetime.now(UTC) - timedelta(hours=1)
    expired_token = jwt_token_factory(
        str(gcp_extension.id),
        gcp_extension.jwt_secret,
        exp=expired_time,
    )

    response = await api_client.get(
        "/entitlements",
        headers={"Authorization": f"Bearer {expired_token}"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Unauthorized."


# ====================
# Create Entitlements
# ====================


async def test_can_create_entitlements(
    api_client: AsyncClient,
    gcp_jwt_token: str,
    gcp_extension: System,
    db_session: AsyncSession,
):
    response = await api_client.post(
        "/entitlements",
        headers={"Authorization": f"Bearer {gcp_jwt_token}"},
        json={
            "name": "AWS",
            "affiliate_external_id": "EXTERNAL_ID_987123",
            "datasource_id": "SPONSOR_CONTAINER_ID_1234",
        },
    )
    assert response.status_code == 201
    data = response.json()

    assert data["id"] is not None
    assert data["name"] == "AWS"
    assert data["affiliate_external_id"] == "EXTERNAL_ID_987123"
    assert data["datasource_id"] == "SPONSOR_CONTAINER_ID_1234"
    assert data["status"] == "new"
    assert data["events"]["created"]["at"] is not None
    assert data["events"]["created"]["by"]["id"] == str(gcp_extension.id)
    assert data["events"]["created"]["by"]["type"] == gcp_extension.type
    assert data["events"]["created"]["by"]["name"] == gcp_extension.name
    assert data["events"]["updated"]["at"] is not None
    assert data["events"]["updated"]["by"]["id"] == str(gcp_extension.id)
    assert data["events"]["updated"]["by"]["type"] == gcp_extension.type
    assert data["events"]["updated"]["by"]["name"] == gcp_extension.name

    result = await db_session.execute(select(Entitlement).where(Entitlement.id == data["id"]))
    assert result.one_or_none() is not None


async def test_create_entitlement_with_incomplete_data(api_client: AsyncClient, gcp_jwt_token: str):
    response = await api_client.post(
        "/entitlements",
        headers={"Authorization": f"Bearer {gcp_jwt_token}"},
        json={
            "name": "AWS",
            "affiliate_external_id": "EXTERNAL_ID_987123",
        },
    )

    assert response.status_code == 422
    [detail] = response.json()["detail"]

    assert detail["type"] == "missing"
    assert detail["loc"] == ["body", "datasource_id"]


async def test_create_entitlement_by_affiliate_with_owner(
    api_client: AsyncClient,
    gcp_jwt_token: str,
):
    response = await api_client.post(
        "/entitlements",
        headers={"Authorization": f"Bearer {gcp_jwt_token}"},
        json={
            "name": "AWS",
            "affiliate_external_id": "EXTERNAL_ID_987123",
            "datasource_id": "ds-id",
            "owner": {"id": "FACC-1234"},
        },
    )

    assert response.status_code == 400
    error_msg = response.json()["detail"]

    assert error_msg == "Affiliate accounts cannot provide an owner for an Entitlement."


async def test_create_entitlement_by_affiliate_with_redeem_at(
    api_client: AsyncClient,
    gcp_jwt_token: str,
):
    response = await api_client.post(
        "/entitlements",
        headers={"Authorization": f"Bearer {gcp_jwt_token}"},
        json={
            "name": "AWS",
            "affiliate_external_id": "EXTERNAL_ID_987123",
            "datasource_id": "ds-id",
            "redeem_at": datetime.now(UTC).isoformat(),
        },
    )

    assert response.status_code == 400
    error_msg = response.json()["detail"]

    assert error_msg == "Affiliate accounts cannot provide a redeem_at for an Entitlement."


async def test_create_entitlement_by_operations_with_owner(
    api_client: AsyncClient,
    ffc_jwt_token: str,
    affiliate_account: Account,
):
    response = await api_client.post(
        "/entitlements",
        headers={"Authorization": f"Bearer {ffc_jwt_token}"},
        json={
            "name": "AWS",
            "affiliate_external_id": "EXTERNAL_ID_987123",
            "datasource_id": "ds-id",
            "owner": {"id": affiliate_account.id},
            "redeem_at": datetime.now(UTC).isoformat(),
        },
    )

    assert response.status_code == 201
    entitlement = response.json()
    assert entitlement["owner"]["id"] == affiliate_account.id
    assert entitlement["redeem_at"] is not None


async def test_create_entitlement_by_operations_without_owner(
    api_client: AsyncClient,
    ffc_jwt_token: str,
):
    response = await api_client.post(
        "/entitlements",
        headers={"Authorization": f"Bearer {ffc_jwt_token}"},
        json={
            "name": "AWS",
            "affiliate_external_id": "EXTERNAL_ID_987123",
            "datasource_id": "ds-id",
        },
    )

    assert response.status_code == 400
    error = response.json()["detail"]
    assert error == "Operations accounts must provide an owner for an Entitlement."


@pytest.mark.parametrize(
    "account_status",
    [AccountStatus.DELETED, AccountStatus.DISABLED],
)
async def test_create_entitlement_by_operations_with_not_active_owner(
    api_client: AsyncClient,
    ffc_jwt_token: str,
    account_factory: ModelFactory[Account],
    account_status: AccountStatus,
):
    affiliate = await account_factory(
        status=account_status,
    )
    response = await api_client.post(
        "/entitlements",
        headers={"Authorization": f"Bearer {ffc_jwt_token}"},
        json={
            "name": "AWS",
            "affiliate_external_id": "EXTERNAL_ID_987123",
            "datasource_id": "ds-id",
            "owner": {"id": affiliate.id},
        },
    )

    assert response.status_code == 400
    error = response.json()["detail"]
    assert error == f"No Active Affiliate Account has been found with ID {affiliate.id}."


async def test_create_entitlement_by_operations_with_owner_not_affiliate(
    api_client: AsyncClient,
    ffc_jwt_token: str,
    account_factory: ModelFactory[Account],
    operations_account: Account,
):
    response = await api_client.post(
        "/entitlements",
        headers={"Authorization": f"Bearer {ffc_jwt_token}"},
        json={
            "name": "AWS",
            "affiliate_external_id": "EXTERNAL_ID_987123",
            "datasource_id": "ds-id",
            "owner": {"id": operations_account.id},
        },
    )

    assert response.status_code == 400
    error = response.json()["detail"]
    assert error == (f"No Active Affiliate Account has been found with ID {operations_account.id}.")


# ================
# Get Entitlements
# ================


async def test_get_all_entitlements_empty_db(api_client: AsyncClient, gcp_jwt_token: str):
    response = await api_client.get(
        "/entitlements",
        headers={"Authorization": f"Bearer {gcp_jwt_token}"},
    )

    assert response.status_code == 200
    assert response.json()["total"] == 0
    assert response.json()["items"] == []


async def test_get_all_entitlements_single_page(
    entitlement_gcp: Entitlement, api_client: AsyncClient, gcp_jwt_token: str
):
    response = await api_client.get(
        "/entitlements",
        headers={"Authorization": f"Bearer {gcp_jwt_token}"},
    )

    assert response.status_code == 200
    data = response.json()

    assert data["total"] == 1
    assert len(data["items"]) == data["total"]
    assert data["items"][0]["id"] == entitlement_gcp.id


async def test_get_all_entitlements_single_page_with_name_filter(
    entitlement_gcp: Entitlement, api_client: AsyncClient, gcp_jwt_token: str
):
    response = await api_client.get(
        "/entitlements?eq(name,GCP)",
        headers={"Authorization": f"Bearer {gcp_jwt_token}"},
    )

    assert response.status_code == 200
    data = response.json()

    assert data["total"] == 1
    assert len(data["items"]) == data["total"]
    assert data["items"][0]["id"] == entitlement_gcp.id


async def test_get_all_entitlements_single_page_with_created_at_filter(
    entitlement_gcp: Entitlement, api_client: AsyncClient, gcp_jwt_token: str
):
    response = await api_client.get(
        f"/entitlements?eq(events.created.at,{entitlement_gcp.created_at.isoformat()})",
        headers={"Authorization": f"Bearer {gcp_jwt_token}"},
    )

    assert response.status_code == 200
    data = response.json()

    assert data["total"] == 1
    assert len(data["items"]) == data["total"]
    assert data["items"][0]["id"] == entitlement_gcp.id


async def test_get_all_entitlements_single_page_with_updated_at_filter(
    entitlement_gcp: Entitlement,
    api_client: AsyncClient,
    gcp_jwt_token: str,
):
    response = await api_client.get(
        f"/entitlements?eq(events.updated.at,{entitlement_gcp.updated_at.isoformat()})",
        headers={"Authorization": f"Bearer {gcp_jwt_token}"},
    )

    assert response.status_code == 200
    data = response.json()

    assert data["total"] == 1
    assert len(data["items"]) == data["total"]
    assert data["items"][0]["id"] == entitlement_gcp.id


async def test_get_all_entitlements_single_page_with_no_matching_name_filter(
    entitlement_gcp: Entitlement, api_client: AsyncClient, gcp_jwt_token: str
):
    response = await api_client.get(
        "/entitlements?ne(name,GCP)",
        headers={"Authorization": f"Bearer {gcp_jwt_token}"},
    )

    assert response.status_code == 200
    data = response.json()

    assert data["total"] == 0


async def test_get_all_entitlements_single_page_with_datasource_id_filter(
    entitlement_gcp: Entitlement, api_client: AsyncClient, gcp_jwt_token: str
):
    response = await api_client.get(
        f"/entitlements?eq(datasource_id,{entitlement_gcp.datasource_id})",
        headers={"Authorization": f"Bearer {gcp_jwt_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["items"]) == data["total"]
    assert data["items"][0]["id"] == entitlement_gcp.id


async def test_get_all_entitlements_single_page_with_status_filter(
    entitlement_gcp: Entitlement, api_client: AsyncClient, gcp_jwt_token: str
):
    response = await api_client.get(
        "/entitlements?eq(status,new)",
        headers={"Authorization": f"Bearer {gcp_jwt_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["items"]) == data["total"]
    assert data["items"][0]["status"] == "new"
    assert data["items"][0]["id"] == entitlement_gcp.id


async def test_get_all_entitlements_multiple_pages(
    entitlement_factory: ModelFactory[Entitlement],
    api_client: AsyncClient,
    gcp_extension: System,
    gcp_account: Account,
    gcp_jwt_token: str,
):
    for index in range(10):
        await entitlement_factory(
            name="AWS",
            affiliate_external_id=f"EXTERNAL_ID_{index}",
            datasource_id=f"CONTAINER_ID_{index}",
            owner=gcp_account,
        )

    count_response = await api_client.get(
        "/entitlements",
        headers={"Authorization": f"Bearer {gcp_jwt_token}"},
        params={"limit": 0},
    )
    count_response_data = count_response.json()
    assert count_response.status_code == 200
    assert count_response_data["total"] == 10
    assert count_response_data["items"] == []
    assert count_response_data["limit"] == 0
    assert count_response_data["offset"] == 0

    first_page_response = await api_client.get(
        "/entitlements",
        headers={"Authorization": f"Bearer {gcp_jwt_token}"},
        params={"limit": 5},
    )
    first_page_data = first_page_response.json()
    assert first_page_response.status_code == 200
    assert first_page_data["total"] == 10
    assert len(first_page_data["items"]) == 5
    assert first_page_data["limit"] == 5
    assert first_page_data["offset"] == 0

    second_page_response = await api_client.get(
        "/entitlements",
        headers={"Authorization": f"Bearer {gcp_jwt_token}"},
        params={"limit": 3, "offset": 5},
    )
    second_page_data = second_page_response.json()

    assert second_page_response.status_code == 200
    assert second_page_data["total"] == 10
    assert len(second_page_data["items"]) == 3
    assert second_page_data["limit"] == 3
    assert second_page_data["offset"] == 5

    third_page_response = await api_client.get(
        "/entitlements",
        headers={"Authorization": f"Bearer {gcp_jwt_token}"},
        params={"offset": 8},
    )
    third_page_data = third_page_response.json()

    assert third_page_response.status_code == 200
    assert third_page_data["total"] == 10
    assert len(third_page_data["items"]) == 2
    assert third_page_data["limit"] > 2
    assert third_page_data["offset"] == 8

    all_items = first_page_data["items"] + second_page_data["items"] + third_page_data["items"]
    all_external_ids = {item["affiliate_external_id"] for item in all_items}
    assert len(all_items) == 10
    assert all_external_ids == {f"EXTERNAL_ID_{index}" for index in range(10)}


# =====================
# Get Entitlement by ID
# =====================


async def test_get_entitlement_by_id(
    entitlement_gcp: Entitlement,
    api_client: AsyncClient,
    gcp_jwt_token: str,
    gcp_extension: System,
):
    response = await api_client.get(
        f"/entitlements/{entitlement_gcp.id}",
        headers={"Authorization": f"Bearer {gcp_jwt_token}"},
    )

    assert response.status_code == 200
    data = response.json()

    assert data["id"] == str(entitlement_gcp.id)
    assert data["name"] == entitlement_gcp.name
    assert data["affiliate_external_id"] == entitlement_gcp.affiliate_external_id
    assert data["datasource_id"] == entitlement_gcp.datasource_id
    assert data["status"] == "new"
    assert data["events"]["created"]["at"] is not None
    assert data["events"]["created"]["by"]["id"] == str(gcp_extension.id)
    assert data["events"]["created"]["by"]["type"] == gcp_extension.type
    assert data["events"]["created"]["by"]["name"] == gcp_extension.name
    assert data["events"]["updated"]["at"] is not None
    assert data["events"]["updated"]["by"]["id"] == str(gcp_extension.id)
    assert data["events"]["updated"]["by"]["type"] == gcp_extension.type
    assert data["events"]["updated"]["by"]["name"] == gcp_extension.name


async def test_get_entitlement_by_id_operations(
    entitlement_gcp: Entitlement,
    api_client: AsyncClient,
    ffc_jwt_token: str,
    gcp_extension: System,
):
    response = await api_client.get(
        f"/entitlements/{entitlement_gcp.id}",
        headers={"Authorization": f"Bearer {ffc_jwt_token}"},
    )

    assert response.status_code == 200
    data = response.json()

    assert data["id"] == str(entitlement_gcp.id)
    assert data["name"] == entitlement_gcp.name
    assert data["affiliate_external_id"] == entitlement_gcp.affiliate_external_id
    assert data["datasource_id"] == entitlement_gcp.datasource_id
    assert data["status"] == "new"
    assert data["events"]["created"]["at"] is not None
    assert data["events"]["created"]["by"]["id"] == str(gcp_extension.id)
    assert data["events"]["created"]["by"]["type"] == gcp_extension.type
    assert data["events"]["created"]["by"]["name"] == gcp_extension.name
    assert data["events"]["updated"]["at"] is not None
    assert data["events"]["updated"]["by"]["id"] == str(gcp_extension.id)
    assert data["events"]["updated"]["by"]["type"] == gcp_extension.type
    assert data["events"]["updated"]["by"]["name"] == gcp_extension.name


async def test_get_non_existant_entitlement(api_client: AsyncClient, gcp_jwt_token: str):
    id = "FENT-1234-5678-9012"
    response = await api_client.get(
        f"/entitlements/{id}",
        headers={"Authorization": f"Bearer {gcp_jwt_token}"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == f"Entitlement with ID `{id}` wasn't found."


async def test_get_invalid_id_format(api_client: AsyncClient, gcp_jwt_token: str):
    response = await api_client.get(
        "/entitlements/this-is-not-a-valid-uuid",
        headers={"Authorization": f"Bearer {gcp_jwt_token}"},
    )

    assert response.status_code == 422

    [detail] = response.json()["detail"]
    assert detail["loc"] == ["path", "id"]
    assert detail["type"] == "string_pattern_mismatch"


# =====================
# Terminate Entitlement
# =====================


async def test_terminate_entitlement_success(
    entitlement_gcp: Entitlement,
    api_client: AsyncClient,
    gcp_jwt_token: str,
    gcp_extension: System,
    db_session: AsyncSession,
):
    assert entitlement_gcp.terminated_at is None
    assert entitlement_gcp.terminated_by is None
    assert entitlement_gcp.status == EntitlementStatus.NEW

    entitlement_gcp.status = EntitlementStatus.ACTIVE

    db_session.add(entitlement_gcp)
    await db_session.commit()
    await db_session.refresh(entitlement_gcp)

    request_start_dt = datetime.now(UTC)
    response = await api_client.post(
        f"/entitlements/{entitlement_gcp.id}/terminate",
        headers={"Authorization": f"Bearer {gcp_jwt_token}"},
    )
    request_end_dt = datetime.now(UTC)

    assert response.status_code == 200
    data = response.json()

    assert data["id"] == str(entitlement_gcp.id)
    assert data["status"] == "terminated"

    await db_session.refresh(entitlement_gcp)

    assert entitlement_gcp.status == EntitlementStatus.TERMINATED
    assert entitlement_gcp.terminated_at is not None
    assert request_start_dt < entitlement_gcp.terminated_at < request_end_dt
    assert entitlement_gcp.terminated_by_id == gcp_extension.id

    assert (
        datetime.fromisoformat(data["events"]["terminated"]["at"]) == entitlement_gcp.terminated_at
    )
    assert data["events"]["terminated"]["by"]["id"] == gcp_extension.id
    assert data["events"]["terminated"]["by"]["type"] == gcp_extension.type._value_
    assert data["events"]["terminated"]["by"]["name"] == gcp_extension.name


async def test_terminate_new_entitlement(
    entitlement_gcp: Entitlement,
    api_client: AsyncClient,
    gcp_jwt_token: str,
):
    assert entitlement_gcp.status == EntitlementStatus.NEW

    response = await api_client.post(
        f"/entitlements/{entitlement_gcp.id}/terminate",
        headers={"Authorization": f"Bearer {gcp_jwt_token}"},
    )

    assert response.status_code == 400
    error_msg = response.json()["detail"]

    assert error_msg == "Only active entitlements can be terminated, current status is new."


async def test_terminate_already_terminated_entitlement(
    entitlement_gcp: Entitlement,
    api_client: AsyncClient,
    gcp_jwt_token: str,
    db_session: AsyncSession,
):
    entitlement_gcp.status = EntitlementStatus.TERMINATED

    db_session.add(entitlement_gcp)
    await db_session.commit()

    response = await api_client.post(
        f"/entitlements/{entitlement_gcp.id}/terminate",
        headers={"Authorization": f"Bearer {gcp_jwt_token}"},
    )

    assert response.status_code == 400
    error_msg = response.json()["detail"]

    assert error_msg == "Entitlement is already terminated."


async def test_terminate_non_existant_entitlement(
    api_client: AsyncClient,
    gcp_jwt_token: str,
    gcp_extension: System,
    db_session: AsyncSession,
):
    entitlement_id = "FENT-1234-5678-9012"
    response = await api_client.post(
        f"/entitlements/{entitlement_id}/terminate",
        headers={"Authorization": f"Bearer {gcp_jwt_token}"},
    )

    assert response.status_code == 404
    error_msg = response.json()["detail"]

    assert error_msg == f"Entitlement with ID `{entitlement_id}` wasn't found."


# ==================
# Redeem Entitlement
# ==================


async def test_redeem_entitlement_success(
    operations_client: AsyncClient,
    entitlement_gcp: Entitlement,
    organization_factory,
    db_session: AsyncSession,
    httpx_mock: HTTPXMock,
    test_settings: Settings,
):
    organization = await organization_factory(
        name="Test Organization",
        currency="USD",
        operations_external_id="ORG-123456",
        linked_organization_id="FORG-123456789012",
    )

    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.optscale_rest_api_base_url}/cloud_accounts/{entitlement_gcp.datasource_id}?details=true",
        match_headers={"Secret": test_settings.optscale_cluster_secret},
        json={
            "id": entitlement_gcp.datasource_id,
            "name": "GCP Dev Project",
            "type": "gcp_cnr",
            "organization_id": "FORG-123456789012",
        },
    )

    response = await operations_client.post(
        f"/entitlements/{entitlement_gcp.id}/redeem",
        json={
            "organization": {"id": organization.id},
            "datasource": {
                "id": entitlement_gcp.datasource_id,
                "name": "GCP Dev Project",
                "type": "gcp_cnr",
            },
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert data["id"] == str(entitlement_gcp.id)
    assert data["status"] == "active"
    assert data["linked_datasource_id"] == entitlement_gcp.datasource_id
    assert data["linked_datasource_name"] == "GCP Dev Project"
    assert data["linked_datasource_type"] == "gcp_cnr"
    assert data["events"]["redeemed"]["at"] is not None
    assert data["events"]["redeemed"]["by"]["id"] == organization.id

    await db_session.refresh(entitlement_gcp)
    assert entitlement_gcp.status == EntitlementStatus.ACTIVE
    assert entitlement_gcp.redeemed_at is not None
    assert entitlement_gcp.redeemed_by_id == organization.id
    assert entitlement_gcp.linked_datasource_id == entitlement_gcp.datasource_id
    assert entitlement_gcp.linked_datasource_name == "GCP Dev Project"
    assert entitlement_gcp.linked_datasource_type == DatasourceType.GCP_CNR


async def test_redeem_entitlement_with_set_redeem_at(
    operations_client: AsyncClient,
    entitlement_gcp_with_redeem_at: Entitlement,
    organization_factory,
    db_session: AsyncSession,
    httpx_mock: HTTPXMock,
    test_settings: Settings,
):
    organization = await organization_factory(
        name="Test Organization",
        currency="USD",
        operations_external_id="ORG-123456",
        linked_organization_id="FORG-123456789012",
    )

    httpx_mock.add_response(
        method="GET",
        url=(
            f"{test_settings.optscale_rest_api_base_url}/cloud_accounts/"
            f"{entitlement_gcp_with_redeem_at.datasource_id}?details=true"
        ),
        match_headers={"Secret": test_settings.optscale_cluster_secret},
        json={
            "id": entitlement_gcp_with_redeem_at.datasource_id,
            "name": "GCP Dev Project",
            "type": "gcp_cnr",
            "organization_id": "FORG-123456789012",
        },
    )

    response = await operations_client.post(
        f"/entitlements/{entitlement_gcp_with_redeem_at.id}/redeem",
        json={
            "organization": {"id": organization.id},
            "datasource": {
                "id": entitlement_gcp_with_redeem_at.datasource_id,
                "name": "GCP Dev",
                "type": "gcp_cnr",
            },
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert data["id"] == str(entitlement_gcp_with_redeem_at.id)
    assert data["status"] == "active"

    await db_session.refresh(entitlement_gcp_with_redeem_at)
    redeemed = data["events"]["redeemed"]["at"]
    assert datetime.fromisoformat(redeemed) == entitlement_gcp_with_redeem_at.redeem_at
    assert entitlement_gcp_with_redeem_at.status == EntitlementStatus.ACTIVE


async def test_redeem_entitlement_by_affiliate(
    affiliate_client: AsyncClient,
    entitlement_gcp: Entitlement,
):
    response = await affiliate_client.post(
        f"/entitlements/{entitlement_gcp.id}/redeem",
        json={
            "organization": {"id": "FORG-123456789012"},
            "datasource": {
                "id": entitlement_gcp.datasource_id,
                "name": "GCP Dev Project",
                "type": "gcp_cnr",
            },
        },
    )

    assert response.status_code == 403


async def test_redeem_non_new_entitlement(
    operations_client: AsyncClient,
    entitlement_gcp: Entitlement,
    db_session: AsyncSession,
):
    entitlement_gcp.status = EntitlementStatus.ACTIVE
    db_session.add(entitlement_gcp)
    await db_session.commit()
    await db_session.refresh(entitlement_gcp)

    response = await operations_client.post(
        f"/entitlements/{entitlement_gcp.id}/redeem",
        json={
            "organization": {"id": "FORG-123456789012"},
            "datasource": {
                "id": entitlement_gcp.datasource_id,
                "name": "GCP Dev Project",
                "type": "gcp_cnr",
            },
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Only new entitlements can be redeemed, current status is active."
    )


async def test_redeem_entitlement_organization_doesnt_exist(
    operations_client: AsyncClient,
    entitlement_gcp: Entitlement,
):
    response = await operations_client.post(
        f"/entitlements/{entitlement_gcp.id}/redeem",
        json={
            "organization": {"id": "FORG-1001-0110"},
            "datasource": {
                "id": entitlement_gcp.datasource_id,
                "name": "GCP Dev Project",
                "type": "gcp_cnr",
            },
        },
    )
    assert response.status_code == 400
    assert response.json()["detail"] == (
        f"Cannot redeem Entitlement {entitlement_gcp.id}: organization FORG-1001-0110 not found."
    )


async def test_redeem_entitlement_inactive_organization(
    operations_client: AsyncClient,
    entitlement_gcp: Entitlement,
    organization_factory,
    db_session: AsyncSession,
):
    organization = await organization_factory(
        name="Test Organization",
        currency="USD",
        operations_external_id="ORG-123456",
        status=OrganizationStatus.CANCELLED,
    )

    response = await operations_client.post(
        f"/entitlements/{entitlement_gcp.id}/redeem",
        json={
            "organization": {"id": organization.id},
            "datasource": {
                "id": entitlement_gcp.datasource_id,
                "name": "GCP Dev Project",
                "type": "gcp_cnr",
            },
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Only active organizations can redeem entitlements, current status is cancelled."
    )


async def test_redeem_entitlement_datasource_organization_mismatch(
    operations_client: AsyncClient,
    entitlement_gcp: Entitlement,
    organization_factory,
    test_settings: Settings,
    httpx_mock: HTTPXMock,
):
    organization = await organization_factory(
        name="Test Organization",
        currency="USD",
        operations_external_id="ORG-123456",
        linked_organization_id="FORG-123456789012",
    )

    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.optscale_rest_api_base_url}/cloud_accounts/{entitlement_gcp.datasource_id}?details=true",
        match_headers={"Secret": test_settings.optscale_cluster_secret},
        json={
            "id": entitlement_gcp.datasource_id,
            "name": "GCP Dev Project",
            "type": "gcp_cnr",
            "organization_id": "FORG-different-org-id",  # Different from the provided organization
        },
    )

    response = await operations_client.post(
        f"/entitlements/{entitlement_gcp.id}/redeem",
        json={
            "organization": {"id": organization.id},
            "datasource": {
                "id": entitlement_gcp.datasource_id,
                "name": "GCP Dev Project",
                "type": "gcp_cnr",
            },
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        f"Datasource {entitlement_gcp.datasource_id} does not belong to organization "
        f"{organization.id} on Optscale."
    )


async def test_redeem_entitlement_datasource_doesnt_exist(
    operations_client: AsyncClient,
    entitlement_gcp: Entitlement,
    organization_factory,
    test_settings: Settings,
    httpx_mock: HTTPXMock,
):
    organization = await organization_factory(
        name="Test Organization",
        currency="USD",
        operations_external_id="ORG-123456",
        linked_organization_id="FORG-123456789012",
    )

    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.optscale_rest_api_base_url}/cloud_accounts/{entitlement_gcp.datasource_id}?details=true",
        status_code=404,
    )

    response = await operations_client.post(
        f"/entitlements/{entitlement_gcp.id}/redeem",
        json={
            "organization": {"id": organization.id},
            "datasource": {
                "id": entitlement_gcp.datasource_id,
                "name": "GCP Dev Project",
                "type": "gcp_cnr",
            },
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        f"Cannot redeem Entitlement {entitlement_gcp.id}: "
        f"datasource {entitlement_gcp.datasource_id} not found."
    )


async def test_redeem_entitlement_datasource_unexpected_http_error(
    operations_client: AsyncClient,
    entitlement_gcp: Entitlement,
    organization_factory,
    test_settings: Settings,
    httpx_mock: HTTPXMock,
):
    organization = await organization_factory(
        name="Test Organization",
        currency="USD",
        operations_external_id="ORG-123456",
        linked_organization_id="FORG-123456789012",
    )

    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.optscale_rest_api_base_url}/cloud_accounts/{entitlement_gcp.datasource_id}?details=true",
        status_code=500,
    )

    response = await operations_client.post(
        f"/entitlements/{entitlement_gcp.id}/redeem",
        json={
            "organization": {"id": organization.id},
            "datasource": {
                "id": entitlement_gcp.datasource_id,
                "name": "GCP Dev Project",
                "type": "gcp_cnr",
            },
        },
    )

    assert response.status_code == 502


async def test_redeem_non_existent_entitlement(operations_client: AsyncClient):
    entitlement_id = "FENT-1234-5678-9012"

    response = await operations_client.post(
        f"/entitlements/{entitlement_id}/redeem",
        json={
            "organization": {"id": "FORG-123456789012"},
            "datasource": {
                "id": "datasource-id",
                "name": "GCP Dev Project",
                "type": "gcp_cnr",
            },
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == f"Entitlement with ID `{entitlement_id}` wasn't found."


####
# delete
####


async def test_delete_entitlement_success(
    operations_client: AsyncClient,
    entitlement_factory: ModelFactory[Entitlement],
    db_session: AsyncSession,
):
    entitlement = await entitlement_factory(status=EntitlementStatus.NEW)

    response = await operations_client.delete(f"/entitlements/{entitlement.id}")

    assert response.status_code == 204
    await db_session.refresh(entitlement)
    assert entitlement.status == EntitlementStatus.DELETED


@pytest.mark.parametrize(
    "entitlement_status",
    [EntitlementStatus.ACTIVE, EntitlementStatus.TERMINATED, EntitlementStatus.DELETED],
)
async def test_delete_entitlement_invalid_status(
    operations_client: AsyncClient,
    entitlement_factory: ModelFactory[Entitlement],
    db_session: AsyncSession,
    entitlement_status: EntitlementStatus,
):
    entitlement = await entitlement_factory(status=entitlement_status)

    response = await operations_client.delete(f"/entitlements/{entitlement.id}")

    assert response.status_code == 400
    assert response.json()["detail"] == "Only Entitlements in status `new` can be deleted."
    await db_session.refresh(entitlement)
    assert entitlement.status == entitlement_status


async def test_delete_deleted_entitlement_by_affiliate(
    affiliate_client: AsyncClient,
    gcp_account: Account,
    entitlement_factory: ModelFactory[Entitlement],
):
    entitlement = await entitlement_factory(
        status=EntitlementStatus.DELETED,
        owner=gcp_account,
    )

    response = await affiliate_client.delete(f"/entitlements/{entitlement.id}")
    assert response.status_code == 404
