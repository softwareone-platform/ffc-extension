import textwrap
import uuid
from typing import Any, Protocol, TypeVar

import httpx
import pytest
from fastapi import status
from pydantic.v1.utils import deep_update
from pytest_httpx import HTTPXMock

from app.api_clients.base import BaseAPIClient
from app.api_clients.optscale import OptscaleClient
from app.conf import Settings
from app.db.models import Organization

C = TypeVar("C", bound=BaseAPIClient)


class BaseMockAPIClient(Protocol[C]):
    real_client: C
    httpx_mock: HTTPXMock

    def __init__(self, test_settings: Settings, httpx_mock: HTTPXMock):
        real_client_cls = self._get_real_client_cls()

        self.real_client = real_client_cls(test_settings)
        self.httpx_mock = httpx_mock

    @classmethod
    def _get_real_client_cls(cls) -> type[C]:
        geneneric_args = next(
            base_cls.__args__
            for base_cls in cls.__orig_bases__  # type: ignore[attr-defined]
            if base_cls.__origin__ is BaseMockAPIClient
        )

        if not geneneric_args:
            raise TypeError(f"Could not find generic arguments for {cls.__name__}")

        if not len(geneneric_args) == 1:
            raise TypeError(
                f"Expected exactly one generic argument for {cls.__name__}, "
                f"got {len(geneneric_args)}"
            )

        api_client_cls = geneneric_args[0]

        if not issubclass(api_client_cls, BaseAPIClient):
            raise TypeError("Generic argument must be a subclass of BaseAPIClient")

        return api_client_cls

    def common_matchers(self) -> dict[str, Any]:
        return {}

    def add_mock_response(self, method: str, url: str, **kwargs: Any) -> None:
        self.httpx_mock.add_response(
            method=method,
            url=f"{self.real_client.base_url}/{url.removeprefix('/')}",
            **self.common_matchers(),
            **kwargs,
        )

    def simulate_read_timeout(self) -> None:
        self.httpx_mock.add_exception(httpx.ReadTimeout("Unable to read within timeout"))

    def assert_no_api_calls(self) -> None:
        if api_requests := self.httpx_mock.get_requests():
            api_calls_str = textwrap.indent("\n".join(map(str, api_requests)), "  ")

            raise AssertionError(
                f"Expected no API calls, got {len(api_requests)}:\n{api_calls_str}"
            )


class MockOptscaleClient(BaseMockAPIClient[OptscaleClient]):
    def common_matchers(self):
        return {"match_headers": {"Secret": self.real_client.settings.optscale_cluster_secret}}

    def mock_fetch_datasources_for_organization(
        self,
        organization: Organization,
        cloud_account_configs: list[dict[str, Any]] | None = None,
        status_code: int = status.HTTP_200_OK,
    ):
        if organization.linked_organization_id is None:
            raise ValueError("Organization has no linked organization ID")

        def cloud_account_details_factory(config: dict[str, Any]) -> dict[str, Any]:
            return deep_update(
                {
                    "id": str(uuid.uuid4()),
                    "deleted_at": 0,
                    "created_at": 1729683941,
                    "name": "CPA (Development and Test)",
                    "type": "azure_cnr",
                    "organization_id": organization.linked_organization_id,
                    "account_id": str(uuid.uuid4()),
                    "details": {
                        "cost": 123.45,
                        "forecast": 1099.0,
                        "tracked": 2,
                        "last_month_cost": 987.65,
                    },
                },
                config,
            )

        json = None

        if cloud_account_configs is not None:
            json = {
                "cloud_accounts": [
                    cloud_account_details_factory(config) for config in cloud_account_configs
                ]
            }

        self.add_mock_response(
            "GET",
            f"organizations/{organization.linked_organization_id}/cloud_accounts?details=true",
            json=json,
            status_code=status_code,
        )

    def mock_fetch_daily_expenses_for_organization(
        self,
        organization: Organization,
        start_period: int,
        end_period: int,
        expenses: dict[str, Any] | None = None,
        status_code: int = status.HTTP_200_OK,
    ):
        if organization.linked_organization_id is None:
            raise ValueError("Organization has no linked organization ID")

        json = {
            "counts": expenses,
            "breakdown": {
                "1754870400": expenses,
            },
            "start_date": start_period,
            "end_date": end_period,
            "total": 100.0,
            "previous_total": 100.0,
            "previous_range_start": start_period,
            "breakdown_by": "cloud_account_id",
        }

        url = f"organizations/{organization.linked_organization_id}/breakdown_expenses"
        self.add_mock_response(
            "GET",
            f"{url}?start_date={start_period}&end_date={end_period}&breakdown_by=cloud_account_id",
            json=json,
            status_code=status_code,
        )


@pytest.fixture
def mock_optscale_client(test_settings: Settings, httpx_mock: HTTPXMock) -> MockOptscaleClient:
    return MockOptscaleClient(test_settings, httpx_mock)
