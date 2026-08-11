# ═══════════════════════════════════════════════
# schemas/conversation.py — Conversation Schemas
# ═══════════════════════════════════════════════

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ConversationBase(BaseModel):
    customer_id: uuid.UUID | None = None
    session_id: uuid.UUID
    role: str
    message: str
    intent: str | None = None
    confidence: float | None = None


class ConversationCreate(ConversationBase):
    pass


class ConversationResponse(ConversationBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    created_at: datetime