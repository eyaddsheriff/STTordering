# ═══════════════════════════════════════════════
# repositories/conversation_repo.py — Conversation CRUD
# ═══════════════════════════════════════════════

import uuid
from typing import List, Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation
from app.schemas.conversation import ConversationCreate


class ConversationRepository:
    @staticmethod
    async def get_by_id(db: AsyncSession, conv_id: uuid.UUID) -> Optional[Conversation]:
        result = await db.execute(select(Conversation).where(Conversation.id == conv_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_session(db: AsyncSession, session_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[Conversation]:
        result = await db.execute(select(Conversation).where(Conversation.session_id == session_id).order_by(Conversation.created_at).offset(skip).limit(limit))
        return list(result.scalars().all())

    @staticmethod
    async def get_by_customer(db: AsyncSession, customer_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[Conversation]:
        result = await db.execute(select(Conversation).where(Conversation.customer_id == customer_id).order_by(Conversation.created_at.desc()).offset(skip).limit(limit))
        return list(result.scalars().all())

    @staticmethod
    async def create(db: AsyncSession, data: ConversationCreate) -> Conversation:
        conv = Conversation(**data.model_dump())
        db.add(conv)
        await db.commit()
        await db.refresh(conv)
        return conv

    @staticmethod
    async def delete_by_session(db: AsyncSession, session_id: uuid.UUID) -> None:
        await db.execute(Conversation.__table__.delete().where(Conversation.session_id == session_id))
        await db.commit()