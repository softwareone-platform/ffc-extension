from collections.abc import Callable
from datetime import date

import pytest

from app.parameters import (
    PARAM_BILLED_PERCENTAGE,
    PARAM_CURRENCY,
    PARAM_DUE_DATE,
    PARAM_IS_NEW_USER,
    PARAM_PHASE_FULFILLMENT,
    PARAM_PHASE_ORDERING,
    get_billed_percentage,
    get_due_date,
    get_fulfillment_parameter,
    get_ordering_parameter,
    get_parameter,
    get_trial_end_date,
    get_trial_start_date,
    reset_ordering_parameters_error,
    set_due_date,
    set_fulfillment_parameter,
    set_is_new_user,
    set_ordering_parameter_error,
)

OrderFactory = Callable[[], dict]


def test_get_parameter_returns_matching_parameter(order_with_parameters: OrderFactory) -> None:
    """`get_parameter` returns the parameter whose `externalId` matches in the given phase."""
    order = order_with_parameters()
    param = get_parameter(PARAM_PHASE_ORDERING, order, PARAM_CURRENCY)
    assert param["value"] == "USD"


def test_get_parameter_returns_empty_dict_when_not_found(
    order_with_parameters: OrderFactory,
) -> None:
    """`get_parameter` returns an empty dict when no parameter matches the external id."""
    order = order_with_parameters()
    assert get_parameter(PARAM_PHASE_ORDERING, order, "doesNotExist") == {}


def test_get_ordering_parameter_targets_ordering_phase(
    order_with_parameters: OrderFactory,
) -> None:
    """`get_ordering_parameter` reads from the ordering phase of the order."""
    order = order_with_parameters()
    assert get_ordering_parameter(order, PARAM_CURRENCY)["value"] == "USD"


def test_get_fulfillment_parameter_targets_fulfillment_phase(
    order_with_parameters: OrderFactory,
) -> None:
    """`get_fulfillment_parameter` reads from the fulfillment phase of the order."""
    order = order_with_parameters()
    assert get_fulfillment_parameter(order, PARAM_DUE_DATE)["value"] == "2025-01-01"


def test_get_due_date_parses_iso_date(order_with_parameters: OrderFactory) -> None:
    """`get_due_date` parses the fulfillment due date string into a `date`."""
    order = order_with_parameters()
    assert get_due_date(order) == date(2025, 1, 1)


def test_get_due_date_returns_none_when_value_empty(
    order_with_parameters: OrderFactory,
) -> None:
    """`get_due_date` returns `None` when the due date parameter has no value."""
    order = order_with_parameters()
    order["parameters"][PARAM_PHASE_FULFILLMENT] = [{"externalId": PARAM_DUE_DATE, "value": ""}]
    assert get_due_date(order) is None


def test_get_trial_start_and_end_dates(order_with_parameters: OrderFactory) -> None:
    """`get_trial_start_date`/`get_trial_end_date` parse their fulfillment values."""
    order = order_with_parameters()
    assert get_trial_start_date(order) == date(2025, 1, 1)
    assert get_trial_end_date(order) == date(2025, 1, 31)


def test_get_billed_percentage_returns_parameter(
    order_with_parameters: OrderFactory,
) -> None:
    """`get_billed_percentage` returns the billed percentage fulfillment parameter."""
    order = order_with_parameters()
    assert get_billed_percentage(order)["value"] == "4"


def test_set_ordering_parameter_error_sets_error_and_constraints(
    order_with_parameters: OrderFactory,
) -> None:
    """`set_ordering_parameter_error` sets the error and default constraints on the parameter."""
    order = order_with_parameters()
    error = {"id": "ERR-001", "message": "boom"}
    updated = set_ordering_parameter_error(order, PARAM_CURRENCY, error)
    param = get_ordering_parameter(updated, PARAM_CURRENCY)
    assert param["error"] == error
    assert param["constraints"] == {"hidden": False, "required": True}


def test_set_ordering_parameter_error_does_not_mutate_original(
    order_with_parameters: OrderFactory,
) -> None:
    """`set_ordering_parameter_error` returns a copy, leaving the source order untouched."""
    order = order_with_parameters()
    set_ordering_parameter_error(order, PARAM_CURRENCY, {"id": "ERR", "message": "x"})
    assert "error" not in get_ordering_parameter(order, PARAM_CURRENCY)


def test_set_ordering_parameter_error_respects_required_flag(
    order_with_parameters: OrderFactory,
) -> None:
    """`set_ordering_parameter_error` honours an explicit `required=False`."""
    order = order_with_parameters()
    updated = set_ordering_parameter_error(
        order, PARAM_CURRENCY, {"id": "ERR", "message": "x"}, required=False
    )
    assert get_ordering_parameter(updated, PARAM_CURRENCY)["constraints"]["required"] is False


@pytest.mark.parametrize(
    ("due_date", "expected"),
    [(date(2025, 6, 1), "2025-06-01"), (None, None)],
)
def test_set_due_date_formats_value(
    order_with_parameters: OrderFactory, due_date: date | None, expected: str | None
) -> None:
    """`set_due_date` writes the formatted date string (or `None`) to the due date parameter."""
    order = order_with_parameters()
    updated = set_due_date(order, due_date)
    assert get_fulfillment_parameter(updated, PARAM_DUE_DATE)["value"] == expected


@pytest.mark.parametrize(
    ("is_new", "expected"),
    [(True, ["Yes"]), (False, None)],
)
def test_set_is_new_user_sets_value(
    order_with_parameters: OrderFactory, is_new: bool, expected: list[str] | None
) -> None:
    """`set_is_new_user` sets the `isNewUser` parameter to `['Yes']` or `None`."""
    order = order_with_parameters()
    updated = set_is_new_user(order, is_new)
    assert get_fulfillment_parameter(updated, PARAM_IS_NEW_USER)["value"] == expected


def test_set_is_new_user_noop_when_parameter_absent() -> None:
    """`set_is_new_user` leaves the order unchanged when the parameter is missing."""
    order: dict = {"parameters": {PARAM_PHASE_FULFILLMENT: []}}
    updated = set_is_new_user(order, True)
    assert get_fulfillment_parameter(updated, PARAM_IS_NEW_USER) == {}


def test_set_fulfillment_parameter_sets_value(
    order_with_parameters: OrderFactory,
) -> None:
    """`set_fulfillment_parameter` writes the given value to the named fulfillment parameter."""
    order = order_with_parameters()
    updated = set_fulfillment_parameter(order, PARAM_BILLED_PERCENTAGE, "42")
    assert get_fulfillment_parameter(updated, PARAM_BILLED_PERCENTAGE)["value"] == "42"


def test_reset_ordering_parameters_error_clears_all_errors(
    order_with_parameters: OrderFactory,
) -> None:
    """`reset_ordering_parameters_error` sets every ordering parameter's error to `None`."""
    order = order_with_parameters()
    order = set_ordering_parameter_error(order, PARAM_CURRENCY, {"id": "E", "message": "m"})
    updated = reset_ordering_parameters_error(order)
    assert all(p["error"] is None for p in updated["parameters"][PARAM_PHASE_ORDERING])
