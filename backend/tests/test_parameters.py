import copy

from app.parameters import (
    PARAM_PHASE_FULFILLMENT,
    PARAM_PHASE_ORDERING,
    reset_ordering_parameters_error,
)


def _order_with_ordering_errors(order_factory):
    order = order_factory(
        order_type="Purchase",
        status="Processing",
        product_id="PRD-4141-4379",
        product_name="SoftwareOne FinOps for Cloud",
    )
    for param in order["parameters"][PARAM_PHASE_ORDERING]:
        param["error"] = {"id": "VAL-001", "message": f"{param['externalId']} is invalid"}
    return order


def test_reset_ordering_parameters_error_clears_all_errors(order_factory):
    order = _order_with_ordering_errors(order_factory)

    updated_order = reset_ordering_parameters_error(order)

    assert all(
        param["error"] is None for param in updated_order["parameters"][PARAM_PHASE_ORDERING]
    )


def test_reset_ordering_parameters_error_returns_new_order(order_factory):
    order = _order_with_ordering_errors(order_factory)

    updated_order = reset_ordering_parameters_error(order)

    assert updated_order is not None
    assert updated_order is not order


def test_reset_ordering_parameters_error_does_not_mutate_input(order_factory):
    order = _order_with_ordering_errors(order_factory)
    original = copy.deepcopy(order)

    reset_ordering_parameters_error(order)

    assert order == original
    assert all(param["error"] is not None for param in order["parameters"][PARAM_PHASE_ORDERING])


def test_reset_ordering_parameters_error_leaves_fulfillment_untouched(order_factory):
    order = _order_with_ordering_errors(order_factory)
    for param in order["parameters"][PARAM_PHASE_FULFILLMENT]:
        param["error"] = {"id": "VAL-002", "message": "fulfillment error"}

    updated_order = reset_ordering_parameters_error(order)

    assert all(
        param["error"] is not None for param in updated_order["parameters"][PARAM_PHASE_FULFILLMENT]
    )


def test_reset_ordering_parameters_error_empty_ordering_list(order_factory):
    order = order_factory(
        order_type="Purchase",
        status="Processing",
        product_id="PRD-4141-4379",
        product_name="SoftwareOne FinOps for Cloud",
    )
    order["parameters"][PARAM_PHASE_ORDERING] = []

    updated_order = reset_ordering_parameters_error(order)

    assert updated_order["parameters"][PARAM_PHASE_ORDERING] == []


def test_reset_ordering_parameters_error_params_without_error_key(order_factory):
    order = order_factory(
        order_type="Purchase",
        status="Processing",
        product_id="PRD-4141-4379",
        product_name="SoftwareOne FinOps for Cloud",
    )
    assert all("error" not in param for param in order["parameters"][PARAM_PHASE_ORDERING])

    updated_order = reset_ordering_parameters_error(order)

    assert all(
        param["error"] is None for param in updated_order["parameters"][PARAM_PHASE_ORDERING]
    )
