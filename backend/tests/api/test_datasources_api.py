import uuid

import pytest
from httpx import AsyncClient
from pytest_httpx import HTTPXMock

from app.conf import Settings
from app.db.models import Organization
from app.enums import DatasourceType
from tests.types import ModelFactory

# ==========================
# FFC API Mock responses
# ==========================


def ffc_api_aws_cnr_datasource_detail_response_data():
    return {
        "id": "5cded1eb-4d7e-4df9-b76f-fc33b5df9eb3",
        "name": "swotest02",
        "type": "aws_cnr",
        "account_id": "203589795269",
        "parent": None,
        "tags": [],
        "last_import_at": 1756684800,  # 2025-09-01T00:00:00Z
        "last_import_modified_at": 0,
        "last_import_attempt_at": 1756684800,
        "last_import_attempt_error": None,
        "cost": 99.88,
        "forecast": 1234.56,
        "resources": 5,
        "details": {
            "connected_at": "2025-08-01T00:00:00Z",
            "account_id": "203589795269",
            "account_type": "management_standalone",
            "authentication_type": "access_key",
            "access_key_id": "AKIAIOSFODNN7EXAMPLE",
            "export_type": "standard_data_export",
            "use_edp_discount": False,
            "export_name": "optscale-billing-export",
            "bucket_name": "optscale-billing-bucket",
            "bucket_prefix": "reports",
        },
        "billing": {
            "last_report_processed_at": "2025-09-01T00:00:00Z",
            "last_attempt_at": "2025-09-01T00:00:00Z",
            "last_report_updated_at": None,
            "status": "completed",
            "error": None,
        },
        "metrics": {
            "last_retrieval_at": None,
            "last_attempt_at": "2025-09-01T00:00:00Z",
            "status": "failed",
            "error": "Access denied",
        },
        "discovery": [
            {
                "resource_type": "instance",
                "enabled": True,
                "last_discovery_at": "2025-09-01T00:00:00Z",
                "last_error_at": None,
                "status": "completed",
                "error": None,
            },
        ],
    }


# =============================================
# Get all datasources within an organization
# =============================================


async def test_get_datasources_for_organization_success(
    test_settings: Settings,
    organization_factory: ModelFactory[Organization],
    httpx_mock: HTTPXMock,
    admin_client: AsyncClient,
):
    org = await organization_factory(
        linked_organization_id=str(uuid.uuid4()),
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.optscale_ffc_api_base_url}/admin/organizations/{org.linked_organization_id}/datasources?limit=50&offset=0",
        match_headers={"Secret": test_settings.optscale_cluster_secret},
        json={
            "items": [
                {
                    "id": "6d55d940-ba4a-4e80-8493-57b3fdf5c331",
                    "name": "CPA (Development and Test)",
                    "type": "azure_cnr",
                    "account_id": "91819a1c-c7d3-4b89-bc9f-39f85bff4666",
                    "parent": {
                        "id": "48108421-7334-4a2c-ac7b-0160476dc790",
                        "name": "CPA (Development)",
                        "type": "azure_cnr",
                    },
                    "cost": 0,
                    "forecast": 1099.0,
                    "resources": 0,
                },
                {
                    "id": "48108421-7334-4a2c-ac7b-0160476dc790",
                    "name": "Test",
                    "type": "azure_tenant",
                    "account_id": "1dc9b339-fadb-432e-86df-423c38a0fcb8",
                    "cost": 0,
                    "forecast": 0.0,
                    "resources": 0,
                },
            ],
            "total": 2,
            "limit": 50,
            "offset": 0,
        },
    )

    response = await admin_client.get(
        f"/organizations/{org.id}/datasources",
    )

    assert response.status_code == 200
    data = response.json()

    assert data["total"] == 2

    azure_cnr = next(item for item in data["items"] if item["type"] == "azure_cnr")
    azure_tenant = next(item for item in data["items"] if item["type"] == "azure_tenant")

    assert azure_cnr["name"] == "CPA (Development and Test)"
    assert azure_cnr["type"] == DatasourceType.AZURE_CNR.value
    assert azure_cnr["parent"]["id"] == "48108421-7334-4a2c-ac7b-0160476dc790"
    assert azure_cnr["resources_charged_this_month"] == 0
    assert azure_cnr["expenses_so_far_this_month"] == pytest.approx(0.0)
    assert azure_cnr["expenses_forecast_this_month"] == pytest.approx(1099.0)
    assert "datasource_id" in azure_cnr
    assert azure_tenant["name"] == "Test"
    assert azure_tenant["type"] == DatasourceType.AZURE_TENANT.value
    assert "parent_id" not in azure_tenant
    assert "datasource_id" in azure_tenant
    assert azure_tenant["resources_charged_this_month"] == 0
    assert azure_tenant["resources_charged_this_month"] == pytest.approx(0.0)
    assert azure_tenant["expenses_forecast_this_month"] == pytest.approx(0.0)


