# ═══════════════════════════════════════════════
# schemas/sync.py — Sync Schemas
# ═══════════════════════════════════════════════

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SyncTriggerRequest(BaseModel):
    source_name: str | None = None
    force: bool = False


class SyncStatusResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    source_name: str
    last_sync_at: datetime | None = None
    sync_status: str
    records_processed: int
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime