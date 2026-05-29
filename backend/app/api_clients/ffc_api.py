import logging
from collections.abc import Generator
from uuid import UUID

import httpx

from app.api_clients.base import APIClientError, BaseAPIClient
from app.conf import Settings

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
        params: list[tuple[str, str]] = []
        if limit is not None:
            params.append(("limit", str(limit)))
        if offset is not None:
            params.append(("offset", str(offset)))
        if rql:
            params.extend((clause, "") for clause in rql.split("&"))

        response = await self.httpx_client.get(
            f"/admin/organizations/{organization_id}/users",
            params=params,
        )
        response.raise_for_status()
        return response
