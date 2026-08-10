"""One-off dev setup: create the local search-layer database, create tables, and load the sample
seed data (04-seed.sql at the repo root). Safe to re-run against an empty DB; not idempotent against
a DB that already has seed data loaded (the seed script will fail on unique-constraint violations).
"""

import asyncio
from pathlib import Path
from urllib.parse import urlsplit

import asyncpg
from sqlalchemy.ext.asyncio import create_async_engine

from app.config import settings
from app.db.models import Base

SEED_FILE = Path(__file__).resolve().parent.parent / "04-seed.sql"


async def _ensure_database_exists() -> None:
    parts = urlsplit(settings.database_url.replace("postgresql+asyncpg", "postgresql"))
    db_name = parts.path.lstrip("/")

    conn = await asyncpg.connect(
        host=parts.hostname, port=parts.port, user=parts.username, password=parts.password, database="postgres"
    )
    try:
        exists = await conn.fetchval("SELECT 1 FROM pg_database WHERE datname = $1", db_name)
        if not exists:
            await conn.execute(f'CREATE DATABASE "{db_name}"')
            print(f"Created database {db_name!r}")
        else:
            print(f"Database {db_name!r} already exists")
    finally:
        await conn.close()


async def _create_tables() -> None:
    engine = create_async_engine(settings.database_url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()
    print("Tables created")


async def _load_seed() -> None:
    parts = urlsplit(settings.database_url.replace("postgresql+asyncpg", "postgresql"))
    conn = await asyncpg.connect(
        host=parts.hostname,
        port=parts.port,
        user=parts.username,
        password=parts.password,
        database=parts.path.lstrip("/"),
    )
    try:
        sql = SEED_FILE.read_text(encoding="utf-8")
        await conn.execute(sql)
        print("Seed data loaded")
    finally:
        await conn.close()


async def main() -> None:
    await _ensure_database_exists()
    await _create_tables()
    await _load_seed()


if __name__ == "__main__":
    asyncio.run(main())
