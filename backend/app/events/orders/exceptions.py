from app.events.exceptions import EventError
from app.events.processing import ProcessingStatus


class FulfilmentError(EventError):
    """Base for known, domain-level fulfilment errors."""


class OrderMovedToQuery(FulfilmentError):
    """The order was moved to query"""

    status = ProcessingStatus.SKIP
    severity = "Info"


class OrderNotValidError(FulfilmentError):
    """Order failed validation. (e.g. status != Processing)"""

    status = ProcessingStatus.SKIP
    severity = "Info"


class OrderProcessingError(FulfilmentError):
    """Wrapper for unexpected errors raised once the order is in hand,
    so the order survives onto the recovery path."""


class UnsupportedOrderTypeError(FulfilmentError):
    """Order type is not supported"""

    severity = "Warning"
