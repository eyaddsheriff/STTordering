# ═══════════════════════════════════════════════
# models/customer_preference.py — SQLAlchemy Model
# ═══════════════════════════════════════════════

import uuid
from datetime import datetime

from sqlalchemy import DECIMAL, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base


class CustomerPreference(Base):
    """Customer preference model — stores allergies, favorites, budget (JSONB)."""

    __tablename__ = "customer_preferences"

    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), primary_key=True
    )

    # JSONB arrays for flexible preferences
    favorite_categories: Mapped[list] = mapped_column(JSONB, default=list, nullable=True)
    favorite_restaurants: Mapped[list] = mapped_column(JSONB, default=list, nullable=True)
    disliked_ingredients: Mapped[list] = mapped_column(JSONB, default=list, nullable=True)
    allergies: Mapped[list] = mapped_column(JSONB, default=list, nullable=True)

    average_budget: Mapped[float | None] = mapped_column(DECIMAL(10, 2), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # ─── Relationships ───
    customer: Mapped["Customer"] = relationship("Customer", back_populates="preferences")
