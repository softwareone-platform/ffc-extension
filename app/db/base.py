from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.conf import Settings

# from app.telemetry import setup_sqlalchemy_instrumentor

session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
    class_=AsyncSession, expire_on_commit=False
)


def configure_db_engine(settings: Settings) -> AsyncEngine:
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
