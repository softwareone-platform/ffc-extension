import logging
from typing import Any

from app.db.models import Account

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
