import textwrap
import uuid
from typing import Any, Protocol, TypeVar

import httpx
import pytest
from fastapi import status
from pydantic.v1.utils import deep_update
from pytest_httpx import HTTPXMock

from app.api_clients.base import BaseAPIClient
from app.api_clients.mpt import MPTClient, MPTExtensionAuth
from app.api_clients.optscale import OptscaleClient
from app.conf import Settings
from app.db.models import Organization

# Unbounded: most real clients subclass BaseAPIClient, but some (e.g. MPTClient) don't.
# The default _build_real_client still enforces the BaseAPIClient contract at runtime.
C = TypeVar("C")


class BaseMockAPIClient(Protocol[C]):
    real_client: C
    httpx_mock: HTTPXMock

    def __init__(self, test_settings: Settings, httpx_mock: HTTPXMock):
        self.real_client = self._build_real_client(test_settings)
        self.httpx_mock = httpx_mock

    def _build_real_client(self, test_settings: Settings) -> C:
        """Construct the real client under test.

        Default works for ``BaseAPIClient`` subclasses (``cls(settings)``); override
        for clients whose constructor differs (e.g. ``MPTClient(auth=...)``).
        """
        return self._get_real_client_cls()(test_settings)

    @property
    def base_url(self) -> str:
        """Base URL the real client issues requests against, for mock matching."""
        return self.real_client.base_url

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
            url=f"{self.base_url}/{url.removeprefix('/')}",
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


class MockExtensionClient(BaseMockAPIClient[MPTClient]):
    """HTTP-level mock for the MPT extension client (``MPTClient``).

    Mirrors ``MockOptscaleClient``: it wraps a *real* ``MPTClient`` and stubs the HTTP
    responses for its endpoints via ``httpx_mock``. Tests therefore exercise the real
    client (URL building, pagination, parsing) while the network is mocked. Stub data
    (orders, templates, ...) is passed to the ``mock_*`` helpers rather than stored on
    the client, and any endpoint without a dedicated helper can be stubbed directly
    with the inherited ``add_mock_response``.
    """

    def _build_real_client(self, test_settings: Settings) -> MPTClient:
        client = MPTClient(auth=MPTExtensionAuth())
        # Pin settings so base_url / page size match what the mock registers below.
        client.settings = test_settings
        return client

    @property
    def base_url(self) -> str:
        return self.real_client.settings.mpt_api_base_url

    # ---- Orders ------------------------------------------------------

    def mock_get_order(self, order: dict, *, status_code: int = status.HTTP_200_OK) -> None:
        self.add_mock_response(
            "GET", f"commerce/orders/{order['id']}", json=order, status_code=status_code
        )

    def mock_update_order(
        self, order_id: str, order: dict, *, status_code: int = status.HTTP_200_OK
    ) -> None:
        self.add_mock_response(
            "PUT", f"commerce/orders/{order_id}", json=order, status_code=status_code
        )

    def mock_complete_order(
        self, order_id: str, order: dict, *, status_code: int = status.HTTP_200_OK
    ) -> None:
        self.add_mock_response(
            "POST", f"commerce/orders/{order_id}/complete", json=order, status_code=status_code
        )

    # ---- Templates ---------------------------------------------------

    def mock_get_product_templates(
        self, product_id: str, templates: list[dict], *, status_code: int = status.HTTP_200_OK
    ) -> None:
        rows = self.real_client.settings.mpt_api_rows_per_page
        self.add_mock_response(
            "GET",
            f"catalog/products/{product_id}/templates?limit={rows}&offset=0",
            json={"data": templates, "$meta": {"pagination": {"total": len(templates)}}},
            status_code=status_code,
        )

    # ---- Agreements --------------------------------------------------

    def mock_get_agreement(self, agreement: dict, *, status_code: int = status.HTTP_200_OK) -> None:
        self.add_mock_response(
            "GET",
            f"commerce/agreements/{agreement['id']}",
            json=agreement,
            status_code=status_code,
        )


@pytest.fixture
def mock_extension_client(test_settings: Settings, httpx_mock: HTTPXMock) -> MockExtensionClient:
    return MockExtensionClient(test_settings, httpx_mock)


@pytest.fixture
def mock_optscale_client(test_settings: Settings, httpx_mock: HTTPXMock) -> MockOptscaleClient:
    return MockOptscaleClient(test_settings, httpx_mock)
