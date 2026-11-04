from contextlib import suppress
from contextvars import Token
from typing import Any, Self

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.activity_log.context import current_session
from app.activity_log.listeners import register_listeners
from app.conf import Settings

# from app.telemetry import setup_sqlalchemy_instrumentor


class ActivityAwareSession(AsyncSession):
    """AsyncSession that exposes itself through `current_session` while open.

    This is what lets instrumented API clients and `record_activity()` find the
    transaction they belong to without being handed a session.
    """

    _token: Token[AsyncSession | None] | None = None

    async def __aenter__(self) -> Self:
        self._token = current_session.set(self)
        return await super().__aenter__()

    async def __aexit__(self, type_: Any, value: Any, traceback: Any) -> None:
        try:
            await super().__aexit__(type_, value, traceback)
        finally:
            if self._token is not None:
                # The token belongs to the context that entered the session; if the
                # exit runs elsewhere, resetting is impossible and also unnecessary.
                with suppress(ValueError):
                    current_session.reset(self._token)
                self._token = None


session_factory: async_sessionmaker[ActivityAwareSession] = async_sessionmaker(
    class_=ActivityAwareSession, expire_on_commit=False
)


def configure_db_engine(settings: Settings) -> AsyncEngine:
    register_listeners()  # idempotent; covers the API, the CLI and the test suite
    db_engine = create_async_engine(
        str(settings.postgres_async_url),
        echo=settings.debug,
        future=True,
        pool_pre_ping=True,
        pool_recycle=280,
    )
    session_factory.configure(bind=db_engine)
    # setup_sqlalchemy_instrumentor(settings, db_engine)
    return db_engine


async def verify_db_connection(settings: Settings):
    async with session_factory() as session:
        result = await session.execute(text("SELECT 1"))

        if result.one()[0] != 1:
            raise RuntimeError("Could not verify database connection")
