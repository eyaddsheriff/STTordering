# ═══════════════════════════════════════════════
# api/routes/customers.py — Customer Endpoints
# ═══════════════════════════════════════════════

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import get_db
from app.schemas.customer import CustomerCreate, CustomerUpdate, CustomerResponse
from app.schemas.customer_preference import CustomerPreferenceUpdate, CustomerPreferenceResponse
from app.services.customer_service import CustomerService

router = APIRouter(tags=["Customers"]) 


@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(customer_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    try:
        return await CustomerService.get_customer(db, customer_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("", response_model=CustomerResponse, status_code=201)
async def create_customer(data: CustomerCreate, db: AsyncSession = Depends(get_db)):
    try:
        return await CustomerService.create_customer(db, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{customer_id}", response_model=CustomerResponse)
async def update_customer(customer_id: uuid.UUID, data: CustomerUpdate, db: AsyncSession = Depends(get_db)):
    try:
        return await CustomerService.update_customer(db, customer_id, data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{customer_id}/preferences", response_model=CustomerPreferenceResponse | None)
async def get_customer_preferences(customer_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    return await CustomerService.get_preferences(db, customer_id)


@router.patch("/{customer_id}/preferences", response_model=CustomerPreferenceResponse)
async def update_customer_preferences(customer_id: uuid.UUID, data: CustomerPreferenceUpdate, db: AsyncSession = Depends(get_db)):
    try:
        return await CustomerService.create_or_update_preferences(db, customer_id, data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))