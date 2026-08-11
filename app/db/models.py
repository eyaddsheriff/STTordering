"""SQLAlchemy models for the local search-layer database.

Table shapes now come from the authoritative `database/01-extensions.sql` through `04-seed.sql`
(pulled from a coworker's `feature/database-backend` branch), replacing the earlier reverse-engineered
version. Confirms `menu_items` genuinely has no `has_variant`/variant concept - price is a plain
`NOT NULL` column there too, not just in our earlier guess.

`menu_embeddings` (BGE-M3, 1024-dim, HNSW-indexed) exists in the schema for the planned pgvector
semantic search, but has no population/generation logic anywhere yet (confirmed against the
coworker's branch) - it's schema-only. Real semantic search is still open work.
"""

import uuid

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


def _uuid_pk() -> Mapped[uuid.UUID]:
    return mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))


class Restaurant(Base):
    __tablename__ = "restaurants"

    id: Mapped[uuid.UUID] = _uuid_pk()
    external_id: Mapped[str] = mapped_column(String, unique=True)
    name: Mapped[str] = mapped_column(String)
    description: Mapped[str | None] = mapped_column(Text)
    phone: Mapped[str | None] = mapped_column(String)
    address: Mapped[str | None] = mapped_column(Text)
    latitude: Mapped[float | None] = mapped_column(Numeric)
    longitude: Mapped[float | None] = mapped_column(Numeric)
    rating: Mapped[float | None] = mapped_column(Numeric)
    is_open: Mapped[bool] = mapped_column(Boolean, default=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    synced_at: Mapped[object | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[uuid.UUID] = _uuid_pk()
    external_id: Mapped[str] = mapped_column(String, unique=True)
    restaurant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("restaurants.id"))
    name: Mapped[str] = mapped_column(String)
    description: Mapped[str | None] = mapped_column(Text)


class MenuItem(Base):
    __tablename__ = "menu_items"

    id: Mapped[uuid.UUID] = _uuid_pk()
    external_id: Mapped[str] = mapped_column(String, unique=True)
    restaurant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("restaurants.id"))
    # Nullable per the real schema (ON DELETE SET NULL) - a menu item can outlive its category.
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("categories.id", ondelete="SET NULL")
    )
    name: Mapped[str] = mapped_column(String)
    description: Mapped[str | None] = mapped_column(Text)
    ingredients: Mapped[list | None] = mapped_column(JSONB)
    price: Mapped[float] = mapped_column(Numeric(10, 2))
    currency: Mapped[str] = mapped_column(String, default="EGP")
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    calories: Mapped[int | None] = mapped_column(Integer)
    synced_at: Mapped[object | None] = mapped_column(DateTime(timezone=True))


class MenuEmbedding(Base):
    """BGE-M3 (1024-dim) embedding per menu item, for the planned pgvector semantic search.

    Schema-only for now - no generation/population logic exists yet (see module docstring).
    """

    __tablename__ = "menu_embeddings"

    menu_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("menu_items.id", ondelete="CASCADE"), primary_key=True
    )
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1024))
    embedding_model: Mapped[str] = mapped_column(String, default="BAAI/bge-m3")
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[uuid.UUID] = _uuid_pk()
    phone: Mapped[str] = mapped_column(String, unique=True)
    name: Mapped[str | None] = mapped_column(String)
    preferred_language: Mapped[str | None] = mapped_column(String)


class CustomerPreference(Base):
    __tablename__ = "customer_preferences"

    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customers.id"), primary_key=True
    )
    favorite_categories: Mapped[list | None] = mapped_column(JSONB)
    favorite_restaurants: Mapped[list | None] = mapped_column(JSONB)
    disliked_ingredients: Mapped[list | None] = mapped_column(JSONB)
    allergies: Mapped[list | None] = mapped_column(JSONB)
    average_budget: Mapped[float | None] = mapped_column(Numeric)
    notes: Mapped[str | None] = mapped_column(Text)


class CallSession(Base):
    """Maps to the `sessions` table (renamed at the ORM level to avoid clashing with SQLAlchemy's own Session)."""

    __tablename__ = "sessions"

    id: Mapped[uuid.UUID] = _uuid_pk()
    customer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("customers.id"))
    status: Mapped[str] = mapped_column(String)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[uuid.UUID] = _uuid_pk()
    customer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("customers.id"))
    restaurant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("restaurants.id"))
    status: Mapped[str] = mapped_column(String)
    total_price: Mapped[float] = mapped_column(Numeric(10, 2))
    payment_status: Mapped[str] = mapped_column(String)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())


class OrderLineItem(Base):
    """Maps to the `order_items` table (renamed at the ORM level to avoid clashing with the agent's own OrderItem)."""

    __tablename__ = "order_items"

    id: Mapped[uuid.UUID] = _uuid_pk()
    order_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("orders.id"))
    menu_item_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("menu_items.id"))
    quantity: Mapped[int] = mapped_column(Integer)
    unit_price: Mapped[float] = mapped_column(Numeric(10, 2))


class ConversationHistory(Base):
    __tablename__ = "conversation_history"

    id: Mapped[uuid.UUID] = _uuid_pk()
    customer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("customers.id"))
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sessions.id"))
    role: Mapped[str] = mapped_column(String)
    message: Mapped[str] = mapped_column(Text)
    intent: Mapped[str | None] = mapped_column(String)
    confidence: Mapped[float | None] = mapped_column(Numeric)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SyncMetadata(Base):
    __tablename__ = "sync_metadata"

    id: Mapped[uuid.UUID] = _uuid_pk()
    source_name: Mapped[str] = mapped_column(String)
    last_sync_at: Mapped[object | None] = mapped_column(DateTime(timezone=True))
    sync_status: Mapped[str] = mapped_column(String)
    records_processed: Mapped[int | None] = mapped_column(Integer)
