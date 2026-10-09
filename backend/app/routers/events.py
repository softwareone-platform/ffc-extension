import logging

from fastapi import APIRouter

from app.dependencies.core import ExtensionContext
from app.dependencies.events import OrderEventHandler, SubscriptionEventHandler
from app.events.orders.constants import ORDER_TYPE_TERMINATE
from app.events.orders.error import ERR_ORDER_TYPE_NOT_SUPPORTED, ERR_TERMINATION_COMMENTS
from app.events.orders.parameters import check_termination_order_parameters
from app.events.tasks import process_event
from app.parameters import reset_ordering_parameters_error
from app.schemas.core import Event, EventResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/orders/validate")
async def validate_order(order: dict):
    if order["type"] == ORDER_TYPE_TERMINATE:
        order = reset_ordering_parameters_error(order)
        order, is_valid = check_termination_order_parameters(order)
        if not is_valid:
            # this shouldn't be needed
            order["error"] = ERR_TERMINATION_COMMENTS.to_dict()
        return order

    # Webhook of Change Order
    order["error"] = ERR_ORDER_TYPE_NOT_SUPPORTED.to_dict(order_type=order["type"])
    return order


@router.post("/orders")
async def process_order(
    event: Event,
    ext_ctx: ExtensionContext,
    handler: OrderEventHandler,
) -> EventResponse:
    return await process_event(ext_ctx, event, handler)


@router.post("/subscriptions")
async def process_subscription(
    event: Event,
    ext_ctx: ExtensionContext,
    handler: SubscriptionEventHandler,
) -> EventResponse:
    return await process_event(ext_ctx, event, handler)
