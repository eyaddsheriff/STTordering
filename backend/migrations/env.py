# ═══════════════════════════════════════════════
# migrations/env.py — Alembic Environment (Async)
# ═══════════════════════════════════════════════

import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# ─── Import our Base and Models ───
# This ensures all models are registered in Base.metadata for autogenerate
from app.db.base import Base
from app.core.config import get_settings

# Import all models so they register with Base.metadata
from app.models.restaurant import Restaurant
from app.models.category import Category
from app.models.menu_item import MenuItem
from app.models.menu_embedding import MenuEmbedding
from app.models.customer import Customer
from app.models.customer_preference import CustomerPreference
from app.models.session import Session
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.conversation import Conversation
from app.models.sync_metadata import SyncMetadata

settings = get_settings()

# ─── Alembic Config ───
config = context.config

# Override sqlalchemy.url with our async URL
config.set_main_option("sqlalchemy.url", settings.database_url)

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ─── Target Metadata ───
# This is what autogenerate compares against
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL and not an Engine.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,  # Detect column type changes
        compare_server_default=True,  # Detect default changes
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Run migrations with a given connection."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode with async engine."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


# ─── Entry Point ───
if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
