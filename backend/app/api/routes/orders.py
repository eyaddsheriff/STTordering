# ═══════════════════════════════════════════════
# api/routes/orders.py — Order Endpoints
# ═══════════════════════════════════════════════

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import get_db
from app.schemas.order import OrderCreate, OrderUpdate, OrderResponse, OrderListResponse
from app.services.order_service import OrderService

router = APIRouter(tags=["Orders"]) 


@router.get("", response_model=OrderListResponse)
async def list_orders(customer_id: uuid.UUID | None = None, restaurant_id: uuid.UUID | None = None, skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=1000), db: AsyncSession = Depends(get_db)):
    return await OrderService.list_orders(db, customer_id, restaurant_id, skip, limit)


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(order_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    try:
        return await OrderService.get_order(db, order_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("", response_model=OrderResponse, status_code=201)
async def create_order(data: OrderCreate, db: AsyncSession = Depends(get_db)):
    try:
        return await OrderService.create_order(db, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{order_id}/status", response_model=OrderResponse)
async def update_order_status(order_id: uuid.UUID, data: OrderUpdate, db: AsyncSession = Depends(get_db)):
    try:
        return await OrderService.update_order(db, order_id, data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))