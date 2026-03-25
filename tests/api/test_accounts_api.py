from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi import HTTPException, status
from httpx import AsyncClient
from pytest_mock import MockerFixture
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.handlers import NotFoundError
from app.db.models import Account, AccountUser, System, User
from app.dependencies.db import AccountRepository
from app.enums import AccountStatus, AccountType, UserStatus
from app.routers.accounts import (
    fetch_account_or_404,
    validate_account_type_and_required_conditions,
    validate_required_conditions_before_update,
)
from app.schemas.accounts import AccountCreate
from tests.types import JWTTokenFactory, ModelFactory


@pytest.fixture
def mock_account_repo():
    return AsyncMock(spec=AccountRepository)


# ====================
# Authentication Tests
# ====================


async def test_get_accounts_without_token(api_client: AsyncClient):
    response = await api_client.get("/accounts")

    assert response.status_code == 401
    assert response.json()["detail"] == "Unauthorized."


async def test_get_account_with_invalid_token(api_client: AsyncClient):
    response = await api_client.get(
        "/accounts",
        headers={"Authorization": "Bearer invalid.token.here"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Unauthorized."


async def test_get_accounts_with_expired_token(
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
        "/accounts",
        headers={"Authorization": f"Bearer {expired_token}"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Unauthorized."


# ====================
# Create Accounts Tests
# ====================


async def test_can_create_accounts(
    operations_client: AsyncClient,
    ffc_extension: System,
    db_session: AsyncSession,
):
    response = await operations_client.post(
        "/accounts",
        json={"name": "Microsoft", "external_id": "ACC-9044-8753", "type": "affiliate"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["id"] is not None
    assert data["name"] == "Microsoft"
    assert data["external_id"] == "ACC-9044-8753"
    assert data["type"] == "affiliate"
    assert data["status"] == "active"
    assert data["events"]["created"]["at"] is not None
    assert data["events"]["created"]["by"]["id"] == str(ffc_extension.id)
    assert data["events"]["created"]["by"]["type"] == ffc_extension.type
    assert data["events"]["created"]["by"]["name"] == ffc_extension.name
    assert data["events"]["updated"]["at"] is not None
    assert data["events"]["updated"]["by"]["id"] == str(ffc_extension.id)
    assert data["events"]["updated"]["by"]["type"] == ffc_extension.type
    assert data["events"]["updated"]["by"]["name"] == ffc_extension.name

    result = await db_session.execute(select(Account).where(Account.id == data["id"]))
    assert result.one_or_none() is not None


async def test_create_accounts_type_not_affiliate(
    operations_client: AsyncClient,
    ffc_jwt_token: str,
    ffc_extension: System,
    db_session: AsyncSession,
):
    response = await operations_client.post(
        "/accounts",
        json={"name": "Microsoft", "external_id": "ACC-9044-8753", "type": "operations"},
    )
    assert response.status_code == 400

    response = await operations_client.post(
        "/accounts",
        json={"external_id": "ACC-9044-8753", "type": "affiliate"},
    )
    assert response.status_code == 422

    response = await operations_client.post(
        "/accounts",
        json={"name": "Microsoft", "type": "affiliate"},
    )
    assert response.status_code == 422


async def test_create_accounts_incomplete_body(
    operations_client: AsyncClient,
    ffc_extension: System,
    db_session: AsyncSession,
):
    response = await operations_client.post(
        "/accounts",
        json={"name": "Microsoft", "external_id": "ACC-9044-8753"},
    )
    assert response.status_code == 422


async def test_cannot_create_accounts_if_context_is_not_operations_account(
    affiliate_account: Account, affiliate_client: AsyncClient
):
    response = await affiliate_client.post(
        "/accounts",
        json={"name": "Microsoft", "external_id": "ACC-9044-8753", "type": "affiliate"},
    )
    data = response.json()
    assert response.status_code == 403
    assert data.get("detail") == "You've found the door, but you don't have the key."


# ====================
# Get Accounts Tests
# ====================


async def test_get_account_by_id(
    affiliate_account: Account,
    operations_client: AsyncClient,
    ffc_extension: System,
):
    response = await operations_client.get(
        f"/accounts/{affiliate_account.id}",
    )

    assert response.status_code == 200
    data = response.json()

    assert data["id"] == affiliate_account.id
    assert data["name"] == affiliate_account.name
    assert data["external_id"] == affiliate_account.external_id
    assert data["type"] == affiliate_account.type
    assert data["status"] == affiliate_account.status
    assert data["events"]["created"]["at"] is not None
    assert data["events"]["created"]["by"]["id"] == str(ffc_extension.id)
    assert data["events"]["created"]["by"]["type"] == ffc_extension.type
    assert data["events"]["created"]["by"]["name"] == ffc_extension.name
    assert data["events"]["updated"]["at"] is not None
    assert data["events"]["updated"]["by"]["id"] == str(ffc_extension.id)
    assert data["events"]["updated"]["by"]["type"] == ffc_extension.type
    assert data["events"]["updated"]["by"]["name"] == ffc_extension.name
    assert data["stats"]["entitlements"]["new"] == affiliate_account.new_entitlements_count
    assert data["stats"]["entitlements"]["redeemed"] == affiliate_account.active_entitlements_count
    assert (
        data["stats"]["entitlements"]["terminated"]
        == affiliate_account.terminated_entitlements_count
    )


async def test_get_account_by_id_no_auth(
    affiliate_account: Account,
    api_client: AsyncClient,
    ffc_extension: System,
):
    response = await api_client.get(
        f"/accounts/{affiliate_account.id}",
    )
    assert response.status_code == 401


async def test_get_invalid_account(operations_client: AsyncClient, ffc_jwt_token: str):
    id = "FACC-1369-9180"
    response = await operations_client.get(f"/accounts/{id}")

    assert response.status_code == 404
    assert response.json()["detail"] == f"Account with ID `{id}` wasn't found."


async def test_get_invalid_id_format(operations_client: AsyncClient, ffc_jwt_token: str):
    response = await operations_client.get(
        "/accounts/this-is-not-a-valid-uuid",
    )

    assert response.status_code == 422

    [detail] = response.json()["detail"]
    assert detail["loc"] == ["path", "id"]
    assert detail["type"] == "string_pattern_mismatch"


async def test_get_all_accounts(operations_client: AsyncClient, ffc_jwt_token: str):
    response = await operations_client.get(
        "/accounts",
        headers={"Authorization": f"Bearer {ffc_jwt_token}"},
    )

    assert response.status_code == 200
    assert response.json()["total"] == 1


async def test_get_all_accounts_single_page(
    operations_account, api_client: AsyncClient, ffc_jwt_token: str
):
    response = await api_client.get(
        "/accounts",
        headers={"Authorization": f"Bearer {ffc_jwt_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["items"]) == data["total"]


async def test_get_all_account_multiple_pages(
    account_factory: ModelFactory[Account],
    operations_client: AsyncClient,
):
    for _ in range(11):
        await account_factory(
            name="SWO",
            type=AccountType.OPERATIONS,
            status=AccountStatus.ACTIVE,
            external_id=str(uuid4()),
        )

    first_page_response = await operations_client.get(
        "/accounts",
        params={"limit": 5},
    )
    first_page_data = first_page_response.json()
    assert first_page_response.status_code == 200
    assert first_page_data["total"] == 12
    assert len(first_page_data["items"]) == 5
    assert first_page_data["limit"] == 5
    assert first_page_data["offset"] == 0

    second_page_response = await operations_client.get(
        "/accounts",
        params={"limit": 3, "offset": 5},
    )
    second_page_data = second_page_response.json()

    assert second_page_response.status_code == 200
    assert second_page_data["total"] == 12
    assert len(second_page_data["items"]) == 3
    assert second_page_data["limit"] == 3
    assert second_page_data["offset"] == 5

    third_page_response = await operations_client.get(
        "/accounts",
        params={"offset": 8},
    )
    third_page_data = third_page_response.json()

    assert third_page_response.status_code == 200
    assert third_page_data["total"] == 12
    assert len(third_page_data["items"]) == 4
    assert third_page_data["limit"] > 2
    assert third_page_data["offset"] == 8

    all_items = first_page_data["items"] + second_page_data["items"] + third_page_data["items"]
    assert len(all_items) == 12


# ====================
# Validation Functions Tests
# ====================


async def test_validate_account_type_and_required_conditions_account_type_operations():
    account_repo = AccountRepository

    data = AccountCreate(name="Microsoft", external_id=str(uuid4()), type=AccountType.OPERATIONS)
    with pytest.raises(HTTPException) as exc_info:
        await validate_account_type_and_required_conditions(account_repo, data)
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "You cannot create an Account of type Operations."


async def test_validate_account_type_and_required_conditions_account_deleted(
    mocker: MockerFixture,
):
    account_repo = mocker.Mock()
    account_repo.first = AsyncMock(return_value=True)

    data = AccountCreate(name="Microsoft", external_id="ACC-9044-8753", type=AccountType.AFFILIATE)

    with pytest.raises(HTTPException) as exc_info:
        await validate_account_type_and_required_conditions(account_repo, data)

    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    assert "An Account with external ID `ACC-9044-8753` already exists." in str(
        exc_info.value.detail
    )


def test_validate_required_conditions_before_update_account_type_operations(
    operations_account: Account,
):
    with pytest.raises(HTTPException) as exc_info:
        validate_required_conditions_before_update(account=operations_account)
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "You cannot update an Account of type Operations."


def test_validate_required_conditions_before_update_account_deleted():
    account = Account(name="Microsoft", external_id="ACC-9044-8753", type=AccountType.AFFILIATE)
    account.status = AccountStatus.DELETED
    with pytest.raises(HTTPException) as exc_info:
        validate_required_conditions_before_update(account=account)

    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    assert "You cannot update an Account Deleted." in str(exc_info.value.detail)


# =================
# UPDATE Accounts
# =================


async def test_can_update_accounts_name(
    operations_client: AsyncClient,
    ffc_extension: System,
    affiliate_account: Account,
    db_session: AsyncSession,
):
    response = await operations_client.put(
        f"/accounts/{affiliate_account.id}",
        json={"name": "AWS"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] is not None
    assert data["name"] == "AWS"
    assert data["external_id"] == affiliate_account.external_id
    assert data["type"] == affiliate_account.type
    assert data["status"] == affiliate_account.status
    assert data["events"]["created"]["at"] is not None
    assert data["events"]["updated"]["at"] is not None
    assert data["events"]["updated"]["by"]["id"] == str(ffc_extension.id)
    assert data["events"]["updated"]["by"]["type"] == ffc_extension.type
    assert data["events"]["updated"]["by"]["name"] == ffc_extension.name

    result = await db_session.execute(select(Account).where(Account.id == data["id"]))
    assert result.one_or_none() is not None


async def test_update_account_empty_body(
    operations_client: AsyncClient,
    ffc_extension: System,
    affiliate_account: Account,
    db_session: AsyncSession,
):
    response = await operations_client.put(
        f"/accounts/{affiliate_account.id}",
        json={},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "At least one field must be sent for update."


async def test_can_update_accounts_external_id(
    operations_client: AsyncClient,
    ffc_extension: System,
    affiliate_account: Account,
    db_session: AsyncSession,
):
    response = await operations_client.put(
        f"/accounts/{affiliate_account.id}",
        json={"external_id": "ACC-9044-8753"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] is not None
    assert data["name"] == "Microsoft"
    assert data["external_id"] == "ACC-9044-8753"
    assert data["type"] == affiliate_account.type
    assert data["status"] == affiliate_account.status
    assert data["events"]["created"]["at"] is not None
    assert data["events"]["updated"]["at"] is not None
    assert data["events"]["updated"]["by"]["id"] == str(ffc_extension.id)
    assert data["events"]["updated"]["by"]["type"] == ffc_extension.type
    assert data["events"]["updated"]["by"]["name"] == ffc_extension.name

    result = await db_session.execute(select(Account).where(Account.id == data["id"]))
    assert result.one_or_none() is not None


async def test_cannot_update_if_status_is_not_active(
    api_client: AsyncClient,
    ffc_jwt_token: str,
    account_factory: ModelFactory[Account],
):
    account = await account_factory(
        status=AccountStatus.DELETED,
        type=AccountType.AFFILIATE,
        name="Microsoft",
        external_id="ACC-9044-8753",
    )
    response = await api_client.put(
        f"/accounts/{account.id}",
        headers={"Authorization": f"Bearer {ffc_jwt_token}"},
        json={"name": "AWS"},
    )
    assert response.status_code == 400


async def test_cannot_update_disabled_accounts(
    operations_client: AsyncClient,
    affiliate_account: Account,
):
    response = await operations_client.put(
        f"/accounts/{affiliate_account.id}",
        json={"status": AccountStatus.DISABLED},
    )
    data = response.json()
    assert response.status_code == 422
    assert data == {
        "detail": [
            {
                "type": "extra_forbidden",
                "loc": ["body", "status"],
                "msg": "Extra inputs are not permitted",
                "input": "disabled",
            }
        ]
    }


async def test_cannot_update_accounts_if_context_is_not_operations_account(
    affiliate_account: Account, affiliate_client: AsyncClient
):
    response = await affiliate_client.put(
        f"/accounts/{affiliate_account.id}",
        json={"name": "AWS"},
    )
    data = response.json()
    assert response.status_code == 403
    assert data.get("detail") == "You've found the door, but you don't have the key."


async def test_can_only_updated_the_name_and_external_id(
    operations_client: AsyncClient,
    affiliate_account: Account,
):
    response = await operations_client.put(
        f"/accounts/{affiliate_account.id}",
        json={"type": AccountType.OPERATIONS},
    )
    data = response.json()
    assert response.status_code == 422
    assert data == {
        "detail": [
            {
                "type": "extra_forbidden",
                "loc": ["body", "type"],
                "msg": "Extra inputs are not permitted",
                "input": "operations",
            }
        ]
    }

    response = await operations_client.put(
        f"/accounts/{affiliate_account.id}",
        json={"status": AccountStatus.DISABLED},
    )
    data = response.json()
    assert response.status_code == 422
    assert data == {
        "detail": [
            {
                "type": "extra_forbidden",
                "loc": ["body", "status"],
                "msg": "Extra inputs are not permitted",
                "input": "disabled",
            }
        ]
    }


# -------
# List Account Users
# -------


async def test_can_list_account_users(
    operations_client: AsyncClient,
    operations_account: Account,
    accountuser_factory: ModelFactory[AccountUser],
    user_factory: ModelFactory[User],
):
    user = await user_factory(
        name="Peter Parker",
        email="peter.parker@spiderman.com",
        status=UserStatus.ACTIVE,
    )
    await accountuser_factory(
        user_id=user.id, account_id=operations_account.id, status=AccountStatus.ACTIVE
    )

    response = await operations_client.get(f"/accounts/{operations_account.id}/users")
    data = response.json()
    assert response.status_code == 200
    assert isinstance(data.get("items"), list)


async def test_list_account_users_deleted_not_included_for_affiliate(
    affiliate_client: AsyncClient,
    gcp_account: Account,
    accountuser_factory: ModelFactory[AccountUser],
    user_factory: ModelFactory[User],
):
    user = await user_factory(
        name="Peter Parker",
        email="peter.parker@spiderman.com",
        status=UserStatus.ACTIVE,
    )
    await accountuser_factory(
        user_id=user.id, account_id=gcp_account.id, status=AccountStatus.DELETED
    )

    response = await affiliate_client.get(f"/accounts/{gcp_account.id}/users")
    data = response.json()
    assert response.status_code == 200
    assert len(data["items"]) == 0


async def test_list_not_existing_account_id(
    affiliate_account: Account,
    operations_client: AsyncClient,
):
    response = await operations_client.get(
        f"/accounts/{affiliate_account.id}/users",
    )
    assert response.status_code == 200


async def test_cannot_access_not_existing_account_id_with_operations_account_context(
    operations_client: AsyncClient,
):
    response = await operations_client.get(
        "/accounts/FACC-8751-0928/users",
    )
    assert response.status_code == 404
    data = response.json()
    assert data.get("detail") == "Account with ID `FACC-8751-0928` wasn't found."


async def test_cannot_cheat_account_type_and_context(
    affiliate_client: AsyncClient, operations_account: Account
):
    response = await affiliate_client.get(
        f"/accounts/{operations_account.id}/users",
    )
    assert response.status_code == 404


async def test_fetch_account_or_404_account_not_found(mock_account_repo: AsyncMock):
    mock_account_repo.get.side_effect = NotFoundError("Account not found")

    with pytest.raises(HTTPException) as exc_info:
        await fetch_account_or_404("invalid_account_id", mock_account_repo)

    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
    assert str(exc_info.value.detail) == "Account not found"
    mock_account_repo.get.assert_awaited_once_with(id="invalid_account_id")


async def test_get_all_list_account_users_multiple_pages(
    operations_client: AsyncClient,
    operations_account: Account,
    accountuser_factory: ModelFactory[AccountUser],
    user_factory: ModelFactory[User],
    db_session: AsyncSession,
):
    users_ids = []
    for index in range(30):
        user = await user_factory(
            name=f"Peter Parker_{index}",
            email=f"peter.parker_{index}@spiderman.com",
            status=UserStatus.ACTIVE,
        )
        users_ids.append(user.id)

    for user_id in users_ids:
        await accountuser_factory(
            user_id=user_id, account_id=operations_account.id, status=AccountStatus.ACTIVE
        )

    first_page_response = await operations_client.get(
        f"/accounts/{operations_account.id}/users",
        params={"limit": 5},
    )
    first_page_data = first_page_response.json()
    result = await db_session.execute(select(Account).where(Account.id == operations_account.id))
    assert result.one_or_none() is not None
    assert first_page_response.status_code == 200
    assert first_page_data["total"] == 30
    assert len(first_page_data["items"]) == 5
    assert first_page_data["limit"] == 5
    assert first_page_data["offset"] == 0
    #
    second_page_response = await operations_client.get(
        f"/accounts/{operations_account.id}/users",
        params={"limit": 3, "offset": 5},
    )
    second_page_data = second_page_response.json()

    assert second_page_response.status_code == 200
    assert second_page_data["total"] == 30
    assert len(second_page_data["items"]) == 3
    assert second_page_data["limit"] == 3
    assert second_page_data["offset"] == 5

    third_page_response = await operations_client.get(
        f"/accounts/{operations_account.id}/users",
        params={"offset": 8},
    )
    third_page_data = third_page_response.json()

    assert third_page_response.status_code == 200
    assert third_page_data["total"] == 30
    assert len(third_page_data["items"]) == 22
    assert third_page_data["limit"] > 2
    assert third_page_data["offset"] == 8

    all_items = first_page_data["items"] + second_page_data["items"] + third_page_data["items"]
    assert len(all_items) == 30


# -------
# Remove User From Account
# -------


async def test_can_remove_user_from_account(
    operations_client: AsyncClient,
    operations_account: Account,
    accountuser_factory: ModelFactory[AccountUser],
    user_factory: ModelFactory[User],
):
    user = await user_factory(
        name="Peter Parker",
        email="peter.parker@spiderman.com",
        status=UserStatus.ACTIVE,
    )
    await accountuser_factory(
        user_id=user.id, account_id=operations_account.id, status=AccountStatus.ACTIVE
    )

    response = await operations_client.delete(f"/accounts/{operations_account.id}/users/{user.id}")
    assert response.status_code == 204


async def test_cannot_remove_user_from_account_without_auth(
    api_client: AsyncClient,
    operations_account: Account,
    accountuser_factory: ModelFactory[AccountUser],
    user_factory: ModelFactory[User],
):
    user = await user_factory(
        name="Peter Parker",
        email="peter.parker@spiderman.com",
        status=UserStatus.ACTIVE,
    )
    await accountuser_factory(
        user_id=user.id, account_id=operations_account.id, status=AccountStatus.ACTIVE
    )

    response = await api_client.delete(f"/accounts/{operations_account.id}/users/{user.id}")
    assert response.status_code == 401


async def test_remove_with_not_existing_user_id(
    operations_client: AsyncClient,
    operations_account: Account,
):
    wrong_user_id = "FUSR-4068-9870"
    response = await operations_client.delete(
        f"/accounts/{operations_account.id}/users/{wrong_user_id}"
    )
    assert response.status_code == 400
    data = response.json()
    assert (
        data.get("detail")
        == f"The User `{wrong_user_id}` does not belong to the Account with ID `{operations_account.id}`."  # noqa: E501
    )


async def test_remove_cheat_account_type_and_context(
    affiliate_client: AsyncClient, operations_account: Account
):
    wrong_user_id = "FUSR-4068-9870"
    response = await affiliate_client.delete(
        f"/accounts/{operations_account.id}/users/{wrong_user_id}"
    )
    assert response.status_code == 404


async def test_cannot_remove_deleted_user_from_account(
    operations_client: AsyncClient,
    operations_account: Account,
    accountuser_factory: ModelFactory[AccountUser],
    user_factory: ModelFactory[User],
):
    user = await user_factory(
        name="Peter Parker",
        email="peter.parker@spiderman.com",
        status=UserStatus.ACTIVE,
    )
    await accountuser_factory(
        user_id=user.id, account_id=operations_account.id, status=AccountStatus.DELETED
    )

    response = await operations_client.delete(f"/accounts/{operations_account.id}/users/{user.id}")
    assert response.status_code == 400
    data = response.json()
    assert (
        data.get("detail")
        == f"The User `{user.id}` does not belong to the Account with ID `{operations_account.id}`."
    )


async def test_get_account_with_filters(
    account_factory: ModelFactory[Account],
    api_client: AsyncClient,
    ffc_jwt_token: str,
):
    account_1 = await account_factory(
        name="First",
    )
    await account_factory(
        name="Second",
    )

    response = await api_client.get(
        "/accounts?eq(name,First)",
        headers={"Authorization": f"Bearer {ffc_jwt_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["name"] == account_1.name


async def test_get_accounts_with_filters_and_ordering(
    account_factory: ModelFactory[Account],
    api_client: AsyncClient,
    ffc_jwt_token: str,
):
    await account_factory(
        name="Pilly",
        status=AccountStatus.ACTIVE,
    )
    await account_factory(
        name="Vanilly",
        status=AccountStatus.ACTIVE,
    )
    await account_factory(
        name="Milly",
        status=AccountStatus.DELETED,
    )

    response = await api_client.get(
        "/accounts?and(ilike(name,*lly),in(status,(active,disabled)))&order_by(name)",
        headers={"Authorization": f"Bearer {ffc_jwt_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == len(data["items"])
    names = [item["name"] for item in data["items"]]
    assert names == ["Pilly", "Vanilly"]


async def test_get_accounts_with_filters_relationship(
    account_factory: ModelFactory[Account],
    api_client: AsyncClient,
    system_factory: ModelFactory[System],
    ffc_jwt_token: str,
):
    created_by = await system_factory(name="Oracle")

    await account_factory(
        name="Pilly",
        status=AccountStatus.ACTIVE,
        created_by=created_by,
    )
    await account_factory(
        name="Vanilly",
        status=AccountStatus.ACTIVE,
    )
    await account_factory(
        name="Milly",
        status=AccountStatus.ACTIVE,
        created_by=created_by,
    )

    response = await api_client.get(
        "/accounts?ilike(events.created.by.name,*racl*)&order_by(-name)",
        headers={"Authorization": f"Bearer {ffc_jwt_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == len(data["items"])
    names = [item["name"] for item in data["items"]]
    assert names == ["Pilly", "Milly"]
