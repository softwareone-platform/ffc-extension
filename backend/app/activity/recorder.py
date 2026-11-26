from collections import defaultdict
from collections.abc import Awaitable, Callable, Iterable
from dataclasses import dataclass
from types import TracebackType
from typing import Any, Self

from sqlalchemy import Connection, event, select, tuple_
from sqlalchemy.ext.asyncio import AsyncSession, AsyncSessionTransaction
from sqlalchemy.orm import Mapper, ORMExecuteState, Session, object_session
from sqlalchemy.orm.attributes import instance_state
from sqlalchemy.orm.base import NEVER_SET, NO_VALUE
from sqlalchemy.orm.state import InstanceState

from app.activity.snapshot import encode_values, mask_sensitive
from app.db.constants import APP_ACTOR_ID
from app.db.models import ActivityLog, ActivityNote, Base, ChangeRecord
from app.utils import resolve_actor_id

# Key of the root recorder in `Session.info`. Stored on the session, not in a ContextVar:
# changes are captured per session (= per transaction), whatever task or function makes them.
_SESSION_KEY = "activity_recorder"

# Execution option that turns capture off for one bulk statement, e.g. a cleanup job
# deleting thousands of rows: `delete(Model).execution_options(activity_log=False)`.
CAPTURE_OPTION = "activity_log"

# Rows read per SELECT when loading before/after images (asyncpg allows 32767 parameters).
_LOAD_CHUNK_SIZE = 1000

# A row is identified by its base mapper (so `Actor` and `User` share keys) and primary key.
type RowKey = tuple[Mapper, tuple[Any, ...]]


class ActivityRecorderError(RuntimeError):
    """The block did something whose changes cannot be recorded reliably."""


def _is_recorded(mapper: Mapper) -> bool:
    """False for the activity log's own tables and models opting out with `__activity_log__`."""
    cls = mapper.class_
    return not issubclass(cls, ActivityLog | ActivityNote | ChangeRecord) and getattr(
        cls, "__activity_log__", True
    )


def _load_rows(
    conn: Connection | Session, mapper: Mapper, identities: Iterable[tuple[Any, ...]]
) -> dict[tuple[Any, ...], dict[str, Any]]:
    """Read the current column values of the given rows, keyed by identity, in chunked SELECTs."""
    identities = list(identities)
    pk_keys = [mapper.get_property_by_column(col).key for col in mapper.primary_key]
    columns = [getattr(mapper.class_, attr.key).label(attr.key) for attr in mapper.column_attrs]
    rows = {}
    for start in range(0, len(identities), _LOAD_CHUNK_SIZE):
        chunk = identities[start : start + _LOAD_CHUNK_SIZE]
        query = select(*columns).where(tuple_(*mapper.primary_key).in_(chunk))
        for row in conn.execute(query).mappings():
            rows[tuple(row[key] for key in pk_keys)] = dict(row)
    return rows


def _committed_values(state: InstanceState) -> tuple[dict[str, Any], bool]:
    """
    Column values of `state` as they are in the database, taken from memory.
    Returns the values and whether they are complete. They are not when some column is
    expired, deferred, or was overwritten before ever being loaded.
    """
    values: dict[str, Any] = {}
    complete = True
    for attr in state.mapper.column_attrs:
        if attr.key in state.committed_state:
            value = state.committed_state[attr.key]
        elif attr.key in state.dict:
            value = state.dict[attr.key]
        else:
            value = NO_VALUE
        if value is NO_VALUE or value is NEVER_SET:
            complete = False
        else:
            values[attr.key] = value
    return values, complete


@dataclass
class _Change:
    mapper: Mapper  # the most specific mapper: gives `object_type` and the columns to read
    before: dict[str, Any] | None  # JSON-safe, unmasked; None for a row created in the block


