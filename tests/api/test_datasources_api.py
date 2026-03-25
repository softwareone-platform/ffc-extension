import uuid
from typing import Any

import pytest
from httpx import AsyncClient
from pytest_httpx import HTTPXMock

from app.conf import Settings
from app.db.models import Organization
from app.enums import DatasourceType
from tests.types import ModelFactory

# ===========================
# Optscale API Mock responses
# ===========================


def optscale_azure_cnr_datasource_response_data(
    organization_id: str,
) -> dict[str, Any]:
    return {
        "deleted_at": 0,
        "id": "6d55d940-ba4a-4e80-8493-57b3fdf5c331",
        "created_at": 1729683941,
        "name": "CPA (Development and Test)",
        "type": "azure_cnr",
        "config": {
            "client_id": "cd945f4b-0554-4a16-9a09-96a2f30bc0ef",
            "tenant": "1dc9b339-fadb-432e-86df-423c38a0fcb8",
            "skipped_subscriptions": {
                "CPA (Development and Test)": "Cloud account for this account already exist"
            },
            "subscription_id": "91819a1c-c7d3-4b89-bc9f-39f85bff4666",
            "expense_import_scheme": "usage",
        },
        "organization_id": str(organization_id),
        "auto_import": True,
        "import_period": 1,
        "last_import_at": 1733151640,
        "last_import_modified_at": 0,
        "account_id": "91819a1c-c7d3-4b89-bc9f-39f85bff4666",
        "process_recommendations": True,
        "cleaned_at": 0,
        "parent_id": "48108421-7334-4a2c-ac7b-0160476dc790",
        "details": {
            "cost": 0,
            "forecast": 1099.0,
            "resources": 0,
            "last_month_cost": 2909.1068521455545,
            "discovery_infos": [],
        },
    }


def optscale_azure_tenant_datasource_response_data(
    organization_id: str,
) -> dict[str, Any]:
    return {
        "deleted_at": 0,
        "id": "48108421-7334-4a2c-ac7b-0160476dc790",
        "created_at": 1729683895,
        "name": "Test",
        "type": "azure_tenant",
        "config": {
            "client_id": "cd945f4b-0554-4a16-9a09-96a2f30bc0ef",
            "tenant": "1dc9b339-fadb-432e-86df-423c38a0fcb8",
            "skipped_subscriptions": {
                "CPA (Development and Test)": "Cloud account for this account already exist"
            },
        },
        "organization_id": str(organization_id),
        "auto_import": False,
        "import_period": 1,
        "last_import_at": 0,
        "last_import_modified_at": 0,
        "account_id": "1dc9b339-fadb-432e-86df-423c38a0fcb8",
        "process_recommendations": True,
        "last_import_attempt_at": 0,
        "last_import_attempt_error": None,
        "last_getting_metrics_at": 0,
        "last_getting_metric_attempt_at": 0,
        "last_getting_metric_attempt_error": None,
        "cleaned_at": 0,
        "parent_id": None,
        "details": {
            "cost": 0,
            "forecast": 0.0,
            "resources": 0,
            "last_month_cost": 0,
            "discovery_infos": [],
        },
    }


def optscale_aws_cnr_datasource_get_by_id_response_data():
    return {
        "account_id": "1dc9b339-fadb-432e-86df-423c38a0fcb8",
        "id": "5cded1eb-4d7e-4df9-b76f-fc33b5df9eb3",
        "last_getting_metric_attempt_at": 0,
        "last_getting_metric_attempt_error": None,
        "last_getting_metrics_at": 0,
        "last_import_at": 0,
        "last_import_attempt_at": 0,
        "last_import_attempt_error": None,
        "name": "swotest02",
        "parent_id": None,
        "type": "aws_cnr",
        "details": {
            "cost": 99.88,
            "discovery_infos": [],
            "forecast": 1234.56,
            "last_month_cost": 0,
            "resources": 5,
        },
        "config": {
            "access_key_id": "[REDACTED]",
            "linked": False,
            "use_edp_discount": False,
            "cur_version": 2,
            "bucket_name": "optscale-billing-bucket",
            "bucket_prefix": "reports",
            "config_scheme": "create_report",
            "region_name": False,
            "report_name": "optscale-billing-export",
        },
    }


# =============================================
# Get all datasources within an organization
# =============================================


async def test_get_datasources_for_organization_success(
    test_settings: Settings,
    organization_factory: ModelFactory[Organization],
    httpx_mock: HTTPXMock,
    operations_client: AsyncClient,
):
    org = await organization_factory(
        linked_organization_id=str(uuid.uuid4()),
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.optscale_rest_api_base_url}/organizations/{org.linked_organization_id}/cloud_accounts?details=true",
        match_headers={"Secret": test_settings.optscale_cluster_secret},
        json={
            "cloud_accounts": [
                optscale_azure_cnr_datasource_response_data(org.linked_organization_id),  # type: ignore
                optscale_azure_tenant_datasource_response_data(org.linked_organization_id),  # type: ignore
            ]
        },
    )

    response = await operations_client.get(
        f"/organizations/{org.id}/datasources",
    )

    assert response.status_code == 200
    data = response.json()

    assert len(data) == 2

    azure_cnr = next(item for item in data if item["type"] == "azure_cnr")
    azure_tenant = next(item for item in data if item["type"] == "azure_tenant")

    assert azure_cnr["name"] == "CPA (Development and Test)"
    assert azure_cnr["type"] == DatasourceType.AZURE_CNR.value
    assert azure_cnr["parent_id"] == "48108421-7334-4a2c-ac7b-0160476dc790"
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
    operations_client: AsyncClient,
):
    org_id = "FORG-1234-5678-9012"
    response = await operations_client.get(
        f"/organizations/{org_id}/datasources",
    )

    assert response.status_code == 404
    assert response.json() == {"detail": f"Organization with ID `{org_id}` wasn't found."}


