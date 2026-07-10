import logging

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
