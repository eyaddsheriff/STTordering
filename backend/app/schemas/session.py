# ═══════════════════════════════════════════════
# schemas/session.py — Session Schemas
# ═══════════════════════════════════════════════

import uuid
from datetime import datetime
from typing import List

from pydantic import BaseModel, ConfigDict


class SessionBase(BaseModel):
    customer_id: uuid.UUID | None = None
    status: str = "active"


class SessionCreate(SessionBase):
    pass


class SessionUpdate(BaseModel):
    status: str | None = None
    ended_at: datetime | None = None


class SessionResponse(SessionBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    started_at: datetime
    last_activity_at: datetime
    ended_at: datetime | None = None


class SessionHistoryResponse(BaseModel):
    session: SessionResponse
    conversations: List[dict]