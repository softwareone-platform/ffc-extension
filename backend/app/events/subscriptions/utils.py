import logging
from typing import Any

from app.api_clients.mpt import MPTClient
from app.db.models import Account
from app.events.subscriptions.constants import (
    EXPIRED_SUBSCRIPTION_STATUS,
    TERMINATED_SUBSCRIPTION_STATUS,
)

logger = logging.getLogger(__name__)


def get_datasource_id(subscription: dict[str, Any]) -> str | None:
    """Return the vendor external id of a subscription, which is the FinOps datasource id."""
    return subscription.get("externalIds", {}).get("vendor")


def is_product_supported(subscription: dict[str, Any], account: Account) -> bool:
    """Check that the subscription's product is accessible to account."""
    products = {
        product.strip().lower()
        for product in (account.products or "").split(",")
        if product.strip()
    }
    return subscription["product"]["id"].lower() in products


async def get_live_subscription(
    client: MPTClient,
    account: Account,
    datasource_id: str,
) -> dict[str, Any] | None:
    """
    Return a marketplace subscription for the datasource that has not ended, if any.

    A subscription can be replaced by a new one for the same datasource (e.g. split billing or
    a change of client, buyer or licensee): the entitlement must follow the live one instead
    of being terminated with the old one.
    """
    query = (
        "and("
        f"eq(externalIds.vendor,{datasource_id}),"
        f"out(status,({TERMINATED_SUBSCRIPTION_STATUS},{EXPIRED_SUBSCRIPTION_STATUS})),"
        f"in(product.id,({account.products}))"
        ")"
    )
    return await client.get_first(
        "commerce/subscriptions",
        query=query,
        select=["id", "name", "status", "externalIds"],
    )
