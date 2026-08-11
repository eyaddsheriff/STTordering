# ═══════════════════════════════════════════════
# api/routes/sync.py — Sync Endpoints (Placeholder)
# ═══════════════════════════════════════════════

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.base import get_db
from app.schemas.sync import SyncTriggerRequest, SyncStatusResponse
from app.models.sync_metadata import SyncMetadata

router = APIRouter(tags=["Sync"])


@router.post("/trigger", response_model=dict)
async def trigger_sync(request: SyncTriggerRequest | None = None, db: AsyncSession = Depends(get_db)):
    return {
        "status": "queued",
        "message": "Sync job queued (Phase 6 implementation pending)",
        "source": request.source_name if request else "manual",
    }


@router.get("/status", response_model=SyncStatusResponse | None)
async def get_sync_status(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SyncMetadata).order_by(SyncMetadata.updated_at.desc()).limit(1))
    sync_meta = result.scalar_one_or_none()
    if not sync_meta:
        return None
    return SyncStatusResponse.model_validate(sync_meta)