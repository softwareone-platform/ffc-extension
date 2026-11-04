"""Session events that make recording automatic for every ORM write."""

from typing import Any

from sqlalchemy import event
from sqlalchemy.orm import Session

from app.activity_log.buffer import buffer_for
from app.activity_log.context import resolve_actor_id
from app.activity_log.recorder import build_entry
from app.activity_log.registry import tracker_for
from app.activity_log.snapshot import before_image

_registered = False


def _before_flush(session: Session, flush_context: Any, instances: Any) -> None:
    buffer = buffer_for(session)
    tracked = False
    for obj in session.new:
        if tracker_for(obj) is not None:
            buffer.track(obj, before=None)
            tracked = True
    for obj in session.dirty:
        if tracker_for(obj) is not None and session.is_modified(obj, include_collections=False):
            buffer.track(obj, before=before_image(obj))
            tracked = True
    # session.deleted is intentionally ignored: deletions are logical in this
    # project (status = deleted) and therefore arrive through session.dirty.
    if tracked:
        # The request's auth context is reset before the session commits, so the
        # actor has to be captured while the business code is still running.
        buffer.remember_actor(resolve_actor_id())


def _before_commit(session: Session) -> None:
    # before_commit fires *before* the flush commit() performs, so pending changes
    # that were never flushed explicitly are not in the buffer yet. Flushing here
    # is allowed and runs _before_flush for them; it also gives every tracked
    # object its generated values (ids, timestamps) before the after-image is
    # taken. The ActivityLog row added below is picked up by the flush that
    # commit() performs after this hook.
    session.flush()
    buffer = buffer_for(session)
    if buffer.is_empty():
        return
    entry = build_entry(buffer)
    buffer.clear()
    if entry is not None:
        session.add(entry)


def _after_rollback(session: Session) -> None:
    # A rolled-back transaction must not leak tracked changes into the next one.
    buffer_for(session).clear()


def register_listeners() -> None:
    """Attach the listeners to the sync Session class. Idempotent."""
    global _registered
    if _registered:
        return
    event.listen(Session, "before_flush", _before_flush)
    event.listen(Session, "before_commit", _before_commit)
    event.listen(Session, "after_rollback", _after_rollback)
    _registered = True
