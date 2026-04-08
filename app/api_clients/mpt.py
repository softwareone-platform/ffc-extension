from __future__ import annotations

import json
import secrets
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from functools import cache, cached_property
from typing import Any

import httpx

from app.billing.enum import JournalStatus
from app.conf import get_settings
from app.utils import get_jwt_token_expires


class TokenInfo:
    def __init__(self, token: str):
        self.token = token
        self.expires = get_jwt_token_expires(token)

    def is_expired(self) -> bool:
        return datetime.now(UTC) > self.expires


class MPTInstallationAuth(httpx.Auth):
    requires_response_body = True

    def __init__(self, account_id: str):
        self.account_id = account_id
        self.token_info: TokenInfo | None = None
        self.settings = get_settings()

    async def async_auth_flow(
        self, request: httpx.Request
    ) -> AsyncGenerator[httpx.Request, httpx.Response]:
        if not self.token_info or self.token_info.is_expired():
            token_request = self.build_token_request()
            token_response = yield token_request
            token_response.raise_for_status()
            await token_response.aread()
            self.update_token(token_response)

        request.headers["Authorization"] = f"Bearer {self.token_info.token}"
        yield request

    def build_token_request(self) -> httpx.Request:
        """Builds the token refresh request."""
        return httpx.Request(
            "POST",
            f"{self.settings.mpt_api_base_url}integration/installations/-/token",
            headers={"Authorization": f"Bearer {self.settings.mpt_extension_token}"},
            params={"account.id": self.account_id},
        )

    def update_token(self, response: httpx.Response) -> None:
        """Updates tokens after a successful refresh."""
        if response.status_code == 200:
            data = response.json()
            self.token_info = TokenInfo(data["token"])


class MPTExtensionAuth(httpx.Auth):
    def __init__(self):
        self.settings = get_settings()

    async def async_auth_flow(
        self, request: httpx.Request
    ) -> AsyncGenerator[httpx.Request, httpx.Response]:
        request.headers["Authorization"] = f"Bearer {self.settings.mpt_extension_token}"
        yield request


