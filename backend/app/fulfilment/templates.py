import copy
import logging

from app.api_clients.mpt import MPTClient
from app.conf import get_settings
from app.fulfilment.constants import PURCHASE_TEMPLATE_NAME

logger = logging.getLogger(__name__)
template_cache: dict[tuple[str, str | None], str] = {}


def set_template(order: dict, template_id: str) -> dict:
    """Return a copy of the order with the provided template assigned."""
    if not template_id:
        raise ValueError("Template id is required")
    updated_order = copy.deepcopy(order)
    try:
        updated_order["template"]["id"] = template_id
        return updated_order
    except KeyError:
        raise KeyError("Order is malformed")


async def get_product_template_id(
    ext_client: MPTClient, template_type: str, template_name: str
) -> str:
    settings = get_settings()
    product_id = settings.mpt_product_id
    if not template_cache:
        logger.info("Initializing template cache for product %s", product_id)
        await fetch_product_templates(ext_client, product_id)
        logger.info("Template cache initialized with %d entries", len(template_cache))
    logger.info("------ Fetching template %s", template_name)
    return template_cache.get((template_type, template_name), template_cache[(template_type, None)])


async def fetch_product_templates(ext_client: MPTClient, product_id: str) -> None:
    async for template in ext_client.get_templates_by_product_id(product_id=product_id):
        template_id = template["id"]
        template_type = template["type"]
        template_name = template["name"] if not template["default"] else None
        template_cache[(template_type, template_name)] = template_id
        logger.debug("Cached template %s (%s, %s)", template_id, template_type, template_name)


async def start_processing_order_template(ext_client: MPTClient, order: dict) -> dict:
    """Ensure the order uses the processing template expected for purchase flow."""
    template_id = await get_product_template_id(
        ext_client, "OrderProcessing", PURCHASE_TEMPLATE_NAME
    )
    logger.info("Processing order template: %s", template_id)
    current_template_id = order.get("template", {}).get("id")
    if template_id != current_template_id:
        order = set_template(order=order, template_id=template_id)
        order = await ext_client.update_order(
            order_id=order["id"],
            template={"id": template_id},
        )
        logger.info(
            "%s: processing template set to %s (%s)",
            order["id"],
            PURCHASE_TEMPLATE_NAME,
            template_id,
        )

    logger.info("%s: processing template is ok, continue", order["id"])
    return order
