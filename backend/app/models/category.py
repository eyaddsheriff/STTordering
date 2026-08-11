# ═══════════════════════════════════════════════
# models/category.py — SQLAlchemy Model
# ═══════════════════════════════════════════════

import uuid

from sqlalchemy import String, Text, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Category(Base):
    """Category model — menu categories per restaurant."""

    __tablename__ = "categories"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    restaurant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ─── Unique Constraint: external_id + restaurant_id ───
    __table_args__ = (
        UniqueConstraint("external_id", "restaurant_id", name="uq_category_external_restaurant"),
    )

    # ─── Relationships ───
    restaurant: Mapped["Restaurant"] = relationship("Restaurant", back_populates="categories")
    menu_items: Mapped[list["MenuItem"]] = relationship("MenuItem", back_populates="category")
