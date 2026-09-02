import logging
from typing import Any

from app.api_clients.mpt import MPTClient
from app.db.models import Account, Entitlement
from app.dependencies.db import EntitlementRepository
from app.enums import AccountType, EntitlementStatus
from app.events.core import EventHandler, EventProcessor
from app.events.processing import ProcessingResult, ProcessingStatus
from app.events.subscriptions.constants import (
    ACTIVE_SUBSCRIPTION_STATUS,
    TERMINATED_SUBSCRIPTION_STATUS,
)
from app.events.subscriptions.exceptions import (
    AccountNotEligibleError,
    SubscriptionNotFoundError,
    SubscriptionNotValidError,
)
from app.events.subscriptions.utils import get_datasource_id, is_product_supported

logger = logging.getLogger(__name__)


class SubscriptionProcessor(EventProcessor):
    """Keep the affiliate entitlements in sync with the marketplace subscriptions."""

    object_type = "subscription"

    def __init__(
        self,
        entitlement_repo: EntitlementRepository,
        account: Account,
        subscription: dict[str, Any],
    ):
        self.entitlement_repo = entitlement_repo
        self.account = account
        self.subscription = subscription

    @property
    def object_id(self) -> str:
        return self.subscription["id"]

    def validate_account(self) -> None:
        """Only affiliate accounts own entitlements: anything else has nothing to sync."""
        if self.account.type != AccountType.AFFILIATE:
            raise AccountNotEligibleError(
                f"The account {self.account.id} is not an affiliate account."
            )

    def validate_product(self) -> None:
        if not is_product_supported(self.subscription, self.account):
            raise SubscriptionNotValidError(
                f"The product {self.subscription['product']['id']} is not enabled for the "
                f"account {self.account.id}."
            )

    async def validate(self) -> None:
        self.validate_account()
        self.validate_product()

    async def get_entitlement(self) -> Entitlement | None:
        """Return the entitlement the subscription is bound to, by datasource id."""
        return await self.entitlement_repo.first(
            where_clauses=[
                Entitlement.owner == self.account,
                Entitlement.datasource_id == get_datasource_id(self.subscription),
                Entitlement.status.in_([EntitlementStatus.NEW, EntitlementStatus.ACTIVE]),
            ],
        )

    def completed(self, message: str, severity: str = "Info") -> ProcessingResult:
        """Log what was done to the entitlement and close the task."""

        logger.info("%s: %s", self.object_id, message)
        return ProcessingResult(
            status=ProcessingStatus.COMPLETE, severity=severity, message=message
        )

    async def handle_active(self, entitlement: Entitlement | None) -> ProcessingResult:
        """Issue an entitlement unless a live one already covers the subscription."""

        if entitlement is not None:
            return self.completed(f"The entitlement {entitlement.id} already exists.")

        entitlement = await self.entitlement_repo.create(
            Entitlement(
                name=self.subscription["name"],
                affiliate_external_id=self.subscription["id"],
                datasource_id=get_datasource_id(self.subscription),
                status=EntitlementStatus.NEW,
                owner=self.account,
            )
        )
        return self.completed(f"The entitlement {entitlement.id} was created.")

    async def handle_terminated(self, entitlement: Entitlement | None) -> ProcessingResult:
        """Drop an entitlement that was never redeemed, terminate the one in use."""
        if entitlement is None:
            return self.completed(f"No entitlement is bound to the subscription {self.object_id}.")

        if entitlement.status == EntitlementStatus.NEW:
            await self.entitlement_repo.delete(entitlement)
            return self.completed(f"The entitlement {entitlement.id} was deleted.")
        else:
            await self.entitlement_repo.terminate(entitlement)
            return self.completed(f"The entitlement {entitlement.id} was terminated.")

    async def handle(self) -> ProcessingResult:
        entitlement = await self.get_entitlement()
        if self.subscription["status"] == ACTIVE_SUBSCRIPTION_STATUS:
            return await self.handle_active(entitlement)
        elif self.subscription["status"] == TERMINATED_SUBSCRIPTION_STATUS:
            return await self.handle_terminated(entitlement)
        else:
            return self.completed(
                f"The subscription status {self.subscription['status']} is not handled.",
                severity="Warning",
            )


class SubscriptionEventHandler(EventHandler):
    def __init__(
        self,
        client: MPTClient,
        ext_client: MPTClient,
        entitlement_repo: EntitlementRepository,
        account: Account,
    ):
        self.client = client
        self.ext_client = ext_client
        self.entitlement_repo = entitlement_repo
        self.account = account

    async def get_processor(self, object_id: str) -> SubscriptionProcessor:
        subscription = await self.client.get_subscription(object_id)
        if not subscription:
            raise SubscriptionNotFoundError(f"No subscription found for {object_id}.")
        return SubscriptionProcessor(
            entitlement_repo=self.entitlement_repo,
            account=self.account,
            subscription=subscription,
        )
