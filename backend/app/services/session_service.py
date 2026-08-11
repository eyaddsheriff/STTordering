# ═══════════════════════════════════════════════
# services/session_service.py — Session Business Logic
# ═══════════════════════════════════════════════

import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.session import Session
from app.schemas.session import SessionCreate, SessionUpdate, SessionResponse


class SessionService:
    @staticmethod
    async def get_session(db: AsyncSession, session_id: uuid.UUID) -> SessionResponse:
        result = await db.execute(select(Session).where(Session.id == session_id))
        session = result.scalar_one_or_none()
        if not session:
            raise ValueError("Session not found")
        return SessionResponse.model_validate(session)

    @staticmethod
    async def create_session(db: AsyncSession, data: SessionCreate) -> SessionResponse:
        session = Session(**data.model_dump())
        db.add(session)
        await db.commit()
        await db.refresh(session)
        return SessionResponse.model_validate(session)

    @staticmethod
    async def update_session(db: AsyncSession, session_id: uuid.UUID, data: SessionUpdate) -> SessionResponse:
        result = await db.execute(select(Session).where(Session.id == session_id))
        session = result.scalar_one_or_none()
        if not session:
            raise ValueError("Session not found")
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(session, field, value)
        await db.commit()
        await db.refresh(session)
        return SessionResponse.model_validate(session)

    @staticmethod
    async def get_session_history(db: AsyncSession, session_id: uuid.UUID):
        from app.repositories.conversation_repo import ConversationRepository
        conversations = await ConversationRepository.get_by_session(db, session_id)
        return conversations