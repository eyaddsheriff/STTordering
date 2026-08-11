# ═══════════════════════════════════════════════
# schemas/order.py — Order Schemas
# ═══════════════════════════════════════════════

import uuid
from datetime import datetime
from typing import List

from pydantic import BaseModel, ConfigDict


class OrderItemCreate(BaseModel):
    menu_item_id: uuid.UUID
    quantity: int
    special_instructions: str | None = None


class OrderItemResponse(OrderItemCreate):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    order_id: uuid.UUID
    unit_price: float


class OrderBase(BaseModel):
    customer_id: uuid.UUID | None = None
    restaurant_id: uuid.UUID
    status: str = "pending"
    payment_status: str = "pending"


class OrderCreate(OrderBase):
    items: List[OrderItemCreate]


class OrderUpdate(BaseModel):
    status: str | None = None
    payment_status: str | None = None
    total_price: float | None = None


class OrderResponse(OrderBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    total_price: float
    created_at: datetime
    updated_at: datetime
    items: List[OrderItemResponse] = []


class OrderListResponse(BaseModel):
    items: List[OrderResponse]
    total: int