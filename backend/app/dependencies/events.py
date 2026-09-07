from typing import Annotated

from fastapi import Depends

from app.dependencies.api_clients import (
    APIModifierClient,
    ExtensionClient,
    InstallationClient,
    OptscaleAuthClient,
    OptscaleClient,
)
from app.dependencies.auth import CurrentAuthContext
from app.dependencies.core import AppSettings
from app.dependencies.db import EntitlementRepository, OrganizationRepository
from app.events.orders.processing import OrderEventHandler as _OrderEventHandler
from app.events.subscriptions.processing import (
    SubscriptionEventHandler as _SubscriptionEventHandler,
)


def get_order_event_handler(
    api_modifier_client: APIModifierClient,
    client: InstallationClient,
    ext_client: ExtensionClient,
    optscale_auth_client: OptscaleAuthClient,
    optscale_client: OptscaleClient,
    organization_repo: OrganizationRepository,
    entitlement_repo: EntitlementRepository,
    settings: AppSettings,
) -> _OrderEventHandler:
    return _OrderEventHandler(
        api_modifier_client=api_modifier_client,
        client=client,
        ext_client=ext_client,
        optscale_auth_client=optscale_auth_client,
        optscale_client=optscale_client,
        organization_repo=organization_repo,
        entitlement_repo=entitlement_repo,
        settings=settings,
    )


def get_subscription_event_handler(
    client: InstallationClient,
    ext_client: ExtensionClient,
    entitlement_repo: EntitlementRepository,
    auth_context: CurrentAuthContext,
) -> _SubscriptionEventHandler:
    return _SubscriptionEventHandler(
        client=client,
        ext_client=ext_client,
        entitlement_repo=entitlement_repo,
        account=auth_context.account,
    )


OrderEventHandler = Annotated[_OrderEventHandler, Depends(get_order_event_handler)]
SubscriptionEventHandler = Annotated[
    _SubscriptionEventHandler, Depends(get_subscription_event_handler)
]
