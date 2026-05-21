import copy
import logging

from app.api_clients.mpt import MPTClient
from app.order_fulfilment.constants import (
    MPT_ORDER_STATUS_PROCESSING,
    PURCHASE_TEMPLATE_NAME,
)

logger = logging.getLogger(__name__)


def set_template(order, template):
    """Return a copy of the order with the provided template assigned."""
    updated_order = copy.deepcopy(order)
    updated_order["template"] = template
    return updated_order


async def start_processing_order_template(
    ext_client: MPTClient, order: dict, product_id: str
) -> dict:
    """Ensure the order uses the processing template expected for purchase flow."""
    template = await ext_client.get_product_template_or_default(
        product_id=product_id,
        status=MPT_ORDER_STATUS_PROCESSING,
        name=PURCHASE_TEMPLATE_NAME,
    )
    current_template_id = order.get("template", {}).get("id")
    if template["id"] != current_template_id:
        order = set_template(order=order, template=template)
        order = await ext_client.update_order(
            order_id=order["id"],
            template=template,
        )
        logger.info(
            f"{order['id']}: processing template set to {PURCHASE_TEMPLATE_NAME} ({template['id']})"
        )
    logger.info(f"{order['id']}: processing template is ok, continue")
    return order
