from typing import Any

import httpx

from app.api_clients.base import BaseAPIClient
from app.billing.exceptions import ExchangeRatesClientError


class ExchangeRatesClient(BaseAPIClient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.exchange_rates_cache: dict[str, dict[str, Any]] = {}

    @property
    def base_url(self):
        return self.settings.exchange_rates_base_url

    @property
    def auth(self):
        return None

    async def fetch_exchange_rates(self, currency: str) -> dict[str, Any]:
        currency = currency.upper()
        cached_value = self.exchange_rates_cache.get(currency)
        if cached_value is not None:
            return cached_value
        try:
            response = await self.httpx_client.get(
                f"{self.settings.exchange_rates_api_token}/latest/{currency}"
            )
            response.raise_for_status()
        except httpx.RequestError as e:
            raise ExchangeRatesClientError(
                f"Network error while fetching exchange rates for {currency}: {e}"
            ) from e
        exchange_rates = response.json()
        self.exchange_rates_cache[currency] = exchange_rates
        return exchange_rates
