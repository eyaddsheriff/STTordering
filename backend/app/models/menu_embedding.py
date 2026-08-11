# ═══════════════════════════════════════════════
# models/menu_embedding.py — SQLAlchemy Model
# ═══════════════════════════════════════════════

import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector

from app.db.base import Base


class MenuEmbedding(Base):
    """Menu embedding model — stores BGE-M3 vector embeddings for semantic search.

    🔒 Placeholder for Phase 5 — no generation logic yet.
    """

    __tablename__ = "menu_embeddings"

    menu_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("menu_items.id", ondelete="CASCADE"), primary_key=True
    )

    # Vector(1024) — BGE-M3 embedding dimension
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1024), nullable=True)

    embedding_model: Mapped[str] = mapped_column(
        String(100), default="BAAI/bge-m3"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # ─── Relationships ───
    menu_item: Mapped["MenuItem"] = relationship("MenuItem", back_populates="embedding")
