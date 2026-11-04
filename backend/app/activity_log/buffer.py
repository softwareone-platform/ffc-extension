"""Per-transaction accumulation of what will become one ActivityLog row."""

from dataclasses import dataclass, field
from typing import Any

from sqlalchemy.orm import Session

from app.db.models import Base

_KEY = "activity_log_buffer"


@dataclass
class TrackedChange:
    obj: Base
    before: dict[str, Any] | None  # None when the row was created in this transaction


@dataclass
class ExternalCall:
    action_key: str
    message: str


@dataclass
class Explicit:
    action_key: str
    message: str
    actor_id: str | None
    changes: list[TrackedChange]


@dataclass
class TransactionBuffer:
    changes: dict[int, TrackedChange] = field(default_factory=dict)  # keyed by id(obj)
    external: list[ExternalCall] = field(default_factory=list)
    explicit: Explicit | None = None
    # Captured when the first change or external call is buffered: the request's
    # auth context is already reset by the time the session commits.
    actor_id: str | None = None

    def track(self, obj: Base, before: dict[str, Any] | None) -> None:
        # Keep the first before-image seen: later flushes in the same transaction
        # must not overwrite it, or an update would look like a no-op.
        self.changes.setdefault(id(obj), TrackedChange(obj, before))

    def remember_actor(self, actor_id: str | None) -> None:
        if self.actor_id is None and actor_id is not None:
            self.actor_id = actor_id

    def is_empty(self) -> bool:
        return not self.changes and not self.external and self.explicit is None

    def clear(self) -> None:
        self.changes.clear()
        self.external.clear()
        self.explicit = None
        self.actor_id = None


def buffer_for(session: Session) -> TransactionBuffer:
    """The buffer of the (sync) session, created on first use. Lives in session.info."""
    return session.info.setdefault(_KEY, TransactionBuffer())
