# ═══════════════════════════════════════════════
# schemas/category.py — Category Schemas
# ═══════════════════════════════════════════════

import uuid
from typing import List

from pydantic import BaseModel, ConfigDict


class CategoryBase(BaseModel):
    external_id: str
    restaurant_id: uuid.UUID
    name: str
    description: str | None = None


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class CategoryResponse(CategoryBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID


class CategoryListResponse(BaseModel):
    items: List[CategoryResponse]
    total: int