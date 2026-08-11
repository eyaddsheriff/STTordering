# ═══════════════════════════════════════════════
# models/customer.py — SQLAlchemy Model
# ═══════════════════════════════════════════════

import uuid
from datetime import datetime

from sqlalchemy import String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base


class Customer(Base):
    """Customer model — stores customer info."""

    __tablename__ = "customers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    phone: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    preferred_language: Mapped[str] = mapped_column(
        String(10), default="ar"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # ─── Relationships ───
    preferences: Mapped["CustomerPreference | None"] = relationship(
        "CustomerPreference", back_populates="customer", uselist=False
    )
    sessions: Mapped[list["Session"]] = relationship("Session", back_populates="customer")
    orders: Mapped[list["Order"]] = relationship("Order", back_populates="customer")
    conversations: Mapped[list["Conversation"]] = relationship("Conversation", back_populates="customer")
