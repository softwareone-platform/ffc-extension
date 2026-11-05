from contextlib import suppress
from contextvars import ContextVar, Token
from types import TracebackType
from typing import Self

from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import AsyncSession

from app.activity_log.constants import APP_ACTOR_ID
from app.activity_log.snapshot import snapshot
from app.auth.context import auth_context
from app.db.models import ActivityLog, Actor, Base, ChangeRecord

# The recorder whose block is open in the current task, if any. Task-local, so two
# requests never see each other's recorder.
_current: ContextVar["ActivityRecorder | None"] = ContextVar("activity_recorder", default=None)


def resolve_actor_id(actor: Actor | str | None) -> str:
    """Explicit actor, else the actor of the current request, else the application itself."""
    if isinstance(actor, Actor):
        return actor.id
    if actor:
        return actor
    with suppress(LookupError):
        current = auth_context.get().get_actor()
        if current is not None:
            return current.id
    return APP_ACTOR_ID


class ActivityRecorder:
    """
    Record one activity and the objects it changed, in the current transaction.
    If the block raises, nothing is recorded.
    A recorder opened while another one is running in the same task and on the same
    session becomes a child: it forwards tracked objects to the parent and appends its
    message to the parent's message, so it produces one entry.
    """

    def __init__(
        self,
        session: AsyncSession,
        action: str,
        message: str = "",
        *,
        actor: Actor | str | None = None,
    ) -> None:
        self.session = session
        self.action = action
        self.message = message
        self.actor = actor
        self._tracked: list[tuple[Base, dict | None]] = []
        self._parent: ActivityRecorder | None = None
        self._token: Token[ActivityRecorder | None] | None = None
        self._closed = False

    @classmethod
    def current(cls) -> "ActivityRecorder | None":
        recorder = _current.get()
        if recorder is None or recorder._closed:
            return None
        return recorder

    def track(self, obj: Base, *, created: bool = False) -> None:
        if self._parent is not None:
            self._parent.track(obj, created=created)
            return
        if any(tracked is obj for tracked, _ in self._tracked):
            return
        self._tracked.append((obj, None if created else snapshot(obj)))

    def append_message(self, message: str) -> None:
        if not message:
            return
        self.message = f"{self.message}; {message}" if self.message else message

    async def __aenter__(self) -> Self:
        parent = self.current()
        if parent is not None and parent.session is self.session:
            self._parent = parent
        else:
            self._token = _current.set(self)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self._closed = True
        if self._token is not None:
            _current.reset(self._token)
        if exc_type is not None:
            return  # record nothing; the exception propagates
        if self._parent is not None:
            self._parent.append_message(self.message)
            return

        await self.session.flush()  # generated ids and server defaults exist after this
        changes: list[ChangeRecord] = []
        for obj, before in self._tracked:
            await self.session.refresh(obj)
            changes.append(
                ChangeRecord(
                    object_type=obj.__tablename__,
                    object_id=str(inspect(obj).identity[0]),  # ty: ignore[not-subscriptable] - set by the flush above
                    before=before,
                    after=snapshot(obj),
                )
            )
        self.session.add(
            ActivityLog(
                actor_id=resolve_actor_id(self.actor),
                action=self.action,
                message=self.message,
                changes=changes,
            )
        )
