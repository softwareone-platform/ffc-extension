import logging
from datetime import UTC, date, datetime, timedelta
from typing import Any

from app import Settings
from app.fulfilment.error import ERR_ADMIN_CONTACT, ERR_CURRENCY, ERR_ORGANIZATION_NAME
from app.parameters import (
    PARAM_ADMIN_CONTACT,
    PARAM_BILLED_PERCENTAGE,
    PARAM_CURRENCY,
    PARAM_DUE_DATE,
    PARAM_ORGANIZATION_NAME,
    PARAM_TRIAL_END_DATE,
    PARAM_TRIAL_START_DATE,
    get_due_date,
    get_fulfillment_parameter,
    get_ordering_parameter,
    set_ordering_parameter_error,
)

logger = logging.getLogger(__name__)


def get_parameter_updates(order: dict[str, Any], settings: Settings) -> dict[str, Any]:
    """Build default fulfillment parameter values when they are missing in the order."""
    updates = {}
    due_date = get_due_date(order)

    if due_date:
        logger.info(
            f"Due date parameter was setup before {due_date.strftime('%Y-%m-%d')}: skip",
        )
    else:
        due_date = date.today() + timedelta(days=int(settings.due_date_days))
        updates[PARAM_DUE_DATE] = due_date.strftime("%Y-%m-%d")

    if not get_fulfillment_parameter(order, PARAM_BILLED_PERCENTAGE).get("value"):
        updates[PARAM_BILLED_PERCENTAGE] = str(settings.default_billed_percentage)

    trial_start_date = get_fulfillment_parameter(order, PARAM_TRIAL_START_DATE).get("value")
    if not trial_start_date:
        trial_start_date = datetime.now(UTC).date().strftime("%Y-%m-%d")
        updates[PARAM_TRIAL_START_DATE] = trial_start_date

    if not get_fulfillment_parameter(order, PARAM_TRIAL_END_DATE).get("value"):
        trial_end_date = datetime.strptime(trial_start_date, "%Y-%m-%d").date() + timedelta(
            days=int(settings.default_trial_period_duration_days)
        )
        updates[PARAM_TRIAL_END_DATE] = trial_end_date.strftime("%Y-%m-%d")

    return updates


def check_order_parameters(order: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    """
    Check that all required ordering parameters have a value.
    For each missing parameter, attach its error to the order. Returns the
    (possibly annotated) order and a flag indicating whether validation
    succeeded.
    """
    errors = {
        PARAM_ORGANIZATION_NAME: ERR_ORGANIZATION_NAME,
        PARAM_CURRENCY: ERR_CURRENCY,
        PARAM_ADMIN_CONTACT: ERR_ADMIN_CONTACT,
    }
    required = [
        PARAM_ORGANIZATION_NAME,
        PARAM_CURRENCY,
        PARAM_ADMIN_CONTACT,
    ]
    validation_succeeded = True
    for param_name in required:
        parameter = get_ordering_parameter(order, param_name)
        if not parameter.get("value"):
            order = set_ordering_parameter_error(order, param_name, errors[param_name])
            validation_succeeded = False
    return order, validation_succeeded
