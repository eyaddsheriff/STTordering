# ═══════════════════════════════════════════════
# schemas/restaurant.py — Restaurant Schemas
# ═══════════════════════════════════════════════

import uuid
from datetime import datetime
from typing import List

from pydantic import BaseModel, ConfigDict


class RestaurantBase(BaseModel):
    external_id: str
    name: str
    description: str | None = None
    phone: str | None = None
    address: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    rating: float | None = None
    is_open: bool = True
    is_deleted: bool = False


class RestaurantCreate(RestaurantBase):
    pass


class RestaurantUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    phone: str | None = None
    address: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    rating: float | None = None
    is_open: bool | None = None
    is_deleted: bool | None = None
    synced_at: datetime | None = None


class RestaurantResponse(RestaurantBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    synced_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class RestaurantListResponse(BaseModel):
    items: List[RestaurantResponse]
    total: int