async def test_get_datasources_for_missing_organization(
    admin_client: AsyncClient,
):
    org_id = "FORG-1234-5678-9012"
    response = await admin_client.get(
        f"/organizations/{org_id}/datasources",
    )

    assert response.status_code == 404
    assert response.json() == {"detail": f"Organization with ID `{org_id}` wasn't found."}


async def test_get_datasources_for_organization_with_no_datasources(
    test_settings: Settings,
    organization_factory: ModelFactory[Organization],
    admin_client: AsyncClient,
    httpx_mock: HTTPXMock,
):
    org = await organization_factory(
        linked_organization_id=str(uuid.uuid4()),
    )

    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.optscale_ffc_api_base_url}/admin/organizations/{org.linked_organization_id}/datasources?limit=50&offset=0",
        match_headers={"Secret": test_settings.optscale_cluster_secret},
        json={"items": [], "total": 0, "limit": 50, "offset": 0},
    )

    response = await admin_client.get(
        f"/organizations/{org.id}/datasources",
    )

    assert response.status_code == 200
    assert response.json()["items"] == []


async def test_get_datasources_for_organization_with_no_organization_id(
    organization_factory: ModelFactory[Organization],
    admin_client: AsyncClient,
):
    org = await organization_factory(
        linked_organization_id=None,
    )

    response = await admin_client.get(
        f"/organizations/{org.id}/datasources",
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": f"Organization {org.name} has no associated FinOps for Cloud organization."
    }


async def test_get_datasources_for_organization_with_optscale_error(
    test_settings: Settings,
    organization_factory: ModelFactory[Organization],
    admin_client: AsyncClient,
    httpx_mock: HTTPXMock,
):
    org = await organization_factory(
        linked_organization_id=str(uuid.uuid4()),
    )

    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.optscale_ffc_api_base_url}/admin/organizations/{org.linked_organization_id}/datasources?limit=50&offset=0",
        match_headers={"Secret": test_settings.optscale_cluster_secret},
        status_code=500,
    )

    response = await admin_client.get(
        f"/organizations/{org.id}/datasources",
    )

    assert response.status_code == 502
    assert f"Error fetching datasources for organization {org.name}" in response.json()["detail"]


# ================================================
# Get a cloud account by ID within an organization
# ================================================


async def test_get_datasource_by_id_success(
    test_settings: Settings,
    organization_factory: ModelFactory[Organization],
    httpx_mock: HTTPXMock,
    admin_client: AsyncClient,
):
    org = await organization_factory(
        linked_organization_id=str(uuid.uuid4()),
    )

    datasource_data = ffc_api_aws_cnr_datasource_detail_response_data()

    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.optscale_ffc_api_base_url}/admin/organizations/{org.linked_organization_id}/datasources/{datasource_data['id']}",
        match_headers={"Secret": test_settings.optscale_cluster_secret},
        json=datasource_data,
    )

    response = await admin_client.get(
        f"/organizations/{org.id}/datasources/{datasource_data['id']}",
    )

    assert response.status_code == 200
    # Null fields are omitted from the response.
    assert response.json() == {
        "id": datasource_data["id"],
        "name": datasource_data["name"],
        "type": DatasourceType.AWS_CNR.value,
        "resources_charged_this_month": 5,
        "expenses_so_far_this_month": 99.88,
        "expenses_forecast_this_month": 1234.56,
        "datasource_id": "203589795269",
        "last_import_at": "2025-09-01T00:00:00Z",
        "last_import_modified_at": "1970-01-01T00:00:00Z",
        "last_import_attempt_at": "2025-09-01T00:00:00Z",
        "details": {
            "connected_at": "2025-08-01T00:00:00Z",
            "account_id": "203589795269",
            "account_type": "management_standalone",
            "authentication_type": "access_key",
            "access_key_id": "AKIAIOSFODNN7EXAMPLE",
            "export_type": "standard_data_export",
            "use_edp_discount": False,
            "export_name": "optscale-billing-export",
            "bucket_name": "optscale-billing-bucket",
            "bucket_prefix": "reports",
        },
        "billing": {
            "last_report_processed_at": "2025-09-01T00:00:00Z",
            "last_attempt_at": "2025-09-01T00:00:00Z",
            "status": "completed",
        },
        "metrics": {
            "last_attempt_at": "2025-09-01T00:00:00Z",
            "status": "failed",
            "error": "Access denied",
        },
        "discovery": [
            {
                "resource_type": "instance",
                "enabled": True,
                "last_discovery_at": "2025-09-01T00:00:00Z",
                "status": "completed",
            },
        ],
    }


