"""Declarative description of which models and client calls are tracked.

Adding a new tracked model, a new action key or a new external call is an edit
here plus a test. Business code is never touched.
"""

from dataclasses import dataclass, field
from types import SimpleNamespace
from typing import Any

from app.activity_log.constants import MASK
from app.db.models import Base, ClientAccount, Entitlement, Organization, System
from app.enums import EntitlementStatus, OrganizationStatus, SystemStatus

ANY = object()  # wildcard for the "from" side of a transition

UNKNOWN = "<unknown>"  # rendered for a template placeholder the snapshot or call cannot provide


class _Namespace(SimpleNamespace):
    def __getattr__(self, name: str) -> Any:
        return UNKNOWN


class _Arguments(dict[str, Any]):
    def __missing__(self, key: str) -> str:
        return UNKNOWN


@dataclass(frozen=True)
class Action:
    key: str
    message: str  # str.format template; `obj` is a namespace over the after-snapshot

    def render(self, after: dict[str, Any]) -> str:
        """This is for database changes. `after` is the snapshot dict of the row
        for example {"id":"FORG-1", "name": "Acme", "status": "ACTIVE"}.
        """
        return self.message.format(obj=_Namespace(**after))


@dataclass(frozen=True)
class ModelActivityTracker:
    object_type: str
    on_create: Action
    on_update: Action
    # (attribute, from, to) -> Action. `from` may be ANY. Checked in declaration order.
    transitions: dict[tuple[str, Any, Any], Action] = field(default_factory=dict)
    # Changing only these columns does not produce an entry (timestamps, audit columns).
    ignore: frozenset[str] = frozenset({"created_at", "updated_at", "updated_by_id"})

    def resolve(self, before: dict[str, Any] | None, after: dict[str, Any]) -> Action:
        if before is None:
            # the obj is new
            return self.on_create
        for (attr, old, new), action in self.transitions.items():
            if before.get(attr) == after.get(attr):
                # skip because the attribute did not change
                continue
            if after.get(attr) == new and (old is ANY or before.get(attr) == old):
                return action
        return self.on_update

    def is_noise(self, before: dict[str, Any] | None, after: dict[str, Any]) -> bool:
        """True when every changed column is in `ignore`."""
        if before is None:
            return False
        changed = {k for k in after if before.get(k) != after.get(k)}
        return changed <= self.ignore


TRACKED_MODELS: dict[type[Base], ModelActivityTracker] = {
    Organization: ModelActivityTracker(
        object_type="organization",
        on_create=Action("organization.created", "Organization {obj.name} created"),
        on_update=Action("organization.updated", "Organization {obj.name} updated"),
        transitions={
            ("status", OrganizationStatus.ACTIVE, OrganizationStatus.TERMINATED): Action(
                "organization.terminated", "Organization {obj.name} terminated"
            ),
            ("status", ANY, OrganizationStatus.DELETED): Action(
                "organization.deleted", "Organization {obj.name} deleted"
            ),
        },
    ),
    Entitlement: ModelActivityTracker(
        object_type="entitlement",
        on_create=Action("entitlement.created", "Entitlement {obj.name} created"),
        on_update=Action("entitlement.updated", "Entitlement {obj.name} updated"),
        transitions={
            ("status", EntitlementStatus.NEW, EntitlementStatus.ACTIVE): Action(
                "entitlement.redeemed",
                "Entitlement {obj.name} redeemed by organization {obj.redeemed_by_id}",
            ),
            ("status", EntitlementStatus.ACTIVE, EntitlementStatus.TERMINATED): Action(
                "entitlement.terminated", "Entitlement {obj.name} terminated"
            ),
            ("status", ANY, EntitlementStatus.DELETED): Action(
                "entitlement.deleted", "Entitlement {obj.name} deleted"
            ),
        },
    ),
    ClientAccount: ModelActivityTracker(
        object_type="client_account",
        on_create=Action("client_account.created", "Client account {obj.name} created"),
        on_update=Action("client_account.updated", "Client account {obj.name} updated"),
    ),
    System: ModelActivityTracker(
        object_type="system",
        on_create=Action("system.created", "System {obj.name} created"),
        on_update=Action("system.updated", "System {obj.name} updated"),
        transitions={
            ("status", SystemStatus.ACTIVE, SystemStatus.DISABLED): Action(
                "system.disabled", "System {obj.name} disabled"
            ),
            ("status", ANY, SystemStatus.DELETED): Action(
                "system.deleted", "System {obj.name} deleted"
            ),
        },
    ),
}


def tracker_for(obj: object) -> ModelActivityTracker | None:
    """The tracker registered for the class of `obj` or for one of its bases."""
    for cls in type(obj).__mro__:
        tracker = TRACKED_MODELS.get(cls)
        if tracker is not None:
            return tracker
    return None


@dataclass(frozen=True)
class ExternalCallActivityTracker:
    key: str
    message: str  # str.format template over the bound call arguments
    mask: frozenset[str] = frozenset()  # argument names never rendered into the message

    def render(self, arguments: dict[str, Any]) -> str:
        safe = _Arguments({k: (MASK if k in self.mask else v) for k, v in arguments.items()})
        return self.message.format_map(safe)


# Keyed by "<ClassName>.<method>". Only methods listed here are recorded.
# Read-only methods (get_*, fetch_*) are deliberately absent.
TRACKED_EXTERNAL_CALLS: dict[str, ExternalCallActivityTracker] = {
    "FFCAPIClient.create_organization": ExternalCallActivityTracker(
        "optscale.organization.created",
        "Organization {org_name} created on FinOps for Cloud",
    ),
    "FFCAPIClient.create_user": ExternalCallActivityTracker(
        "optscale.user.created",
        "User {email} created on FinOps for Cloud",
        mask=frozenset({"password"}),
    ),
    "FFCAPIClient.create_tag_for_datasource": ExternalCallActivityTracker(
        "optscale.tag.created", "Tag created for datasource {datasource_id}"
    ),
    "FFCAPIClient.delete_tag": ExternalCallActivityTracker(
        "optscale.tag.deleted", "Tag {id} deleted on FinOps for Cloud"
    ),
    "OptscaleClient.delete_organization": ExternalCallActivityTracker(
        "optscale.organization.deleted",
        "Organization {organization_id} deleted on FinOps for Cloud",
    ),
    "MPTClient.update_agreement": ExternalCallActivityTracker(
        "mpt.agreement.updated", "Agreement {agreement_id} updated on MPT"
    ),
    "MPTClient.complete_order": ExternalCallActivityTracker(
        "mpt.order.completed", "Order {order_id} completed on MPT"
    ),
    "MPTClient.fail_order": ExternalCallActivityTracker(
        "mpt.order.failed", "Order {order_id} failed on MPT"
    ),
    "MPTClient.create_subscription": ExternalCallActivityTracker(
        "mpt.subscription.created", "Subscription created for order {order_id} on MPT"
    ),
}
