# ═══════════════════════════════════════════════
# schemas/menu_item.py — MenuItem Schemas
# ═══════════════════════════════════════════════

import uuid
from datetime import datetime
from typing import List

from pydantic import BaseModel, ConfigDict, Field


class MenuItemBase(BaseModel):
    external_id: str
    restaurant_id: uuid.UUID
    category_id: uuid.UUID | None = None
    name: str
    description: str | None = None
    ingredients: List[str] = []
    price: float
    currency: str = "EGP"
    image_url: str | None = None
    is_available: bool = True
    is_deleted: bool = False
    calories: int | None = None


class MenuItemCreate(MenuItemBase):
    pass


class MenuItemUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    ingredients: List[str] | None = None
    price: float | None = None
    currency: str | None = None
    image_url: str | None = None
    is_available: bool | None = None
    is_deleted: bool | None = None
    calories: int | None = None
    category_id: uuid.UUID | None = None
    synced_at: datetime | None = None


class MenuItemResponse(MenuItemBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    synced_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class MenuItemListResponse(BaseModel):
    items: List[MenuItemResponse]
    total: int


class MenuFilters(BaseModel):
    restaurant_id: uuid.UUID | None = None
    category_id: uuid.UUID | None = None
    price_min: float | None = Field(None, ge=0)
    price_max: float | None = Field(None, ge=0)
    is_available: bool | None = True
    exclude_ingredients: List[str] = []


class MenuSearchRequest(BaseModel):
    query: str | None = None
    search_type: str = "text"
    filters: MenuFilters | None = None


class MenuSearchResponse(BaseModel):
    items: List[MenuItemResponse]
    total: int
    search_type: str
    query: str | None = None