# ═══════════════════════════════════════════════
# schemas/customer_preference.py — CustomerPreference Schemas
# ═══════════════════════════════════════════════

import uuid
from datetime import datetime
from typing import List

from pydantic import BaseModel, ConfigDict


class CustomerPreferenceBase(BaseModel):
    customer_id: uuid.UUID
    favorite_categories: List[str] = []
    favorite_restaurants: List[str] = []
    disliked_ingredients: List[str] = []
    allergies: List[str] = []
    average_budget: float | None = None
    notes: str | None = None


class CustomerPreferenceCreate(CustomerPreferenceBase):
    pass


class CustomerPreferenceUpdate(BaseModel):
    favorite_categories: List[str] | None = None
    favorite_restaurants: List[str] | None = None
    disliked_ingredients: List[str] | None = None
    allergies: List[str] | None = None
    average_budget: float | None = None
    notes: str | None = None


class CustomerPreferenceResponse(CustomerPreferenceBase):
    model_config = ConfigDict(from_attributes=True)
    updated_at: datetime