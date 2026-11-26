import datetime
import logging
from collections.abc import AsyncGenerator
from contextlib import AbstractAsyncContextManager, asynccontextmanager

from fastapi import HTTPException
from sqlalchemy import CursorResult, select, update
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.activity.recorder import ActivityRecorder
from app.db.base import session_factory
from app.db.models import ActivityLog, ActivityNote, ChangeRecord
from app.enums import ActivityStatus
from app.utils import resolve_actor_id

logger = logging.getLogger(__name__)

# Longest failure detail kept in the note of a failed attempt.
_FAILURE_DETAIL_MAX_LENGTH = 500

# SQLSTATE of a `FOR UPDATE NOWAIT` that found the row locked.
_LOCK_NOT_AVAILABLE = "55P03"


class ActivityOperation:
    """
    Record an activity that takes several steps or attempts (an order, add admin) as one
    activity log entry that shows its progress and its failed attempts.

        operation = ActivityOperation(session, f"order:{order_id}", "order.purchase", "...")
        async with operation.attempt():
            async with operation.step():
                ...  # database work
            await call_external_service()
            async with operation.step():
                ...  # database work
            await operation.complete("Order ORD-1 completed")

    The entry is the one with `operation_key = key` that is still in progress; it is
    created when none exists, so every attempt of the operation writes to the same entry.
    After `complete()` or `abandon()`, the same key starts a new entry.

    * `attempt()` wraps one try of the operation. When it raises, a note with the reason is
      added and the exception goes on; the entry stays in progress.
    * `step()` is a recorder block whose change records are appended to the entry.
    * `note()` adds a remark to the entry.
    * `complete()` and `abandon()` close the entry. Completion is always explicit.

    The actor is `actor_id` when given, else the one authenticated in the current request,
    else the application itself. The entry's actor and time are those of its latest
    update: an attempt on an existing entry, `complete()` and `abandon()` set them. The
    actors of earlier attempts stay on their notes.

    With `durable=True` (REST API only), creating the entry, the update at the start of an
    attempt and the notes are written in their own committed transactions, taken from
    `durable_session_factory`, so they survive a rollback of the request. Change records
    and the final status still follow the request's transaction.

    Rules:

    1. Steps contain only database work; external calls go between steps.
    2. Never commit inside a step.
    3. Never read the Activity Log to decide what to do.
    """

    def __init__(
        self,
        session: AsyncSession,
        key: str,
        action: str,
        message: str,
        *,
        actor_id: str | None = None,
        durable: bool = False,
        durable_session_factory: async_sessionmaker[AsyncSession] = session_factory,
    ) -> None:
        if not message.strip():
            raise ValueError("An activity needs a message describing what was done.")
        self.session = session
        self.key = key
        self.action = action
        self.message = message
        self.actor_id = actor_id
        self.durable = durable
        self._durable_session_factory = durable_session_factory
        self._entry_id: str | None = None

    def attempt(self) -> AbstractAsyncContextManager[None]:
        """
        One try of the operation. Finds or creates the entry; when the block raises, adds
        the note "Attempt failed: <detail>" and re-raises. A clean exit changes nothing.
        """
        return self._attempt()

    def step(self) -> ActivityRecorder:
        """
        A recorder block whose change records are appended to the operation's entry.

        A step that changes nothing adds nothing, and a step that raises rolls back its
        rows. Opened inside another recorder block, its changes go to that recorder.
        """
        return ActivityRecorder(
            self.session,
            self.action,
            self.message,
            atomic=True,
            skip_if_unchanged=True,
            entry_sink=self._append_changes,
        )

    async def note(self, message: str) -> None:
        """Add a remark to the entry, written by the current actor."""
        entry_id, _ = await self._find_or_create_entry()
        await self._add_note(entry_id, message, durable=self.durable)

    async def complete(self, message: str) -> None:
        """Close the entry as completed, with its final message. No-op on a closed entry."""
        await self._close(ActivityStatus.COMPLETED, note="Completed.", message=message)

    async def abandon(self, reason: str) -> None:
        """Close the entry as abandoned, noting why. No-op on a closed entry."""
        await self._close(ActivityStatus.ABANDONED, note=reason)

    # -- the entry ------------------------------------------------------------------------

    def _actor_id(self) -> str:
        return self.actor_id if self.actor_id is not None else resolve_actor_id()

    async def _find_or_create_entry(self) -> tuple[str, bool]:
        """The id of the operation's entry, and whether this call created it."""
        if self._entry_id is not None:
            return self._entry_id, False
        entry_id = await self._find_entry()
        created = False
        if entry_id is None:
            try:
                entry_id = await self._create_entry()
                created = True
            except IntegrityError:
                # A concurrent attempt created the entry first (partial unique index).
                entry_id = await self._find_entry()
                if entry_id is None:
                    raise
        self._entry_id = entry_id
        return entry_id, created

    async def _find_entry(self) -> str | None:
        return await self.session.scalar(
            select(ActivityLog.id).where(
                ActivityLog.operation_key == self.key,
                ActivityLog.status == ActivityStatus.IN_PROGRESS.value,
            )
        )

    async def _create_entry(self) -> str:
        entry = ActivityLog(
            action=self.action,
            message=self.message,
            status=ActivityStatus.IN_PROGRESS.value,
            operation_key=self.key,
            recorded_by_id=self._actor_id(),
        )
        if self.durable:
            async with self._durable_session_factory() as durable_session:
                durable_session.add(entry)
                await durable_session.commit()
        else:
            # Write what is pending first, so that a failed insert discards only the entry.
            await self.session.flush()
            async with self.session.begin_nested():
                self.session.add(entry)
                await self.session.flush()
        return entry.id

    async def _touch_entry(self, entry_id: str) -> None:
        """Make the current actor and time those of the entry: an attempt starts on it."""
        touch = (
            update(ActivityLog)
            .where(
                ActivityLog.id == entry_id,
                ActivityLog.status == ActivityStatus.IN_PROGRESS.value,
            )
            .values(
                recorded_by_id=self._actor_id(),
                recorded_at=datetime.datetime.now(datetime.UTC),
            )
        )
        if not self.durable:
            await self.session.execute(touch)
            return
        async with self._durable_session_factory() as durable_session:
            try:
                await durable_session.execute(
                    select(ActivityLog.id)
                    .where(ActivityLog.id == entry_id)
                    .with_for_update(nowait=True)
                )
                await durable_session.execute(touch)
                await durable_session.commit()
            except DBAPIError as error:
                if getattr(error.orig, "sqlstate", None) != _LOCK_NOT_AVAILABLE:
                    raise
                # Another transaction is updating the entry: do not wait for it.
                logger.warning(
                    "Activity log entry %s is locked: its actor and time were not updated "
                    "at the start of this attempt.",
                    entry_id,
                )

    # -- attempt --------------------------------------------------------------------------

    @asynccontextmanager
    async def _attempt(self) -> AsyncGenerator[None]:
        entry_id, created = await self._find_or_create_entry()
        if not created:
            await self._touch_entry(entry_id)
        try:
            yield
        except Exception as error:
            try:
                await self._add_note(
                    entry_id, f"Attempt failed: {_failure_detail(error)}", durable=self.durable
                )
            except Exception:
                logger.exception(
                    "Could not add the failure note to activity log entry %s.", entry_id
                )
            raise

    # -- step -----------------------------------------------------------------------------

    async def _append_changes(self, changes: list[ChangeRecord]) -> None:
        """Entry sink of `step()`: attach the step's change records to the entry."""
        entry_id, _ = await self._find_or_create_entry()
        # Set here, not by the database: Postgres `now()` is the transaction start time and
        # would give the records of every step of one attempt the same value.
        recorded_at = datetime.datetime.now(datetime.UTC)
        for change in changes:
            # By foreign key, not through `entry.changes`: records are appended without
            # loading or locking the ones the entry already has.
            change.activity_log_id = entry_id
            change.recorded_at = recorded_at
        self.session.add_all(changes)

    # -- notes and final status -----------------------------------------------------------

    async def _add_note(self, entry_id: str, message: str, *, durable: bool) -> None:
        note = ActivityNote(
            activity_log_id=entry_id,
            recorded_at=datetime.datetime.now(datetime.UTC),
            recorded_by_id=self._actor_id(),
            message=message,
        )
        if durable:
            # No lock on the entry is needed: inserting a note only takes a key-share lock
            # on it, which does not conflict with the request updating the entry.
            async with self._durable_session_factory() as durable_session:
                durable_session.add(note)
                await durable_session.commit()
        else:
            self.session.add(note)
            await self.session.flush()

    async def _close(
        self, status: ActivityStatus, *, note: str, message: str | None = None
    ) -> None:
        entry_id, _ = await self._find_or_create_entry()
        values = {
            "status": status.value,
            "recorded_by_id": self._actor_id(),
            "recorded_at": datetime.datetime.now(datetime.UTC),
        }
        if message is not None:
            values["message"] = message
        result: CursorResult = await self.session.execute(  # ty: ignore[invalid-assignment]
            update(ActivityLog)
            .where(
                ActivityLog.id == entry_id,
                ActivityLog.status == ActivityStatus.IN_PROGRESS.value,
            )
            .values(**values)
        )
        if result.rowcount == 0:
            return  # already completed or abandoned
        # Through the request's session in both modes, like the status it explains.
        await self._add_note(entry_id, note, durable=False)


def _failure_detail(error: Exception) -> str:
    """Why an attempt failed, in at most 500 characters and without a traceback."""
    if isinstance(error, HTTPException):
        detail = str(error.detail)
    else:
        detail = f"{type(error).__name__}: {error}"
    return detail[:_FAILURE_DETAIL_MAX_LENGTH]