async def test_get_datasource_by_id_picks_details_schema_from_type(
    test_settings: Settings,
    organization_factory: ModelFactory[Organization],
    httpx_mock: HTTPXMock,
    admin_client: AsyncClient,
):
    org = await organization_factory(
        linked_organization_id=str(uuid.uuid4()),
    )

    # An Azure tenant details payload is also a valid Azure subscription one:
    # the datasource type must drive which schema is used.
    datasource_data = {
        **ffc_api_aws_cnr_datasource_detail_response_data(),
        "type": "azure_tenant",
        "details": {
            "connected_at": "2025-08-01T00:00:00Z",
            "tenant_id": "8b1d7e4a-3c2f-4a9b-8e6d-1f0a5c7b9d2e",
            "client_id": "c2a9f0b3-7e1d-4b6a-9c8f-3d5e2a1b0c4f",
        },
    }

    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.optscale_ffc_api_base_url}/admin/organizations/{org.linked_organization_id}/datasources/{datasource_data['id']}",
        json=datasource_data,
    )

    response = await admin_client.get(
        f"/organizations/{org.id}/datasources/{datasource_data['id']}",
    )

    assert response.status_code == 200
    assert response.json()["details"] == datasource_data["details"]


async def test_get_datasource_by_id_for_unsupported_type_omits_details(
    test_settings: Settings,
    organization_factory: ModelFactory[Organization],
    httpx_mock: HTTPXMock,
    admin_client: AsyncClient,
):
    org = await organization_factory(
        linked_organization_id=str(uuid.uuid4()),
    )

    datasource_data = {
        **ffc_api_aws_cnr_datasource_detail_response_data(),
        "type": "kubernetes_cnr",
        "details": None,
    }

    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.optscale_ffc_api_base_url}/admin/organizations/{org.linked_organization_id}/datasources/{datasource_data['id']}",
        json=datasource_data,
    )

    response = await admin_client.get(
        f"/organizations/{org.id}/datasources/{datasource_data['id']}",
    )

    assert response.status_code == 200
    data = response.json()
    assert data["type"] == DatasourceType.UNKNOWN.value
    assert "details" not in data


async def test_get_datasource_by_id_for_missing_organization(
    admin_client: AsyncClient,
):
    org_id = "FORG-1234-5678-9012"
    response = await admin_client.get(
        f"/organizations/{org_id}/datasources/{uuid.uuid4()}",
    )

    assert response.status_code == 404
    assert response.json() == {"detail": f"Organization with ID `{org_id}` wasn't found."}


async def test_get_datasource_by_id_for_missing_datasource(
    test_settings: Settings,
    organization_factory: ModelFactory[Organization],
    admin_client: AsyncClient,
    httpx_mock: HTTPXMock,
):
    org = await organization_factory(
        linked_organization_id=str(uuid.uuid4()),
    )

    datasource_id = str(uuid.uuid4())
    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.optscale_ffc_api_base_url}/admin/organizations/{org.linked_organization_id}/datasources/{datasource_id}",
        match_headers={"Secret": test_settings.optscale_cluster_secret},
        status_code=404,
    )

    response = await admin_client.get(
        f"/organizations/{org.id}/datasources/{datasource_id}",
    )

    assert response.status_code == 404
    assert response.json() == {"detail": f"Datasource with ID `{datasource_id}` wasn't found."}


async def test_get_datasource_by_id_with_ffc_api_error(
    test_settings: Settings,
    organization_factory: ModelFactory[Organization],
    admin_client: AsyncClient,
    httpx_mock: HTTPXMock,
):
    org = await organization_factory(
        linked_organization_id=str(uuid.uuid4()),
    )

    datasource_id = str(uuid.uuid4())
    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.optscale_ffc_api_base_url}/admin/organizations/{org.linked_organization_id}/datasources/{datasource_id}",
        status_code=500,
    )

    response = await admin_client.get(
        f"/organizations/{org.id}/datasources/{datasource_id}",
    )

    assert response.status_code == 502
    assert f"Error fetching datasource with ID {datasource_id}" in response.json()["detail"]


