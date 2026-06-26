import httpx
import pytest
from pytest_httpx import HTTPXMock
from pytest_mock import MockerFixture

from app.api_clients.exchage_rates import ExchangeRatesClient
from app.billing.exceptions import ExchangeRatesClientError
from app.conf import Settings


async def test_fetch_exchange_rates_returns_from_cache(
    test_settings: Settings, mocker: MockerFixture
) -> None:
    client = ExchangeRatesClient(test_settings)
    client.exchange_rates_cache["USD"] = {"base": "USD", "rates": {"EUR": 0.92}}
    mock_get = mocker.spy(client.httpx_client, "get")

    result = await client.fetch_exchange_rates("USD")

    assert result == {"base": "USD", "rates": {"EUR": 0.92}}
    mock_get.assert_not_awaited()


@pytest.mark.parametrize(
    "currency",
    ["USD", "usd", "uSd"],
)
async def test_fetch_exchange_rates_fetches_and_caches_response(
    test_settings: Settings,
    httpx_mock: HTTPXMock,
    currency: str,
) -> None:
    client = ExchangeRatesClient(test_settings)
    payload = {"base": currency.upper(), "rates": {"EUR": 0.92}}
    httpx_mock.add_response(
        method="GET",
        url=(
            f"{test_settings.exchange_rates_base_url}/"
            f"{test_settings.exchange_rates_api_token}/latest/{currency.upper()}"
        ),
        json=payload,
    )
    assert "USD" not in client.exchange_rates_cache
    result = await client.fetch_exchange_rates(currency.upper())

    assert result == payload
    assert client.exchange_rates_cache[currency.upper()] == payload


async def test_fetch_exchange_rates_wraps_request_error(
    test_settings: Settings, httpx_mock: HTTPXMock
) -> None:
    client = ExchangeRatesClient(test_settings)
    httpx_mock.add_exception(httpx.RequestError("boom"))

    with pytest.raises(ExchangeRatesClientError) as exc_info:
        await client.fetch_exchange_rates("USD")

    assert "Network error while fetching exchange rates for USD: boom" in str(exc_info.value)
    assert "USD" not in client.exchange_rates_cache


async def test_fetch_exchange_rates_propagates_http_status_error(
    test_settings: Settings, httpx_mock: HTTPXMock
) -> None:
    client = ExchangeRatesClient(test_settings)
    httpx_mock.add_response(status_code=500)

    with pytest.raises(httpx.HTTPStatusError):
        await client.fetch_exchange_rates("USD")

    assert "USD" not in client.exchange_rates_cache
