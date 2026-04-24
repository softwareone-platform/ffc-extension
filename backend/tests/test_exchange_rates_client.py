from unittest.mock import AsyncMock, Mock

import httpx
import pytest

from app.api_clients.exchage_rates import ExchangeRatesClient
from app.billing.exceptions import ExchangeRatesClientError


@pytest.mark.asyncio()
async def test_fetch_exchange_rates_returns_cached_value_without_http_call(test_settings):
    client = ExchangeRatesClient(test_settings)
    client.exchange_rates_cache["USD"] = {"cached": True}
    mock_get = AsyncMock()
    client.httpx_client = AsyncMock()
    client.httpx_client.get = mock_get

    result = await client.fetch_exchange_rates("USD")

    assert result == {"cached": True}
    mock_get.assert_not_called()


@pytest.mark.asyncio()
async def test_fetch_exchange_rates_fetches_and_caches_response(test_settings):
    client = ExchangeRatesClient(test_settings)

    response = Mock()
    response.raise_for_status = Mock()
    response.json = Mock(return_value={"base": "USD", "rates": {"EUR": 0.92}})

    mock_get = AsyncMock(return_value=response)
    client.httpx_client = AsyncMock()
    client.httpx_client.get = mock_get

    result = await client.fetch_exchange_rates("USD")

    assert result == {"base": "USD", "rates": {"EUR": 0.92}}
    client.httpx_client.get.assert_awaited_once_with(
        f"{test_settings.exchange_rates_api_token}/latest/USD"
    )
    response.raise_for_status.assert_called_once()
    assert client.exchange_rates_cache["USD"] == result


@pytest.mark.asyncio()
async def test_fetch_exchange_rates_wraps_request_error(test_settings):
    client = ExchangeRatesClient(test_settings)

    request = httpx.Request("GET", "https://example.test/latest/USD")
    request_error = httpx.RequestError("boom", request=request)
    mock_get = AsyncMock(side_effect=request_error)
    client.httpx_client = AsyncMock()
    client.httpx_client.get = mock_get

    with pytest.raises(ExchangeRatesClientError) as exc_info:
        await client.fetch_exchange_rates("USD")

    assert "Network error while fetching exchange rates for USD: boom" in str(exc_info.value)