async def test_get_datasource_by_id_for_organization_with_no_organization_id(
    organization_factory: ModelFactory[Organization],
    admin_client: AsyncClient,
):
    org = await organization_factory(
        linked_organization_id=None,
    )

    response = await admin_client.get(
        f"/organizations/{org.id}/datasources/{uuid.uuid4()}",
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": f"Organization {org.name} has no associated FinOps for Cloud organization."
    }


async def test_force_reimport_datasource(
    organization_factory: ModelFactory[Organization],
    test_settings: Settings,
    httpx_mock: HTTPXMock,
    admin_client: AsyncClient,
):
    org = await organization_factory(
        linked_organization_id=str(uuid.uuid4()),
    )
    datasource_id = str(uuid.uuid4())
    httpx_mock.add_response(
        method="PATCH",
        url=f"{test_settings.optscale_rest_api_base_url}/cloud_accounts/{datasource_id}",
        match_headers={"Secret": test_settings.optscale_cluster_secret},
        status_code=200,
    )
    httpx_mock.add_response(
        method="POST",
        url=f"{test_settings.optscale_rest_api_base_url}/schedule_imports",
        match_headers={"Secret": test_settings.optscale_cluster_secret},
        status_code=200,
    )

    response = await admin_client.post(
        f"/organizations/{org.id}/datasources/{datasource_id}/force-reimport",
    )

    assert response.status_code == 204


async def test_force_reimport_datasource_with_last_import_at(
    organization_factory: ModelFactory[Organization],
    test_settings: Settings,
    httpx_mock: HTTPXMock,
    admin_client: AsyncClient,
):
    org = await organization_factory(
        linked_organization_id=str(uuid.uuid4()),
    )
    datasource_id = str(uuid.uuid4())
    # 2025-09-01T00:00:00+00:00 expressed as seconds since the epoch
    expected_timestamp = 1756684800
    httpx_mock.add_response(
        method="PATCH",
        url=f"{test_settings.optscale_rest_api_base_url}/cloud_accounts/{datasource_id}",
        match_headers={"Secret": test_settings.optscale_cluster_secret},
        match_json={
            "last_import_at": expected_timestamp,
            "last_import_modified_at": expected_timestamp,
        },
        status_code=200,
    )
    httpx_mock.add_response(
        method="POST",
        url=f"{test_settings.optscale_rest_api_base_url}/schedule_imports",
        match_headers={"Secret": test_settings.optscale_cluster_secret},
        status_code=200,
    )

    response = await admin_client.post(
        f"/organizations/{org.id}/datasources/{datasource_id}/force-reimport",
        json={"last_import_at": "2025-09-01"},
    )

    assert response.status_code == 204


async def test_force_reimport_datasource_no_linked_organization_id(
    organization_factory: ModelFactory[Organization],
    test_settings: Settings,
    admin_client: AsyncClient,
):
    org = await organization_factory(
        linked_organization_id=None,
    )

    response = await admin_client.post(
        f"/organizations/{org.id}/datasources/{str(uuid.uuid4())}/force-reimport",
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": f"Organization {org.name} has no associated FinOps for Cloud organization."
    }


async def test_force_reimport_datasource_optscale_error(
    organization_factory: ModelFactory[Organization],
    test_settings: Settings,
    httpx_mock: HTTPXMock,
    admin_client: AsyncClient,
):
    org = await organization_factory(
        linked_organization_id=str(uuid.uuid4()),
    )
    datasource_id = str(uuid.uuid4())
    httpx_mock.add_response(
        method="PATCH",
        url=f"{test_settings.optscale_rest_api_base_url}/cloud_accounts/{datasource_id}",
        match_headers={"Secret": test_settings.optscale_cluster_secret},
        status_code=200,
    )
    httpx_mock.add_response(
        method="POST",
        url=f"{test_settings.optscale_rest_api_base_url}/schedule_imports",
        match_headers={"Secret": test_settings.optscale_cluster_secret},
        status_code=400,
    )

    response = await admin_client.post(
        f"/organizations/{org.id}/datasources/{datasource_id}/force-reimport",
    )

    assert response.status_code == 502
    assert "Error scheduling import" in response.json()["detail"]
