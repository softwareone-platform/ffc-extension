import inspect
import string
from typing import Any

import pytest

from app.activity_log.constants import MASK
from app.activity_log.registry import (
    TRACKED_EXTERNAL_CALLS,
    TRACKED_MODELS,
    UNKNOWN,
    Action,
    ExternalCallActivityTracker,
    tracker_for,
)
from app.api_clients.ffc_api import FFCAPIClient
from app.api_clients.mpt import MPTClient
from app.api_clients.optscale import OptscaleClient
from app.db.models import Account, Entitlement, Organization

CLIENT_CLASSES: dict[str, type] = {
    "FFCAPIClient": FFCAPIClient,
    "MPTClient": MPTClient,
    "OptscaleClient": OptscaleClient,
}


def test_resolve_returns_on_create_without_before_image() -> None:
    """`resolve()` returns the create action when the row did not exist before the transaction."""
    tracker = TRACKED_MODELS[Organization]

    assert tracker.resolve(None, {"status": "active"}) is tracker.on_create


def test_resolve_picks_the_matching_status_transition() -> None:
    """`resolve()` returns the registered action for a from/to status transition."""
    action = TRACKED_MODELS[Entitlement].resolve({"status": "active"}, {"status": "terminated"})

    assert action.key == "entitlement.terminated"


def test_resolve_matches_a_wildcard_source_status() -> None:
    """`resolve()` matches a transition declared with `ANY` whatever the previous status was."""
    action = TRACKED_MODELS[Organization].resolve({"status": "terminated"}, {"status": "deleted"})

    assert action.key == "organization.deleted"


def test_resolve_falls_back_to_on_update_for_unregistered_changes() -> None:
    """`resolve()` returns the update action when no registered transition matches."""
    tracker = TRACKED_MODELS[Organization]

    action = tracker.resolve({"status": "active", "name": "A"}, {"status": "active", "name": "B"})

    assert action is tracker.on_update


def test_resolve_ignores_transitions_whose_attribute_did_not_change() -> None:
    """`resolve()` does not fire a transition whose target status was already the previous one."""
    tracker = TRACKED_MODELS[Entitlement]

    action = tracker.resolve(
        {"status": "terminated", "name": "A"}, {"status": "terminated", "name": "B"}
    )

    assert action is tracker.on_update


@pytest.mark.parametrize(
    ("before", "after", "expected"),
    [
        pytest.param(None, {"name": "A"}, False, id="created"),
        pytest.param(
            {"name": "A", "updated_at": "1"}, {"name": "A", "updated_at": "2"}, True, id="timestamp"
        ),
        pytest.param({"updated_by_id": "X"}, {"updated_by_id": "Y"}, True, id="audit-column"),
        pytest.param(
            {"name": "A", "updated_at": "1"}, {"name": "B", "updated_at": "2"}, False, id="business"
        ),
    ],
)
def test_is_noise_only_for_ignored_columns(
    before: dict[str, Any] | None, after: dict[str, Any], expected: bool
) -> None:
    """`is_noise()` is true only when every changed column is in the tracker's ignore set."""
    assert TRACKED_MODELS[Organization].is_noise(before, after) is expected


def test_action_render_fills_placeholders_from_the_snapshot() -> None:
    """`Action.render()` formats the template with the after-snapshot exposed as `obj`."""
    assert Action("k", "Org {obj.name} ({obj.status})").render(
        {"name": "A", "status": "active"}
    ) == ("Org A (active)")


def test_action_render_tolerates_missing_attributes() -> None:
    """`Action.render()` never fails on a placeholder the snapshot does not contain."""
    assert Action("k", "Org {obj.name}").render({}) == f"Org {UNKNOWN}"


def test_external_tracker_render_masks_arguments() -> None:
    """`ExternalCallActivityTracker.render()` replaces masked arguments with the mask."""
    tracker = ExternalCallActivityTracker(
        "k", "User {email} with {password}", mask=frozenset({"password"})
    )

    assert tracker.render({"email": "a@b.c", "password": "s3cret"}) == f"User a@b.c with {MASK}"


def test_external_tracker_render_tolerates_missing_arguments() -> None:
    """`ExternalCallActivityTracker.render()` tolerates a placeholder the call did not provide."""
    assert ExternalCallActivityTracker("k", "Order {order_id}").render({}) == f"Order {UNKNOWN}"


def test_tracker_for_returns_none_for_untracked_models() -> None:
    """`tracker_for()` returns None for a model absent from the registry."""
    assert tracker_for(Account(name="Untracked", external_id="ACC-1")) is None


def test_tracker_for_finds_the_tracker_of_a_tracked_model() -> None:
    """`tracker_for()` returns the registry entry of the instance's class."""
    tracker = tracker_for(Organization(name="Tracked"))

    assert tracker is TRACKED_MODELS[Organization]


@pytest.mark.parametrize(
    ("name", "tracker"), list(TRACKED_EXTERNAL_CALLS.items()), ids=list(TRACKED_EXTERNAL_CALLS)
)
def test_tracked_external_call_matches_a_client_method(
    name: str, tracker: ExternalCallActivityTracker
) -> None:
    """Every tracked call names an existing client method whose parameters fill its template."""
    class_name, method_name = name.split(".")
    method = getattr(CLIENT_CLASSES[class_name], method_name)
    parameters = set(inspect.signature(method).parameters) - {"self"}
    placeholders = {field for _, field, _, _ in string.Formatter().parse(tracker.message) if field}

    assert inspect.iscoroutinefunction(method)
    assert placeholders <= parameters
    assert tracker.mask <= parameters
