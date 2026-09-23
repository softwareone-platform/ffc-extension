from app.events.exceptions import EventError
from app.events.processing import ProcessingStatus


class SubscriptionEventError(EventError):
    """
    Base for known, domain-level subscription event errors.

    Nothing in this flow can be retried by the platform, so every known error still
    closes the task; only the severity of the log entry changes.
    """

    status = ProcessingStatus.COMPLETE
    severity = "Error"


class SubscriptionNotFoundError(SubscriptionEventError):
    """The subscription referenced by the event does not exist on the marketplace."""


class SubscriptionNotValidError(SubscriptionEventError):
    """The subscription cannot be processed (e.g. its product is not enabled for the account)."""


class AccountNotEligibleError(SubscriptionEventError):
    """Nothing to sync: the account the event runs under owns no affiliate entitlements."""

    severity = "Info"
