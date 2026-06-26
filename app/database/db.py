from collections.abc import AsyncGenerator
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for SQLAlchemy declarative models."""


engine = None
SessionLocal: async_sessionmaker[AsyncSession] | None = None


async def init_database(database_url: str) -> None:
    """Initialize database engine and create tables when they do not exist."""
    global SessionLocal, engine

    if database_url.startswith("sqlite"):
        database_path = database_url.split("///")[-1]
        if database_path and database_path != ":memory:":
            Path(database_path).parent.mkdir(parents=True, exist_ok=True)

    engine = create_async_engine(database_url, pool_pre_ping=True)
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    from app.database import models  # noqa: F401

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)


async def close_database() -> None:
    """Dispose database engine on application shutdown."""
    if engine is not None:
        await engine.dispose()


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async SQLAlchemy session."""
    if SessionLocal is None:
        raise RuntimeError("Database is not initialized")

    async with SessionLocal() as session:
        yield session
