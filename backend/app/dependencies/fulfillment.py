from typing import Annotated

from fastapi import Depends

from app.dependencies.api_clients import (
    APIModifierClient,
    ExtensionClient,
    InstallationClient,
    OptscaleAuthClient,
    OptscaleClient,
)
from app.dependencies.core import AppSettings
from app.dependencies.db import OrganizationRepository
from app.fulfilment.processing import OrderProcessorFactory


def get_order_processor_factory(
    api_modifier_client: APIModifierClient,
    client: InstallationClient,
    ext_client: ExtensionClient,
    optscale_auth_client: OptscaleAuthClient,
    optscale_client: OptscaleClient,
    organization_repo: OrganizationRepository,
    settings: AppSettings,
) -> OrderProcessorFactory:
    return OrderProcessorFactory(
        api_modifier_client=api_modifier_client,
        client=client,
        ext_client=ext_client,
        optscale_auth_client=optscale_auth_client,
        optscale_client=optscale_client,
        organization_repo=organization_repo,
        settings=settings,
    )


OrderProcessorFactoryDep = Annotated[OrderProcessorFactory, Depends(get_order_processor_factory)]
