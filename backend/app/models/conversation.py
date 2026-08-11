# ═══════════════════════════════════════════════
# models/conversation.py — SQLAlchemy Model
# ═══════════════════════════════════════════════

import uuid
from datetime import datetime

from sqlalchemy import String, Text, DECIMAL, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base


class Conversation(Base):
    """Conversation history model — stores AI chat messages.

    🔥 v2.2: confidence uses DECIMAL(4,3) for higher precision (0.952).
    """

    __tablename__ = "conversation_history"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    customer_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customers.id", ondelete="SET NULL"), nullable=True
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    intent: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # 🔥 v2.2: DECIMAL(4,3) — stores 0.952 instead of 0.95
    confidence: Mapped[float | None] = mapped_column(DECIMAL(4, 3), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # ─── Relationships ───
    customer: Mapped["Customer | None"] = relationship("Customer", back_populates="conversations")
    session: Mapped["Session"] = relationship("Session", back_populates="conversations")
