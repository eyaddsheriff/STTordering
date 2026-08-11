# ═══════════════════════════════════════════════
# schemas/customer.py — Customer Schemas
# ═══════════════════════════════════════════════

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CustomerBase(BaseModel):
    phone: str
    name: str | None = None
    preferred_language: str = "ar"


class CustomerCreate(CustomerBase):
    pass


class CustomerUpdate(BaseModel):
    name: str | None = None
    preferred_language: str | None = None


class CustomerResponse(CustomerBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    created_at: datetime