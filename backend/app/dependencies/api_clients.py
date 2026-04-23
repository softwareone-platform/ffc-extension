from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends

from app.api_clients import api_modifier, exchage_rates, optscale
from app.api_clients.base import BaseAPIClient
from app.api_clients.mpt import MPTClient, MPTExtensionAuth, get_installation_client
from app.auth.auth import MPTAuthContext
from app.dependencies.core import AppSettings


class APIClientFactory[T: BaseAPIClient]:
    def __init__(self, client_cls: type[T]):
        self.client_cls = client_cls

    async def __call__(self, settings: AppSettings) -> AsyncGenerator[T]:
        client = self.client_cls(settings)
        async with client:
            yield client


APIModifierClient = Annotated[
    api_modifier.APIModifierClient,
    Depends(APIClientFactory(api_modifier.APIModifierClient)),
]
OptscaleClient = Annotated[
    optscale.OptscaleClient,
    Depends(APIClientFactory(optscale.OptscaleClient)),
]
OptscaleAuthClient = Annotated[
    optscale.OptscaleAuthClient,
    Depends(APIClientFactory(optscale.OptscaleAuthClient)),
]

ExchangeRatesClient = Annotated[
    exchage_rates.ExchangeRatesClient,
    Depends(APIClientFactory(exchage_rates.ExchangeRatesClient)),
]


def _get_installation_client(ctx: MPTAuthContext) -> MPTClient:
    return get_installation_client(ctx.account_id)


def _get_extension_client() -> MPTClient:
    return MPTClient(MPTExtensionAuth())


InstallationClient = Annotated[MPTClient, Depends(_get_installation_client)]
ExtensionClient = Annotated[MPTClient, Depends(_get_extension_client)]