class MPTClient:
    def __init__(self, auth: httpx.Auth) -> None:
        self.auth = auth
        self.settings = get_settings()

    @cached_property
    def httpx_client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            base_url=self.settings.mpt_api_base_url,
            auth=self.auth,
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

    async def get_collection(
        self,
        endpoint: str,
        query: str | None = None,
        select: list[str] | None = None,
    ) -> dict[str, Any]:
        parts = []
        if query:
            parts.append(query)
        if select:
            parts.append(f"select={','.join(select)}")
        url = f"{endpoint}?{'&'.join(parts)}" if parts else endpoint

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
        parts = []
        if query:
            parts.append(query)
        if select:
            parts.append(f"select={','.join(select)}")
        parts.extend([f"limit={limit}", f"offset={offset}"])
        url = f"{endpoint}?{'&'.join(parts)}"

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
    ) -> AsyncGenerator[dict[str, Any], None]:
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

    async def get_authorization(
        self,
        authorization_id: str,
    ) -> dict[str, Any]:
        return await self.get("catalog/authorizations/", id=authorization_id)

    def get_authorizations_for_product(
        self,
    ) -> AsyncGenerator[dict[str, Any], None]:
        return self.collection_iterator(
            "catalog/authorizations", query=f"eq(product.id,{self.settings.mpt_product_id[0]})"
        )

    async def get_user(self, user_id: str, select: list[str] | None = None) -> dict[str, Any]:
        return await self.get("accounts/users", user_id, select=select)

    async def get_account(self, account_id: str, select: list[str] | None = None) -> dict[str, Any]:
        return await self.get("accounts/accounts", account_id, select=select)

    async def get_token(self, user_id: str, select: list[str] | None = None) -> dict[str, Any]:
        return await self.get("accounts/api-tokens", user_id, select=select)

    async def get_order(self, order_id: str, select: list[str] | None = None) -> dict[str, Any]:
        return await self.get("commerce/orders", order_id, select=select)

    async def get_task(self, task_id: str, select: list[str] | None = None) -> dict[str, Any]:
        return await self.get("system/tasks", task_id, select=select)

    async def update_task(self, task_id: str, payload: dict) -> dict[str, Any]:
        return await self.update("system/tasks", task_id, payload=payload)

    async def start_task(self, task_id: str) -> dict[str, Any] | None:
        return await self.run_object_action("system/tasks", task_id, "execute")

    async def complete_task(
        self, task_id: str, payload: dict | None = None
    ) -> dict[str, Any] | None:
        return await self.run_object_action("system/tasks", task_id, "complete", payload=payload)

    async def get_first(
        self,
        endpoint: str,
        query: str | None = None,
        select: list[str] | None = None,
    ) -> dict[str, Any] | None:
        items = await self.get_page(
            endpoint,
            limit=1,
            offset=0,
            query=query,
            select=select,
        )
        if items["data"]:
            return items["data"][0]
        return None

    async def count(
        self,
        endpoint: str,
        query: str | None = None,
    ) -> int:
        page = await self.get_page(endpoint, limit=0, offset=0, query=query)
        return page["$meta"]["pagination"]["total"]

    def get_orders(
        self, query: str | None = None, select: list[str] | None = None
    ) -> AsyncGenerator[dict[str, Any], None]:
        return self.collection_iterator("commerce/orders", query=query, select=select)

    async def get_journal_by_authorization_external_id(
        self, authorization_id: str, external_id: str
    ) -> dict[str, Any] | None:
        rql = (
            "and("
            f"eq(authorization.id,{authorization_id}),"
            f"eq(externalIds.vendor,{external_id}),"
            f"ne(status,{JournalStatus.DELETED.value})"
            ")"
        )

        return await self.get_first("billing/journals", query=rql)

    async def count_active_agreements(
        self,
        authorization_id: str,
        start_date: datetime,
        end_date: datetime,
    ):
        rql = (
            "and("
            f"eq(authorization.id,{authorization_id}),"
            "or("
            f"and(eq(status,{JournalStatus.ACTIVE.value}),le(audit.active.at,{end_date.strftime('%Y-%m-%dT%H:%M:%SZ')})),"
            f"and(eq(status,{JournalStatus.TERMINATED.value}),le(audit.terminated.at,{end_date.strftime('%Y-%m-%dT%H:%M:%SZ')}),"
            f"ge(audit.terminated.at,{start_date.strftime('%Y-%m-%dT%H:%M:%SZ')}))"
            ")"
            ")"
        )

        return await self.count(endpoint="commerce/agreements", query=rql)

    def get_agreements_by_organization(
        self, organization_id: str
    ) -> AsyncGenerator[dict[str, Any], None]:
        rql = f"eq(externalIds.vendor,{organization_id})&select=parameters"
        return self.collection_iterator("commerce/agreements", rql)

    async def create_journal(
        self, authorization_id: str, external_id: str, name: str, due_date: datetime
    ) -> dict[str, Any]:

        return await self.create(
            endpoint="/billing/journals",
            payload={
                "authorization": {"id": authorization_id},
                "externalIds": {"vendor": external_id},
                "name": name,
                "dueDate": due_date.isoformat(),
            },
        )

    async def upload_journal_charges(self, journal_id: str, charges_file: Any) -> None:
        response = await self.httpx_client.post(
            f"billing/journals/{journal_id}/upload",
            files={
                "file": (charges_file.name, charges_file, "application/jsonl"),
            },
        )
        response.raise_for_status()

    async def get_journal_attachment(
        self, journal_id: str, file_prefix: str
    ) -> dict[str, Any] | None:
        return await self.get_first(
            f"billing/journals/{journal_id}/attachments",
            query=f"like(name,{file_prefix}*)",
        )

    async def get_journal(self, journal_id: str, select: list[str] | None = None) -> dict[str, Any]:
        return await self.get("billing/journals/", journal_id, select=select)

    async def delete_journal_attachment(self, journal_id: str, attachment_id: str) -> None:
        return await self.delete(
            endpoint=f"billing/journals/{journal_id}/attachments",
            id=attachment_id,
        )

    async def create_journal_attachment(
        self, journal_id: str, filename: str, json_data: str
    ) -> None:

        boundary = f"----{secrets.token_hex(8)}"
        # Data parts
        attachment_content = json.dumps(
            {"name": filename, "description": "Currency conversion rates"}
        )
        body = (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="file"; filename="{filename}.json"\r\n'
            "Content-Type: application/json\r\n"
            "\r\n"
            f"{json_data}\r\n"
            f"--{boundary}\r\n"
            'Content-Disposition: form-data; name="attachment"\r\n'
            "Content-Type: application/json\r\n"
            "\r\n"
            f"{attachment_content}\r\n"
            f"--{boundary}--\r\n"
        ).encode()

        response = await self.httpx_client.post(
            url=f"billing/journals/{journal_id}/attachments",
            content=body,
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        )
        try:
            response.raise_for_status()
        finally:
            await response.aclose()

    async def submit_journal(self, journal_id: str) -> None:
        response = await self.httpx_client.post(f"billing/journals/{journal_id}/submit")
        response.raise_for_status()


@cache
def get_installation_client(account_id: str) -> MPTClient:
    return MPTClient(MPTInstallationAuth(account_id))