class ActivityRecorder:
    """
    Record one activity, and every row it inserts, updates or deletes, in the current
    transaction.

    Changes are captured from the session while the block is open: ORM flushes, whichever
    code issued them, and ORM-enabled bulk `update()` / `delete()` statements. Each change
    record holds the row as it was in the database when the block started and as it is
    when the block ends; rows that end up unchanged are left out. If the block raises,
    nothing is recorded.

    The actor is `actor_id` when given, else the one authenticated in the current request,
    else the application itself (commands, event consumers).

    `action` and `message` may be reassigned inside the block, for entries whose wording
    depends on the outcome; the values at the end of the block are recorded. A blank
    message at the end of the block raises `ValueError`, as at creation.

    Options:

    * `skip_if_unchanged`: write no entry when the block changed no row. Off by default:
      an API action with no local change (an order completed on MPT, a reimport requested)
      is still an activity worth an entry.
    * `atomic`: run the block in a savepoint. If it raises, every row it wrote is rolled
      back as well, so the enclosing transaction can be committed without the partial work
      of a failed step. Without it, rows flushed inside a failing block stay pending in the
      transaction; only the entry is not written.

    A recorder opened on a session that already has one open is a child: its changes go to
    the root's entry, and its action, message and actor are not recorded (the root's
    describe the activity). An atomic child still gets its own savepoint: when it fails,
    only its rows are rolled back and the root records the rest.

    `entry_sink` is for `ActivityOperation.step()`: instead of adding a new entry, a root
    recorder hands its change records to the sink, which attaches them to an existing one.
    """

    def __init__(
        self,
        session: AsyncSession,
        action: str,
        message: str,
        *,
        actor_id: str | None = None,
        skip_if_unchanged: bool = False,
        atomic: bool = False,
        entry_sink: Callable[[list[ChangeRecord]], Awaitable[None]] | None = None,
    ) -> None:
        if not message.strip():
            raise ValueError("An activity needs a message describing what was done.")
        self.session = session
        self.action = action
        self.message = message
        self.actor_id = actor_id
        self.skip_if_unchanged = skip_if_unchanged
        self.atomic = atomic
        self._entry_sink = entry_sink
        self._root: ActivityRecorder | None = None
        self._savepoint: AsyncSessionTransaction | None = None
        self._changes: dict[RowKey, _Change] = {}
        self._inserted: list[InstanceState] = []  # pending rows seen at the last flush
        self._bulk_touched: set[RowKey] = set()  # rows a bulk statement may have changed

    @classmethod
    def active(cls, session: AsyncSession | Session) -> "ActivityRecorder | None":
        """The root recorder open on `session`, if any."""
        if isinstance(session, AsyncSession):
            session = session.sync_session
        return session.info.get(_SESSION_KEY)

    async def __aenter__(self) -> Self:
        self._root = self.active(self.session)
        if self._root is None or self.atomic:
            # Write what was pending before the block, so it is not attributed to it (nor
            # rolled back with it when the block is atomic).
            await self.session.flush()
        if self.atomic:
            self._savepoint = await self.session.begin_nested()
        if self._root is None:
            self.session.sync_session.info[_SESSION_KEY] = self
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        if self._root is not None:
            # A child: its changes are already the root's. Its savepoint, if any, keeps or
            # discards its rows; the root reads them back when it builds its records.
            await self._end_savepoint(keep=exc_type is None)
            return
        try:
            if exc_type is None:
                await self._record()
        except BaseException:
            await self._end_savepoint(keep=False)
            raise
        finally:
            del self.session.sync_session.info[_SESSION_KEY]
        await self._end_savepoint(keep=exc_type is None)

    async def _record(self) -> None:
        """Build the change records and add the entry; called by the root block on success."""
        if not self.message.strip():
            raise ValueError("An activity needs a message describing what was done.")
        await self.session.flush()  # capture what is still pending
        changes = await self.session.run_sync(self._build_change_records)
        if self.skip_if_unchanged and not changes:
            return
        if self._entry_sink is not None:
            await self._entry_sink(changes)
        else:
            self.session.add(
                ActivityLog(
                    recorded_by_id=(
                        self.actor_id if self.actor_id is not None else resolve_actor_id()
                    ),
                    action=self.action,
                    message=self.message,
                    changes=changes,
                )
            )
        if self._savepoint is not None:
            await self.session.flush()  # the entry belongs in the savepoint with its rows

    async def _end_savepoint(self, keep: bool) -> None:
        """Release the block's savepoint, or roll it back to discard every row it wrote."""
        savepoint, self._savepoint = self._savepoint, None
        if savepoint is None:
            return  # not atomic
        if keep:
            await savepoint.commit()
        elif self.session.sync_session.get_nested_transaction() is savepoint.sync_transaction:
            # Still the current savepoint, even after a failed flush inside the block left it
            # inactive: rolling it back makes the enclosing transaction usable again. It is
            # not when the block already rolled the whole session back.
            await savepoint.rollback()

    # -- capture (called from the session and mapper event listeners below) -----------

    def _prefetch_before(self, session: Session, states: Iterable[InstanceState]) -> None:
        """
        Take the before image of the rows a flush is about to write, reading the ones
        that are incomplete in memory in one SELECT per mapper rather than one per row.
        """
        incomplete: dict[Mapper, list[tuple[Any, ...]]] = defaultdict(list)
        for state in states:
            mapper, identity = state.mapper, state.identity
            if identity is None or (mapper.base_mapper, identity) in self._changes:
                continue
            if not _is_recorded(mapper):
                continue
            values, complete = _committed_values(state)
            if complete:
                self._changes[(mapper.base_mapper, identity)] = _Change(
                    mapper, encode_values(values)
                )
            else:
                incomplete[mapper].append(identity)
        for mapper, identities in incomplete.items():
            self._capture_rows_before(session, mapper, identities)

    def _capture_before(self, conn: Connection, state: InstanceState) -> None:
        """Fallback for rows the flush writes without them being dirty, e.g. synced FKs."""
        mapper, identity = state.mapper, state.identity
        if identity is None or (mapper.base_mapper, identity) in self._changes:
            return  # keep the image from before the first change
        values, complete = _committed_values(state)
        if not complete:
            values = _load_rows(conn, mapper, [identity]).get(identity, {})
        self._changes[(mapper.base_mapper, identity)] = _Change(mapper, encode_values(values))

    def _capture_rows_before(
        self, session: Session, mapper: Mapper, identities: Iterable[tuple[Any, ...]]
    ) -> None:
        """Read the before images of `identities` from the database; their after images too."""
        new = [i for i in identities if (mapper.base_mapper, i) not in self._changes]
        for identity, values in _load_rows(session, mapper, new).items():
            self._changes[(mapper.base_mapper, identity)] = _Change(mapper, encode_values(values))
        self._bulk_touched.update((mapper.base_mapper, i) for i in identities)

    def _register_inserted(self) -> None:
        """
        Key the rows the last flush inserted; a rolled-back one has no identity.
        Runs before `_prefetch_before` so that a row inserted in one flush and updated in
        the next keeps `before = None`.
        """
        for state in self._inserted:
            if state.identity is not None:
                key = (state.mapper.base_mapper, state.identity)
                self._changes.setdefault(key, _Change(state.mapper, None))

    # -- build the entry --------------------------------------------------------------

    def _build_change_records(self, session: Session) -> list[ChangeRecord]:
        self._register_inserted()
        # After images: from memory when the object is in the session and complete, else
        # read from the database (bulk-updated rows, expired rows, rows gone from the
        # identity map, hard-deleted rows).
        after_images: dict[RowKey, dict[str, Any] | None] = {}
        to_read: dict[Mapper, list[tuple[Any, ...]]] = defaultdict(list)
        for key, change in self._changes.items():
            base_mapper, identity = key
            obj = session.identity_map.get(base_mapper.identity_key_from_primary_key(identity))
            if obj is None or key in self._bulk_touched:
                to_read[change.mapper].append(identity)
                continue
            state = instance_state(obj)
            values, complete = _committed_values(state)
            if complete and not state.modified:
                after_images[key] = values
            else:
                to_read[change.mapper].append(identity)
        for mapper, identities in to_read.items():
            rows = _load_rows(session, mapper, identities)
            for identity in identities:
                after_images[(mapper.base_mapper, identity)] = rows.get(identity)

        records = []
        for key, change in self._changes.items():
            (_, identity) = key
            row = after_images[key]
            after = encode_values(row) if row is not None else None
            if after == change.before:
                continue  # never changed, or changed back, or rolled back
            records.append(
                ChangeRecord(
                    object_type=change.mapper.class_.__tablename__,
                    object_id=",".join(str(v) for v in identity),
                    before=mask_sensitive(change.mapper, change.before) if change.before else None,
                    after=mask_sensitive(change.mapper, after) if after else None,
                )
            )
        return records


