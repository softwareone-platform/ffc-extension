"""Level 2: record successful external calls without touching their call sites.

How it works, in three steps:

1. `@instrument` is placed on an API client class (FFCAPIClient, MPTClient, ...).
2. For every method of that class listed in TRACKED_EXTERNAL_CALLS, the decorator
   replaces the method with a wrapper that runs the real method and then records
   the call in the activity log.
3. The record is buffered on the open DB session, so it is saved together with the
   DB changes of the same transaction. If no session is open, it is saved right
   away in its own small transaction.

A failing external call records nothing. A failure *while recording* is logged and
swallowed, so the activity log can never break business code.
"""

import functools
import inspect
import logging
from collections.abc import Callable
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.activity_log.buffer import ExternalCall, buffer_for
from app.activity_log.constants import APP_ACTOR_ID
from app.activity_log.context import current_session, resolve_actor_id
from app.activity_log.registry import TRACKED_EXTERNAL_CALLS, ExternalCallActivityTracker
from app.db.models import ActivityLog

logger = logging.getLogger(__name__)

# Set on every wrapper we create, so a method we already wrapped is recognized and skipped.
ALREADY_WRAPPED = "__activity_log_wrapped__"


def instrument[T: type](client_cls: T) -> T:
    """Class decorator: make the tracked methods of `client_cls` record their calls."""
    for method_name, tracker in _tracked_methods(client_cls):
        original_method = getattr(client_cls, method_name)
        if getattr(original_method, ALREADY_WRAPPED, False):
            continue
        setattr(client_cls, method_name, _wrap_method(original_method, tracker))
    return client_cls


def _tracked_methods(client_cls: type) -> list[tuple[str, ExternalCallActivityTracker]]:
    """Return `(method_name, tracker)` for every registry key that belongs to `client_cls`.

    Registry keys look like "FFCAPIClient.delete_tag". For FFCAPIClient this returns
    `[(("delete_tag", ExternalCallActivityTracker(
          key="optscale.tag.deleted",
          message="Tag {id} deleted on FinOps for Cloud",
          mask=frozenset(),
       )), ), ...]` and ignores the MPTClient.* and OptscaleClient.* keys.
    """
    prefix = f"{client_cls.__name__}."
    return [
        (key.removeprefix(prefix), tracker)
        for key, tracker in TRACKED_EXTERNAL_CALLS.items()
        if key.startswith(prefix)
    ]


def _wrap_method(
    method: Callable[..., Any], tracker: ExternalCallActivityTracker
) -> Callable[..., Any]:
    """Return an async function that runs `method` and then records the call."""

    @functools.wraps(method)  # the wrapper keeps the original name and docstring
    async def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
        # 1. Run the real method first. If it raises, nothing is recorded.
        result = await method(self, *args, **kwargs)

        # 2. Record the call. Any error here is logged, never raised.
        try:
            parameters = _map_method_values_to_signature_parameters(method, self, *args, **kwargs)
            message = tracker.render(parameters)
            await record_external_call(ExternalCall(tracker.key, message))
        except Exception:
            logger.exception("Failed to record external call %s in the activity log.", tracker.key)

        # 3. Give the caller exactly what the real method returned.
        return result

    setattr(wrapper, ALREADY_WRAPPED, True)
    return wrapper


def _map_method_values_to_signature_parameters(
    method: Callable[..., Any], *args: Any, **kwargs: Any
) -> dict[str, Any]:
    """Map the values a method was called with to the parameter names of its signature.

    Example: `async def delete_tag(self, id: str)` called as `client.delete_tag("T-1")`
    gives `{"id": "T-1"}`. Defaults are filled in and `self` is dropped. The message
    templates in the registry use these parameter names as placeholders.
    """
    bound = inspect.signature(method).bind(*args, **kwargs)
    bound.apply_defaults()
    return {name: value for name, value in bound.arguments.items() if name != "self"}


async def record_external_call(call: ExternalCall) -> None:
    """Buffer `call` on the open session, or write an external-only entry at once."""
    session = current_session.get()
    if session is None:
        await _write_now(call)
    else:
        _add_to_transaction(session, call)


def _add_to_transaction(session: AsyncSession, call: ExternalCall) -> None:
    """Queue the call on the session; it joins the activity log entry built at commit."""
    buffer = buffer_for(session.sync_session)
    buffer.remember_actor(resolve_actor_id())
    buffer.external.append(call)


async def _write_now(call: ExternalCall) -> None:
    """No session is open: write an entry for this call alone, in its own transaction."""
    from app.db.base import session_factory  # noqa: PLC0415 - app.db.base imports this package

    async with session_factory() as session, session.begin():
        session.add(
            ActivityLog(
                actor_id=resolve_actor_id() or APP_ACTOR_ID,
                action=call.action_key,
                message=call.message,
            )
        )
