"""Context variables that let the listeners resolve actor and session implicitly."""

from contextlib import suppress
from contextvars import ContextVar

from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.context import auth_context

# Set once at the entry point of a command or event handler that acts for a
# specific System. Requests do not need it: auth_context already carries the actor.
activity_actor: ContextVar[str | None] = ContextVar("activity_actor", default=None)

# The AsyncSession currently open in this task, if any. Set by ActivityAwareSession
# (see app.db.base), so commands and requests get it without any code of their own.
current_session: ContextVar[AsyncSession | None] = ContextVar("current_session", default=None)


def resolve_actor_id() -> str | None:
    """Actor acting in the current task, in priority order, or None when unknown.

    1. the authenticated actor of the current request,
    2. the actor a command or event handler declared through `activity_actor`.

    The caller falls back to the FinOps for Cloud app actor when this returns None.
    """
    with suppress(LookupError):
        actor = auth_context.get().get_actor()
        if actor is not None:
            return actor.id
    return activity_actor.get()
