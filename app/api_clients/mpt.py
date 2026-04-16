from __future__ import annotations

from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from functools import cache, cached_property
from typing import Any

import httpx

from app.conf import get_settings
from app.utils import get_jwt_token_expires


class TokenInfo:
    def __init__(self, token: str):
        self.token = token
        self.expires = get_jwt_token_expires(token)

    def is_expired(self) -> bool:
        return datetime.now(UTC) > self.expires


class MPTExtensionAuth(httpx.Auth):
    requires_response_body = True

    def __init__(self, client: MPTClient):
        self.client = client

    async def async_auth_flow(
        self, request: httpx.Request
    ) -> AsyncGenerator[httpx.Request, httpx.Response]:
        if not self.client.token_info or self.client.token_info.is_expired():
            token_request = self.build_token_request()
            token_response = yield token_request
            token_response.raise_for_status()
            await token_response.aread()
            self.update_token(token_response)

        request.headers["Authorization"] = f"Bearer {self.client.token_info.token}"  # type: ignore
        yield request

    def build_token_request(self) -> httpx.Request:
        """Builds the token refresh request."""
        return httpx.Request(
            "POST",
            f"{self.client.settings.mpt_api_base_url}/integration/installations/-/token",
            headers={"Authorization": f"Bearer {self.client.settings.mpt_extension_token}"},
            params={"account.id": self.client.account_id},
        )

    def update_token(self, response: httpx.Response) -> None:
        """Updates tokens after a successful refresh."""
        if response.status_code == 200:
            data = response.json()
            self.client.token_info = TokenInfo(data["token"])


class MPTClient:
    def __init__(self, account_id: str) -> None:
        self.account_id = account_id
        self.settings = get_settings()
        self.token_info: TokenInfo | None = None

    @cached_property
    def httpx_client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            base_url=self.settings.mpt_api_base_url,
            auth=MPTExtensionAuth(self),
            timeout=httpx.Timeout(
                connect=10.0,
                read=180.0,
                write=2.0,
                pool=5.0,
            ),
        )

    async def get(
        self,
        endpoint: str,
        id: str,
        select: list | None = None,
    ) -> dict[str, Any]:
        url = f"{endpoint}/{id}"
        if select:
            url = f"{url}?select={','.join(select)}"
        response = await self.httpx_client.get(url)
        try:
            response.raise_for_status()
            return response.json()
        finally:
            await response.aclose()

    async def create(self, endpoint: str, payload: dict[str, Any]) -> dict[str, Any]:
        response: httpx.Response = await self.httpx_client.post(
            endpoint,
            json=payload,
        )
        try:
            response.raise_for_status()
            return response.json()
        finally:
            await response.aclose()

    async def update(self, endpoint: str, id: str, payload: dict) -> dict[str, Any]:
        response = await self.httpx_client.put(f"{endpoint}/{id}", json=payload)
        try:
            response.raise_for_status()
            return response.json()
        finally:
            await response.aclose()

    async def delete(self, endpoint: str, id: str) -> None:
        response = await self.httpx_client.delete(f"{endpoint}/{id}")
        try:
            response.raise_for_status()
        finally:
            await response.aclose()

    async def run_object_action(
        self, endpoint: str, id: str, action: str, payload: dict | None = None
    ) -> dict[str, Any] | None:
        response: httpx.Response = await self.httpx_client.post(
            f"{endpoint}/{id}/{action}",
            json=payload,
        )
        try:
            response.raise_for_status()
            return response.json()
        finally:
            await response.aclose()

    async def get_page(
        self,
        endpoint: str,
        limit: int,
        offset: int,
        query: str | None = None,
        select: list[str] | None = None,
    ) -> dict[str, Any]:
        rql = None
        if query or select:
            rql = f"{query or ''}&select={','.join(select or [])}"
        url = f"{endpoint}?{rql or ''}&limit={limit}&offset={offset}"

        response = await self.httpx_client.get(url)
        try:
            response.raise_for_status()
            page = response.json()
            return page
        finally:
            await response.aclose()

    async def collection_iterator(
        self,
        endpoint: str,
        query: str | None = None,
        select: list[str] | None = None,
    ) -> AsyncGenerator[dict, None]:
        offset = 0
        while True:
            page = await self.get_page(
                endpoint, self.settings.mpt_api_rows_per_page, offset, query=query, select=select
            )
            items = page["data"]

            for item in items:
                yield item

            pagination_meta = page["$meta"]["pagination"]
            total = pagination_meta["total"]
            if total <= self.settings.mpt_api_rows_per_page + offset:
                break

            offset = offset + self.settings.mpt_api_rows_per_page

    async def get_user(self, user_id: str, select: list[str] | None = None):
        return await self.get("accounts/users", user_id, select=select)

    async def get_account(self, account_id: str, select: list[str] | None = None):
        return await self.get("accounts/accounts", account_id, select=select)

    async def get_token(self, user_id: str, select: list[str] | None = None):
        return await self.get("accounts/api-tokens", user_id, select=select)

    async def get_order(self, order_id: str, select: list[str] | None = None):
        return await self.get("commerce/orders", order_id, select=select)

    def get_orders(
        self, query: str | None = None, select: list[str] | None = None
    ) -> AsyncGenerator[dict[str, Any], None]:
        return self.collection_iterator("commerce/orders", query=query, select=select)


@cache
def get_installation_client(account_id: str) -> MPTClient:
    return MPTClient(account_id)
