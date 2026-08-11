# ═══════════════════════════════════════════════
# models/menu_item.py — SQLAlchemy Model
# ═══════════════════════════════════════════════

import uuid
from datetime import datetime

from sqlalchemy import String, Text, DECIMAL, Boolean, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB, TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base


class MenuItem(Base):
    """Menu item model — with JSONB ingredients, TSVECTOR search, and sync tracking."""

    __tablename__ = "menu_items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    restaurant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False
    )
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("categories.id", ondelete="SET NULL"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # 🔥 v2.2: JSONB ingredients for allergy filtering
    ingredients: Mapped[list] = mapped_column(JSONB, default=list, nullable=True)

    price: Mapped[float] = mapped_column(DECIMAL(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="EGP")
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)

    # 🔥 v2.2: calories column
    calories: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # 🔥 v2.2: synced_at for debugging
    synced_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # 🔥 v2.2: TSVECTOR for full-text search (managed by DB trigger)
    search_vector: Mapped[str | None] = mapped_column(TSVECTOR, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # ─── Relationships ───
    restaurant: Mapped["Restaurant"] = relationship("Restaurant", back_populates="menu_items")
    category: Mapped["Category | None"] = relationship("Category", back_populates="menu_items")
    embedding: Mapped["MenuEmbedding | None"] = relationship(
        "MenuEmbedding", back_populates="menu_item", uselist=False
    )
    order_items: Mapped[list["OrderItem"]] = relationship("OrderItem", back_populates="menu_item")