def activity_recorder(
    session: AsyncSession,
    action: str,
    message: str,
    *,
    actor_id: str | None = None,
    skip_if_unchanged: bool = False,
    atomic: bool = False,
) -> ActivityRecorder:
    """
    Record one activity on `session`:

        async with activity_recorder(session, "organization.terminated", "...") as recorder:
            ...

    See `ActivityRecorder` for the options.
    """
    return ActivityRecorder(
        session,
        action,
        message,
        actor_id=actor_id,
        skip_if_unchanged=skip_if_unchanged,
        atomic=atomic,
    )


def system_activity_recorder(session: AsyncSession, action: str, message: str) -> ActivityRecorder:
    """
    Record one activity done by the application itself, for events and jobs:

        async with system_activity_recorder(session, "entitlement.terminated", "...") as recorder:
            ...

    The actor is the application, a block that changes nothing writes no entry, and a
    block that raises leaves neither rows nor entry behind (see `ActivityRecorder`).
    """
    return ActivityRecorder(
        session, action, message, actor_id=APP_ACTOR_ID, skip_if_unchanged=True, atomic=True
    )


# -- event listeners ------------------------------------------------------------------
# Registered when this module is imported, which any use of a recorder implies. They are
# no-ops (one dict lookup) for a session that has no recorder open.


