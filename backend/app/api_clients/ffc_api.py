import logging
from collections.abc import Generator
from typing import Any
from uuid import UUID

import httpx

from app.api_clients.base import APIClientError, BaseAPIClient
from app.conf import Settings
from app.enums import TagType

logger = logging.getLogger(__name__)


class FFCAPIClientError(APIClientError):
    pass


class FFCAPIAuthClientError(APIClientError):
    pass


class FFCAPIClusterSecretAuth(httpx.Auth):
    def __init__(self, settings: Settings):
        self.settings = settings

    def auth_flow(self, request: httpx.Request) -> Generator[httpx.Request, httpx.Response, None]:
        request.headers["Secret"] = self.settings.optscale_cluster_secret

        yield request


def resolve_params(
    limit: int | None = None, offset: int | None = None, rql: str | None = None
) -> list[tuple[str, str | int | float | bool | None]]:
    params: list[tuple[str, str | int | float | bool | None]] = []
    if limit is not None:
        params.append(("limit", str(limit)))
    if offset is not None:
        params.append(("offset", str(offset)))
    if rql:
        params.extend((clause, "") for clause in rql.split("&"))

    return params


class FFCAPIClient(BaseAPIClient):
    @property
    def base_url(self):
        return self.settings.optscale_ffc_api_base_url

    @property
    def auth(self):
        return FFCAPIClusterSecretAuth(self.settings)

    async def fetch_users_for_organization(
        self,
        organization_id: UUID | str,
        limit: int | None = None,
        offset: int | None = None,
        rql: str | None = None,
    ) -> httpx.Response:
        response = await self.httpx_client.get(
            f"/admin/organizations/{organization_id}/users",
            params=resolve_params(limit=limit, offset=offset, rql=rql),
        )
        response.raise_for_status()
        return response

    async def fetch_datasources_for_organization(
        self,
        organization_id: UUID | str,
        limit: int | None = None,
        offset: int | None = None,
        rql: str | None = None,
    ) -> httpx.Response:
        response = await self.httpx_client.get(
            f"/admin/organizations/{organization_id}/datasources",
            params=resolve_params(limit=limit, offset=offset, rql=rql),
        )
        response.raise_for_status()
        return response

    async def fetch_expenses_for_organization(self, organization_id: UUID | str) -> httpx.Response:
        response = await self.httpx_client.get(f"/admin/organizations/{organization_id}/expenses")
        response.raise_for_status()
        return response

    async def create_tag(self, payload: dict[str, Any]) -> httpx.Response:
        response = await self.httpx_client.post("/admin/tags", json=payload)
        response.raise_for_status()
        return response

    async def create_tag_for_datasource(
        self,
        datasource_id: UUID | str,
        name: str,
        value: str,
    ) -> httpx.Response:
        payload = {
            "resource_id": datasource_id,
            "resource_type": TagType.DATA_SOURCE,
            "name": name,
            "value": value,
        }

        return await self.create_tag(payload)
