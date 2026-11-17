import copy
import functools
from datetime import date, datetime
from typing import Any

from app.enums import TerminationReason
from app.utils import find_first

PARAM_PHASE_ORDERING = "ordering"
PARAM_PHASE_FULFILLMENT = "fulfillment"
PARAM_CONTACT = "contact"

PARAM_DUE_DATE = "dueDate"

PARAM_ORGANIZATION_NAME = "organizationName"
PARAM_CURRENCY = "currency"
PARAM_ADMIN_CONTACT = "adminContact"
PARAM_IS_NEW_USER = "isNewUser"
PARAM_TRIAL_START_DATE = "trialStartDate"
PARAM_TRIAL_END_DATE = "trialEndDate"
PARAM_BILLED_PERCENTAGE = "billedPercentage"
PARAM_TERMINATION_REASON = "terminationReason"
PARAM_TERMINATION_COMMENTS = "terminationComments"


def get_parameter(
    parameter_phase: str, source: dict[str, Any], param_external_id: str
) -> dict[str, Any]:
    """
    Returns a parameter of a given phase by its external identifier.
    Returns an empty dictionary if the parameter is not found.
    Args:
        parameter_phase (str): The phase of the parameter (ordering, fulfillment).
        source : The source business object from which the parameter
        should be extracted.
        param_external_id (str): The unique external identifier of the parameter.

    Returns:
        dict: The parameter object or an empty dictionary if not found.
    """
    return find_first(
        lambda x: x.get("externalId") == param_external_id,
        source["parameters"][parameter_phase],
        default={},
    )


get_ordering_parameter = functools.partial(get_parameter, PARAM_PHASE_ORDERING)

get_fulfillment_parameter = functools.partial(get_parameter, PARAM_PHASE_FULFILLMENT)


def get_ff_date_parameter(parameter_name: str, source: dict[str, Any]) -> date | None:
    parameter = get_fulfillment_parameter(source, parameter_name)

    if parameter.get("value", ""):
        return datetime.strptime(parameter["value"], "%Y-%m-%d").date()

    return None


def set_ordering_parameter_error(
    order: dict[str, Any],
    param_external_id: str,
    error: dict[str, Any],
    required: bool = True,
) -> dict[str, Any]:
    """
    Set a validation error on an ordering parameter.

    Args:
        order (dict): The order that contains the parameter.
        param_external_id (str): The external identifier of the parameter.
        error (dict): The error (id, message) that must be set.

    Returns:
        dict: The order updated.
    """
    updated_order = copy.deepcopy(order)
    param = get_ordering_parameter(
        updated_order,
        param_external_id,
    )
    param["error"] = error
    param["constraints"] = {
        "hidden": False,
        "required": required,
    }
    return updated_order


get_due_date = functools.partial(get_ff_date_parameter, PARAM_DUE_DATE)


def set_due_date(order: dict[str, Any], due_date: date | None) -> dict[str, Any]:
    """
    Set Due Date parameter
    Args:
        order (dict): Order to be updated
        due_date (date|None): due date
    """
    updated_order = copy.deepcopy(order)

    param = get_fulfillment_parameter(updated_order, PARAM_DUE_DATE)
    param["value"] = due_date.strftime("%Y-%m-%d") if due_date else due_date

    return updated_order


def set_is_new_user(order: dict[str, Any], is_new: bool) -> dict[str, Any]:
    """
    Set Is New User parameter
    Args:
        order (dict): Order to be updated
        is_new (bool): due date
    """
    updated_order = copy.deepcopy(order)

    param_value = ["Yes"] if is_new else None
    param = get_fulfillment_parameter(updated_order, PARAM_IS_NEW_USER)
    if param:
        # remove after v5, case when there are processing orders
        # without the parameter is_new_user
        # parameter was introduced after v4 release
        param["value"] = param_value

    return updated_order


def set_fulfillment_parameter(order: dict[str, Any], parameter: str, value: Any) -> dict[str, Any]:
    """
    Set the provided fulfillment parameter with given value
    Args:
        order (dict): Order to be updated
        parameter (str): name of the parameter
        value (Any): value of the parameter
    """
    updated_order = copy.deepcopy(order)

    param = get_fulfillment_parameter(updated_order, parameter)
    param["value"] = value

    return updated_order


def reset_ordering_parameters_error(order: dict[str, Any]) -> dict[str, Any]:
    """
    Reset errors for all ordering parameters

    Args:
        order (dict): The order that contains the parameter.

    Returns:
        dict: The order updated.
    """
    updated_order = copy.deepcopy(order)

    for param in updated_order["parameters"][PARAM_PHASE_ORDERING]:
        param["error"] = None

    return updated_order


get_trial_start_date = functools.partial(get_ff_date_parameter, PARAM_TRIAL_START_DATE)
get_trial_end_date = functools.partial(get_ff_date_parameter, PARAM_TRIAL_END_DATE)


def get_billed_percentage(source: dict[str, Any]) -> dict[str, Any]:
    return get_fulfillment_parameter(source, PARAM_BILLED_PERCENTAGE)


def get_termination_reason(source: dict[str, Any]) -> TerminationReason | None:
    """
    Returns the value of the Termination Reason ordering parameter.

    Args:
        source: The order from which the parameter should be extracted.

    Returns:
        TerminationReason | None: The selected reason, or None if the parameter
        is missing or has no value.

    Raises:
        ValueError: If the value is not a valid TerminationReason key.
    """
    value = get_ordering_parameter(source, PARAM_TERMINATION_REASON).get("value")
    return TerminationReason(value) if value else None


def get_termination_comments(source: dict[str, Any]) -> str | None:
    """
    Returns the value of the Termination Comments (additional comments) ordering parameter.

    Args:
        source: The order from which the parameter should be extracted.

    Returns:
        str | None: The comments stripped of surrounding whitespace, or None if the
        parameter is missing or blank.
    """
    value = get_ordering_parameter(source, PARAM_TERMINATION_COMMENTS).get("value")
    return (value or "").strip() or None
