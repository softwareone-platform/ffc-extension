from typing import Annotated

from fastapi import Depends

from app.dependencies.api_clients import (
    ExtensionClient,
    FFCAPIClient,
    InstallationClient,
    OptscaleAuthClient,
    OptscaleClient,
)
from app.dependencies.auth import CurrentAuthContext
from app.dependencies.core import AppSettings
from app.dependencies.db import (
    ClientAccountRepository,
    EntitlementRepository,
    OrganizationRepository,
    TerminationFeedbackRepository,
)
from app.events.accounts.processing import (
    ClientAccountEventHandler as _ClientAccountEventHandler,
)
from app.events.orders.processing import OrderEventHandler as _OrderEventHandler
from app.events.subscriptions.processing import (
    SubscriptionEventHandler as _SubscriptionEventHandler,
)


def get_order_event_handler(
    ffc_api_client: FFCAPIClient,
    installation_client: InstallationClient,
    ext_client: ExtensionClient,
    optscale_auth_client: OptscaleAuthClient,
    optscale_client: OptscaleClient,
    organization_repo: OrganizationRepository,
    entitlement_repo: EntitlementRepository,
    termination_feedback_repo: TerminationFeedbackRepository,
    client_account_repo: ClientAccountRepository,
    settings: AppSettings,
) -> _OrderEventHandler:
    return _OrderEventHandler(
        ffc_api_client=ffc_api_client,
        installation_client=installation_client,
        ext_client=ext_client,
        optscale_auth_client=optscale_auth_client,
        optscale_client=optscale_client,
        organization_repo=organization_repo,
        entitlement_repo=entitlement_repo,
        termination_feedback_repo=termination_feedback_repo,
        client_account_repo=client_account_repo,
        settings=settings,
    )


def get_subscription_event_handler(
    installation_client: InstallationClient,
    ext_client: ExtensionClient,
    entitlement_repo: EntitlementRepository,
    auth_context: CurrentAuthContext,
) -> _SubscriptionEventHandler:
    return _SubscriptionEventHandler(
        installation_client=installation_client,
        ext_client=ext_client,
        entitlement_repo=entitlement_repo,
        account=auth_context.account,
    )


def get_client_account_event_handler(
    installation_client: InstallationClient,
    ext_client: ExtensionClient,
    client_account_repo: ClientAccountRepository,
) -> _ClientAccountEventHandler:
    return _ClientAccountEventHandler(
        installation_client=installation_client,
        ext_client=ext_client,
        client_account_repo=client_account_repo,
    )


OrderEventHandler = Annotated[_OrderEventHandler, Depends(get_order_event_handler)]
SubscriptionEventHandler = Annotated[
    _SubscriptionEventHandler, Depends(get_subscription_event_handler)
]
ClientAccountEventHandler = Annotated[
    _ClientAccountEventHandler, Depends(get_client_account_event_handler)
]
