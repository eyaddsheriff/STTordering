# ═══════════════════════════════════════════════
# db/base.py — SQLAlchemy Async Engine + Session
# ═══════════════════════════════════════════════

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base
from app.core.config import get_settings

settings = get_settings()

# ─── Async Engine ───
# pool_pre_ping=True: Check connection before using (prevents stale connections)
# echo=False: Set to True in debug to see SQL queries
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

# ─── Async Session Factory ───
# expire_on_commit=False: Objects stay usable after commit (better for FastAPI)
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

# ─── Base Model ───
# All SQLAlchemy models inherit from this
Base = declarative_base()


# ─── Dependency for FastAPI ───
async def get_db() -> AsyncSession:
    """FastAPI dependency — yields a database session per request."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
