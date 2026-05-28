import uuid

from httpx import AsyncClient
from pytest_httpx import HTTPXMock

from app.conf import Settings
from app.db.models import Organization
from tests.types import ModelFactory

# =============================================
# Get employees within an organization
# =============================================


async def test_get_employees_for_organization_success(
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
        url=f"{test_settings.optscale_ffc_api_base_url}/organizations/{org.linked_organization_id}/users?limit=50&offset=0",
        match_headers={"Secret": test_settings.optscale_cluster_secret},
        json={
            "items": [
                {
                    "id": "85a86112-a94f-4470-9343-f7d19101b15d",
                    "created_at": 1730390070,
                    "name": "Tim",
                    "auth_user": {
                        "id": "989d185b-8c95-4104-b152-36148743e52d",
                        "email": "tim.cook@apple.com",
                        "last_login": "2024-10-31T15:41:02Z",
                        "assignments": [],
                    },
                    "tags": [],
                    "roles": 0,
                },
                {
                    "id": "0ae68497-a912-4fc1-a559-6f52a99bf12b",
                    "created_at": 1736339978,
                    "name": "Test User",
                    "auth_user": {
                        "id": "c391517d-5c71-4195-82cf-47e7e44c06b1",
                        "email": "FinOpsTest1@outlook.com",
                        "last_login": "2025-01-20T15:49:39Z",
                        "assignments": [
                            {
                                "resource_id": "9044af7f-2f62-40cd-976f-1cbbbf1a0411",
                                "role_name": "Manager",
                                "resource_name": "Apple Inc",
                                "resource_type": "organization",
                                "resource_purpose": "BUSINESS_UNIT",
                                "id": "265b6597-d7f6-4de7-8afd-c3ab3c14bf66",
                                "purpose": "optscale_manager",
                            },
                        ],
                    },
                    "tags": [],
                    "roles": 1,
                },
            ],
            "total": 2,
            "limit": 50,
            "offset": 0,
        },
    )

    response = await admin_client.get(
        f"/organizations/{org.id}/employees",
    )

    assert response.status_code == 200
    data = response.json()

    assert data["total"] == 2
    assert data["items"] == [
        {
            "created_at": "2024-10-31T15:54:30Z",
            "display_name": "Tim",
            "email": "tim.cook@apple.com",
            "id": "85a86112-a94f-4470-9343-f7d19101b15d",
            "last_login": "2024-10-31T15:41:02Z",
            "roles_count": 1,
            "is_admin": False,
        },
        {
            "created_at": "2025-01-08T12:39:38Z",
            "display_name": "Test User",
            "email": "FinOpsTest1@outlook.com",
            "id": "0ae68497-a912-4fc1-a559-6f52a99bf12b",
            "last_login": "2025-01-20T15:49:39Z",
            "roles_count": 2,
            "is_admin": True,
        },
    ]


async def test_get_employees_for_missing_organization(
    admin_client: AsyncClient,
):
    org_id = "FORG-1234-5678-9012"
    response = await admin_client.get(
        f"/organizations/{org_id}/employees",
    )

    assert response.status_code == 404
    assert response.json() == {"detail": f"Organization with ID `{org_id}` wasn't found."}


async def test_get_employees_for_organization_with_no_employees(
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
        url=f"{test_settings.optscale_ffc_api_base_url}/organizations/{org.linked_organization_id}/users?limit=50&offset=0",
        match_headers={"Secret": test_settings.optscale_cluster_secret},
        json={"items": [], "total": 0, "limit": 50, "offset": 0},
    )

    response = await admin_client.get(
        f"/organizations/{org.id}/employees",
    )

    assert response.status_code == 200
    assert response.json()["items"] == []


async def test_get_employees_for_organization_with_no_organization_id(
    organization_factory: ModelFactory[Organization],
    admin_client: AsyncClient,
    httpx_mock: HTTPXMock,
):
    org = await organization_factory(
        linked_organization_id=None,
    )

    response = await admin_client.get(
        f"/organizations/{org.id}/employees",
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": f"Organization {org.name} has no associated FinOps for Cloud organization."
    }


