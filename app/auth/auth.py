from typing import Annotated

import httpx
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth.constants import UNAUTHORIZED_EXCEPTION
from app.auth.context import MPTAuthContext as _MPTAuthContext
from app.conf import get_settings
from app.utils import get_jwt_token_claims

security = HTTPBearer(auto_error=False)


async def resolve_installation(account_id: str) -> str | None:
    settings = get_settings()
    query = f"and(eq(account.id,{account_id}),eq(status,Installed))"
    url = f"/integration/extensions/{settings.mpt_extension_id}/installations?{query}"
    async with httpx.AsyncClient(
        base_url=settings.mpt_api_base_url,
        headers={"Authorization": f"Bearer {settings.mpt_extension_token}"},
    ) as client:
        response = await client.get(url)
        response.raise_for_status()
        data = response.json()
        if len(data["data"]) > 0:
            return data["data"][0]["id"]


async def get_auth_context(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
) -> _MPTAuthContext:
    if not credentials:
        raise UNAUTHORIZED_EXCEPTION

    token = credentials.credentials

    claims = get_jwt_token_claims(token)

    account_id = claims["https://claims.softwareone.com/accountId"]
    account_type = claims["https://claims.softwareone.com/accountType"]
    installation_id = claims.get("https://claims.softwareone.com/installationId")
    user_id = claims.get("https://claims.softwareone.com/userId")
    token_id = claims.get("https://claims.softwareone.com/apiTokenId")
    if not installation_id:
        installation_id = await resolve_installation(account_id)

    ctx = _MPTAuthContext(
        account_id=account_id,
        account_type=account_type,
        installation_id=installation_id,
        user_id=user_id,
        token_id=token_id,
    )
    return ctx


MPTAuthContext = Annotated[_MPTAuthContext, Depends(get_auth_context)]
