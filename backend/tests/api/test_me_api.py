from httpx import AsyncClient

from app.db.models import Account, System, User


async def test_get_me_without_token(api_client: AsyncClient):
    response = await api_client.get("/me")

    assert response.status_code == 401
    assert response.json()["detail"] == "Unauthorized."


async def test_get_me_with_user(
    api_client: AsyncClient,
    admin_user_token: str,
    admin_account: Account,
    admin_user: User,
):
    response = await api_client.get("/me", headers={"Authorization": f"Bearer {admin_user_token}"})

    assert response.status_code == 200
    info = response.json()
    assert info["account"]["id"] == admin_account.id
    assert info["account"]["name"] == admin_account.name
    assert info["account"]["type"] == admin_account.type
    assert info["account"]["external_id"] == admin_account.external_id
    assert info["user"]["id"] == admin_user.id
    assert info["user"]["name"] == admin_user.name
    assert info["user"]["email"] == admin_user.email
    assert info["user"]["external_id"] == admin_user.external_id
    assert "system" not in info


async def test_get_me_with_system(
    api_client: AsyncClient,
    ffc_jwt_token: str,
    admin_account: Account,
    ffc_extension: System,
):
    response = await api_client.get("/me", headers={"Authorization": f"Bearer {ffc_jwt_token}"})

    assert response.status_code == 200
    info = response.json()
    assert info["account"]["id"] == admin_account.id
    assert info["account"]["name"] == admin_account.name
    assert info["account"]["type"] == admin_account.type
    assert info["account"]["external_id"] == admin_account.external_id
    assert info["system"]["id"] == ffc_extension.id
    assert info["system"]["name"] == ffc_extension.name
    assert info["system"]["external_id"] == ffc_extension.external_id
    assert "user" not in info