async def test_get_employees_for_organization_with_optscale_error(
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
        url=f"{test_settings.optscale_ffc_api_base_url}/organizations/{org.linked_organization_id}/users?limit=50&offset=0",
        match_headers={"Secret": test_settings.optscale_cluster_secret},
        status_code=500,
    )

    response = await admin_client.get(
        f"/organizations/{org.id}/employees",
    )

    assert response.status_code == 502
    assert f"Error fetching employees for organization {org.name}" in response.json()["detail"]


# ===============
# Make employee admin
# ===============


async def test_make_employee_admin(
    test_settings: Settings,
    organization_factory: ModelFactory[Organization],
    admin_client: AsyncClient,
    httpx_mock: HTTPXMock,
):
    user_id = str(uuid.uuid4())
    org = await organization_factory(
        linked_organization_id=str(uuid.uuid4()),
    )
    auth_user_id = str(uuid.uuid4())

    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.optscale_rest_api_base_url}/employees/{user_id}?roles=true",
        match_headers={"Secret": test_settings.optscale_cluster_secret},
        status_code=200,
        json={
            "deleted_at": 0,
            "id": "2c2e9705-8023-437c-b09d-8cbd49f0a682",
            "created_at": 1729156673,
            "name": "Ciccio",
            "organization_id": org.linked_organization_id,
            "auth_user_id": auth_user_id,
            "default_ssh_key_id": None,
        },
    )

    httpx_mock.add_response(
        method="POST",
        url=f"{test_settings.optscale_auth_api_base_url}/users/{auth_user_id}/assignment_register",
        match_headers={"Secret": test_settings.optscale_cluster_secret},
        status_code=200,
        json={
            "created_at": 1736352461,
            "deleted_at": 0,
            "id": "7884c0c0-be5c-4cc7-8413-dd8033b1e4a2",
            "type_id": 2,
            "role_id": 3,
            "user_id": auth_user_id,
            "resource_id": org.linked_organization_id,
        },
        match_json={
            "role_id": 3,  # Admin
            "type_id": 2,  # Organization
            "resource_id": org.linked_organization_id,
        },
    )
    response = await admin_client.post(
        f"/organizations/{org.id}/employees/{user_id}/make-admin",
    )
    assert response.status_code == 204


async def test_make_user_admin_not_found(
    test_settings: Settings,
    organization_factory: ModelFactory[Organization],
    admin_client: AsyncClient,
    httpx_mock: HTTPXMock,
):
    user_id = str(uuid.uuid4())
    org = await organization_factory(
        linked_organization_id=str(uuid.uuid4()),
    )

    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.optscale_rest_api_base_url}/employees/{user_id}?roles=true",
        match_headers={"Secret": test_settings.optscale_cluster_secret},
        status_code=404,
    )

    response = await admin_client.post(
        f"/organizations/{org.id}/employees/{user_id}/make-admin",
    )
    assert response.status_code == 502
    assert "Error making employee admin in FinOps for Cloud: 404" in response.json()["detail"]


async def test_make_user_admin_error_assigning_role(
    test_settings: Settings,
    organization_factory: ModelFactory[Organization],
    admin_client: AsyncClient,
    httpx_mock: HTTPXMock,
):
    user_id = str(uuid.uuid4())
    org = await organization_factory(
        linked_organization_id=str(uuid.uuid4()),
    )
    auth_user_id = str(uuid.uuid4())

    httpx_mock.add_response(
        method="GET",
        url=f"{test_settings.optscale_rest_api_base_url}/employees/{user_id}?roles=true",
        match_headers={"Secret": test_settings.optscale_cluster_secret},
        status_code=200,
        json={
            "deleted_at": 0,
            "id": "2c2e9705-8023-437c-b09d-8cbd49f0a682",
            "created_at": 1729156673,
            "name": "Ciccio",
            "organization_id": org.linked_organization_id,
            "auth_user_id": auth_user_id,
            "default_ssh_key_id": None,
        },
    )

    httpx_mock.add_response(
        method="POST",
        url=f"{test_settings.optscale_auth_api_base_url}/users/{auth_user_id}/assignment_register",
        match_headers={"Secret": test_settings.optscale_cluster_secret},
        status_code=400,
        match_json={
            "role_id": 3,  # Admin
            "type_id": 2,  # Organization
            "resource_id": org.linked_organization_id,
        },
    )
    response = await admin_client.post(
        f"/organizations/{org.id}/employees/{user_id}/make-admin",
    )
    assert response.status_code == 502
    assert "Error making employee admin in FinOps for Cloud: 400" in response.json()["detail"]
