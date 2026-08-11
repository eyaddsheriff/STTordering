# ═══════════════════════════════════════════════
# api/routes/conversations.py — Conversation Endpoints
# ═══════════════════════════════════════════════

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import get_db
from app.schemas.conversation import ConversationCreate, ConversationResponse
from app.repositories.conversation_repo import ConversationRepository

router = APIRouter(tags=["Conversations"])

@router.post("", response_model=ConversationResponse, status_code=201)
async def create_conversation(data: ConversationCreate, db: AsyncSession = Depends(get_db)):
    conv = await ConversationRepository.create(db, data)
    return ConversationResponse.model_validate(conv)


@router.get("/session/{session_id}", response_model=list[ConversationResponse])
async def get_conversations_by_session(session_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    conversations = await ConversationRepository.get_by_session(db, session_id)
    return [ConversationResponse.model_validate(c) for c in conversations]