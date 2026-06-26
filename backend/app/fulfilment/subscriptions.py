import logging

from app.api_clients.mpt import MPTClient
from app.db.models import Organization
from app.utils import find_first

logger = logging.getLogger(__name__)


def get_subscription_by_line_and_item_id(
    subscriptions: list, item_id: str, line_id: str
) -> dict | None:
    """
    Return a subscription by line id and sku.
    Args:
        subscriptions (list): a list of subscription objects.
        item_id (str): the item SKU
        line_id (str): the id of the order line that should contain the given SKU.


    Returns:
        dict: the corresponding subscription if it is found, None otherwise.
    """
    for subscription in subscriptions:
        item = find_first(
            lambda x: x["id"] == line_id and x["item"]["id"] == item_id,
            subscription["lines"],
        )

        if item:
            return subscription
    return None


async def create_order_subscription(ext_client: MPTClient, order: dict, organization: Organization):
    """Create missing subscriptions for each order line and bind them to the organization."""
    for line in order["lines"]:
        order_subscription = get_subscription_by_line_and_item_id(
            order["subscriptions"],
            line["item"]["id"],
            line["id"],
        )
        if not order_subscription:
            subscription = {
                "name": f"Subscription for {line['item']['name']}",
                "parameters": {},
                "externalIds": {"vendor": organization.id},
                "lines": [
                    {
                        "id": line["id"],
                    },
                ],
            }
            subscription = await ext_client.create_subscription(
                order_id=order["id"],
                subscription=subscription,
            )
            logger.info(
                "%s: subscription %s (%s) created", order["id"], line["id"], subscription["id"]
            )
