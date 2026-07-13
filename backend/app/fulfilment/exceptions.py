from typing import Any


class FulfilmentError(Exception):
    """Base for known, domain-level fulfilment errors.

    Carries the order (when known) so the recovery layer can act on it,
    even though the call that raised never returns a value.
    """

    def __init__(self, message: str = "", *, order: dict[str, Any] | None = None):
        self.order = order
        super().__init__(message)


class OrderMovedToQuery(FulfilmentError):
    """The order was moved to query"""


class OrderNotValidError(FulfilmentError):
    """Order failed validation . (e.g. status != Processing)"""


class OrderProcessingError(FulfilmentError):
    """Wrapper for unexpected errors raised once the order is in hand,
    so the order survives onto the recovery path."""
