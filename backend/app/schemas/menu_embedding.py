# ═══════════════════════════════════════════════
# schemas/menu_embedding.py — MenuEmbedding Schemas
# ═══════════════════════════════════════════════

import uuid
from datetime import datetime
from typing import List

from pydantic import BaseModel, ConfigDict


class MenuEmbeddingBase(BaseModel):
    menu_item_id: uuid.UUID
    embedding: List[float] | None = None
    embedding_model: str = "BAAI/bge-m3"


class MenuEmbeddingCreate(MenuEmbeddingBase):
    pass


class MenuEmbeddingResponse(MenuEmbeddingBase):
    model_config = ConfigDict(from_attributes=True)
    updated_at: datetime