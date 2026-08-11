# ═══════════════════════════════════════════════
# api/routes/sessions.py — Session Endpoints
# ═══════════════════════════════════════════════

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import get_db
from app.schemas.session import SessionCreate, SessionUpdate, SessionResponse
from app.schemas.conversation import ConversationResponse
from app.services.session_service import SessionService

router = APIRouter(tags=["Sessions"])


@router.post("", response_model=SessionResponse, status_code=201)
async def create_session(data: SessionCreate, db: AsyncSession = Depends(get_db)):
    return await SessionService.create_session(db, data)


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(session_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    try:
        return await SessionService.get_session(db, session_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/{session_id}", response_model=SessionResponse)
async def update_session(session_id: uuid.UUID, data: SessionUpdate, db: AsyncSession = Depends(get_db)):
    try:
        return await SessionService.update_session(db, session_id, data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{session_id}/history", response_model=list[ConversationResponse])
async def get_session_history(session_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    conversations = await SessionService.get_session_history(db, session_id)
    return [ConversationResponse.model_validate(c) for c in conversations]