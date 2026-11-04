"""The single primitive that turns buffered changes into ActivityLog rows.

Everything else (listeners, external instrumentation, explicit calls) ends here.
"""

from typing import Any

from sqlalchemy.orm.attributes import instance_state

from app.activity_log.buffer import (
    Explicit,
    ExternalCall,
    TrackedChange,
    TransactionBuffer,
    buffer_for,
)
from app.activity_log.constants import APP_ACTOR_ID
from app.activity_log.context import current_session, resolve_actor_id
from app.activity_log.registry import Action, tracker_for
from app.activity_log.snapshot import snapshot
from app.db.models import ActivityLog, Base, ChangeRecord


def _object_type(obj: Base) -> str:
    tracker = tracker_for(obj)
    return tracker.object_type if tracker else obj.__tablename__


def _object_id(obj: Base) -> str:
    identity = instance_state(obj).identity
    return str(identity[0]) if identity else str(obj.id)


def _join(message: str, external: list[ExternalCall]) -> str:
    return "; ".join([message, *(call.message for call in external)])


def _resolve_action(meaningful: list[tuple[TrackedChange, dict[str, Any]]]) -> Action:
    """Most specific registered action across the changed objects.

    A registered transition beats on_create, which beats on_update. Ties go to the
    order in which the objects were first tracked. Only registered models reach
    this point: the listener never tracks anything outside TRACKED_MODELS.
    """
    best: Action | None = None
    best_rank = -1
    for change, after in meaningful:
        tracker = tracker_for(change.obj)
        assert tracker is not None  # noqa: S101 - listener only tracks registered models
        action = tracker.resolve(change.before, after)
        rank = 1 if action is tracker.on_update else 2 if action is tracker.on_create else 3
        if rank > best_rank:
            best, best_rank = action, rank
    assert best is not None  # noqa: S101 - meaningful is never empty here
    return best


def build_entry(buffer: TransactionBuffer) -> ActivityLog | None:
    """Build one ActivityLog from the buffer, or None if nothing worth recording.

    Called from before_commit by the listener, after a flush, so every tracked
    object already has its generated values. The returned entry is not yet added
    to the session.
    """
    # Drop pure-noise updates (only ignored columns changed) before deciding.
    meaningful: list[tuple[TrackedChange, dict[str, Any]]] = []
    for change in buffer.changes.values():
        after = snapshot(change.obj)
        tracker = tracker_for(change.obj)
        if tracker and tracker.is_noise(change.before, after):
            continue
        meaningful.append((change, after))

    explicit_actor: str | None = None
    if buffer.explicit is not None:
        explicit = buffer.explicit
        action_key, message = explicit.action_key, explicit.message
        explicit_actor = explicit.actor_id
        # Explicit changes first, then any automatic ones not already covered.
        seen = {(_object_type(c.obj), _object_id(c.obj)) for c in explicit.changes}
        extra = [
            (c, a) for c, a in meaningful if (_object_type(c.obj), _object_id(c.obj)) not in seen
        ]
        records = [(c, snapshot(c.obj)) for c in explicit.changes] + extra
    elif meaningful:
        # The DB change names the activity. External calls made in the same
        # transaction are appended to the message so they are not lost.
        action = _resolve_action(meaningful)
        action_key = action.key
        message = _join(action.render(meaningful[0][1]), buffer.external)
        records = meaningful
    elif buffer.external:
        # External-only transaction: one entry, no change records. The first call
        # names the activity, the others are appended to the message.
        first, *rest = buffer.external
        action_key = first.action_key
        message = _join(first.message, rest)
        records = []
    else:
        return None

    actor_id = explicit_actor or buffer.actor_id or resolve_actor_id() or APP_ACTOR_ID
    return ActivityLog(
        actor_id=actor_id,
        action=action_key,
        message=message,
        changes=[
            ChangeRecord(
                object_type=_object_type(change.obj),
                object_id=_object_id(change.obj),
                before=change.before,
                after=after,
            )
            for change, after in records
        ],
    )


def record_activity(
    action: str,
    message: str,
    *,
    changes: list[tuple[Base, dict[str, Any] | None]] | None = None,
    actor_id: str | None = None,
) -> None:
    """Explicitly name the activity of the current transaction.

    Use it when the registry cannot produce a good enough message, or for an
    external-only activity outside any instrumented client. It replaces the
    automatic action and message for this transaction; automatic change records
    not already listed in `changes` are still attached.

    Requires an open session in the current task (see ActivityAwareSession).
    """
    session = current_session.get()
    if session is None:
        raise RuntimeError("record_activity() requires an open database session.")
    buffer = buffer_for(session.sync_session)
    buffer.remember_actor(resolve_actor_id())
    buffer.explicit = Explicit(
        action_key=action,
        message=message,
        actor_id=actor_id,
        changes=[TrackedChange(obj, before) for obj, before in (changes or [])],
    )