async def test_get_datasources_for_organization_with_no_datasources(
    test_settings: Settings,
    organization_factory: ModelFactory[Organization],
    operations_client: AsyncClient,
    httpx_mock: HTTPXMock,
):
    org = await organization_factory(
        linked_organization_id=str(uuid.uuid4()),
    )

    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.optscale_rest_api_base_url}/organizations/{org.linked_organization_id}/cloud_accounts?details=true",
        match_headers={"Secret": test_settings.optscale_cluster_secret},
        json={"cloud_accounts": []},
    )

    response = await operations_client.get(
        f"/organizations/{org.id}/datasources",
    )

    assert response.status_code == 200
    assert response.json() == []


async def test_get_datasources_for_organization_with_no_organization_id(
    organization_factory: ModelFactory[Organization],
    operations_client: AsyncClient,
):
    org = await organization_factory(
        linked_organization_id=None,
    )

    response = await operations_client.get(
        f"/organizations/{org.id}/datasources",
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": f"Organization {org.name} has no associated FinOps for Cloud organization."
    }


async def test_get_datasources_for_organization_with_optscale_error(
    test_settings: Settings,
    organization_factory: ModelFactory[Organization],
    operations_client: AsyncClient,
    httpx_mock: HTTPXMock,
):
    org = await organization_factory(
        linked_organization_id=str(uuid.uuid4()),
    )

    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.optscale_rest_api_base_url}/organizations/{org.linked_organization_id}/cloud_accounts?details=true",
        match_headers={"Secret": test_settings.optscale_cluster_secret},
        status_code=500,
    )

    response = await operations_client.get(
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
    operations_client: AsyncClient,
):
    org = await organization_factory(
        linked_organization_id=str(uuid.uuid4()),
    )

    datasource_data = optscale_aws_cnr_datasource_get_by_id_response_data()  # type: ignore

    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.optscale_rest_api_base_url}/cloud_accounts/{datasource_data['id']}?details=true",
        match_headers={"Secret": test_settings.optscale_cluster_secret},
        json=datasource_data,
    )

    response = await operations_client.get(
        f"/organizations/{org.id}/datasources/{datasource_data['id']}",
    )

    assert response.status_code == 200
    assert response.json() == {
        "id": datasource_data["id"],
        "name": datasource_data["name"],
        "type": DatasourceType.AWS_CNR.value,
        "resources_charged_this_month": 5,
        "expenses_so_far_this_month": 99.88,
        "expenses_forecast_this_month": 1234.56,
        "datasource_id": "1dc9b339-fadb-432e-86df-423c38a0fcb8",
    }


async def test_get_datasource_by_id_for_missing_organization(
    operations_client: AsyncClient,
):
    org_id = "FORG-1234-5678-9012"
    response = await operations_client.get(
        f"/organizations/{org_id}/datasources/{uuid.uuid4()}",
    )

    assert response.status_code == 404
    assert response.json() == {"detail": f"Organization with ID `{org_id}` wasn't found."}


async def test_get_datasource_by_id_for_missing_datasource(
    test_settings: Settings,
    organization_factory: ModelFactory[Organization],
    operations_client: AsyncClient,
    httpx_mock: HTTPXMock,
):
    org = await organization_factory(
        linked_organization_id=str(uuid.uuid4()),
    )

    datasource_id = str(uuid.uuid4())
    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.optscale_rest_api_base_url}/cloud_accounts/{datasource_id}?details=true",
        match_headers={"Secret": test_settings.optscale_cluster_secret},
        status_code=404,
    )

    response = await operations_client.get(
        f"/organizations/{org.id}/datasources/{datasource_id}",
    )

    assert response.status_code == 502
    assert f"Error fetching cloud account with ID {datasource_id}" in response.json()["detail"]


async def test_get_datasource_by_id_for_organization_with_no_organization_id(
    organization_factory: ModelFactory[Organization],
    operations_client: AsyncClient,
):
    org = await organization_factory(
        linked_organization_id=None,
    )

    response = await operations_client.get(
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
    operations_client: AsyncClient,
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

    response = await operations_client.post(
        f"/organizations/{org.id}/datasources/{datasource_id}/force-reimport",
    )

    assert response.status_code == 204


async def test_force_reimport_datasource_no_linked_organization_id(
    organization_factory: ModelFactory[Organization],
    test_settings: Settings,
    operations_client: AsyncClient,
):
    org = await organization_factory(
        linked_organization_id=None,
    )

    response = await operations_client.post(
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
    operations_client: AsyncClient,
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

    response = await operations_client.post(
        f"/organizations/{org.id}/datasources/{datasource_id}/force-reimport",
    )

    assert response.status_code == 502
    assert "Error scheduling import" in response.json()["detail"]