def _recorder_of(target: Base) -> ActivityRecorder | None:
    session = object_session(target)
    return session.info.get(_SESSION_KEY) if session is not None else None


@event.listens_for(Session, "before_flush")
def _on_before_flush(session: Session, flush_context: object, instances: object) -> None:
    recorder = session.info.get(_SESSION_KEY)
    if recorder is None:
        return
    recorder._register_inserted()  # rows inserted by earlier flushes now have an identity
    recorder._inserted = [
        instance_state(obj) for obj in session.new if _is_recorded(instance_state(obj).mapper)
    ]
    modified = [obj for obj in session.dirty if session.is_modified(obj, include_collections=False)]
    recorder._prefetch_before(
        session, [instance_state(obj) for obj in [*modified, *session.deleted]]
    )


@event.listens_for(Base, "before_update", propagate=True)
@event.listens_for(Base, "before_delete", propagate=True)
def _on_before_update_or_delete(mapper: Mapper, connection: Connection, target: Base) -> None:
    recorder = _recorder_of(target)
    if recorder is not None and _is_recorded(mapper):
        recorder._capture_before(connection, instance_state(target))


@event.listens_for(Session, "do_orm_execute")
def _on_orm_execute(execute_state: ORMExecuteState) -> None:
    """
    Capture the rows an ORM-enabled bulk `update()` / `delete()` is about to touch, by
    selecting their primary keys with the statement's own WHERE clause first.

    Known limit: the pre-select and the statement are two reads under READ COMMITTED. A row
    that another transaction makes match the WHERE clause in between is changed by the
    statement but not recorded; a row that it changes in between keeps a before image that
    predates that change.
    """
    recorder = execute_state.session.info.get(_SESSION_KEY)
    is_dml = execute_state.is_insert or execute_state.is_update or execute_state.is_delete
    if recorder is None or not is_dml:
        return  # reads, and textual SQL (which the ORM cannot inspect)
    if not execute_state.execution_options.get(CAPTURE_OPTION, True):
        return
    mapper = execute_state.bind_mapper
    if mapper is not None and not _is_recorded(mapper):
        return
    if mapper is None or execute_state.is_insert:
        raise ActivityRecorderError(
            "Inside an ActivityRecorder block, only ORM-enabled update()/delete() bulk "
            "statements are captured. Use the ORM, or pass "
            f"execution_options({CAPTURE_OPTION}=False) to skip recording this statement."
        )
    pk_keys = [mapper.get_property_by_column(col).key for col in mapper.primary_key]
    if isinstance(execute_state.parameters, list):  # "bulk update by primary key"
        identities = [tuple(params[key] for key in pk_keys) for params in execute_state.parameters]
    else:
        statement: Any = execute_state.statement
        query = select(*(getattr(mapper.class_, key) for key in pk_keys))
        if statement.whereclause is not None:
            query = query.where(statement.whereclause)
        identities = [tuple(row) for row in execute_state.session.execute(query)]
    recorder._capture_rows_before(execute_state.session, mapper, identities)


@event.listens_for(Session, "before_commit")
def _on_before_commit(session: Session) -> None:
    # `before_commit` also fires when a savepoint (`begin_nested()`) is released; only the
    # outer commit would split the entry from the changes it describes.
    if session.info.get(_SESSION_KEY) is not None and not session.in_nested_transaction():
        raise ActivityRecorderError(
            "Cannot commit inside an ActivityRecorder block: the entry would not be part of "
            "the transaction it describes. Commit after the block."
        )
