# ═══════════════════════════════════════════════
# api/routes/restaurants.py — Restaurant Endpoints
# ═══════════════════════════════════════════════

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import get_db
from app.schemas.restaurant import RestaurantCreate, RestaurantUpdate, RestaurantResponse, RestaurantListResponse
from app.services.restaurant_service import RestaurantService

router = APIRouter(tags=["Restaurants"])


@router.get("", response_model=RestaurantListResponse)
async def list_restaurants(skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=1000), is_open: Optional[bool] = None, db: AsyncSession = Depends(get_db)):
    return await RestaurantService.list_restaurants(db, skip, limit, is_open)


@router.get("/{restaurant_id}", response_model=RestaurantResponse)
async def get_restaurant(restaurant_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    try:
        return await RestaurantService.get_restaurant(db, restaurant_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("", response_model=RestaurantResponse, status_code=201)
async def create_restaurant(data: RestaurantCreate, db: AsyncSession = Depends(get_db)):
    try:
        return await RestaurantService.create_restaurant(db, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{restaurant_id}", response_model=RestaurantResponse)
async def update_restaurant(restaurant_id: uuid.UUID, data: RestaurantUpdate, db: AsyncSession = Depends(get_db)):
    try:
        return await RestaurantService.update_restaurant(db, restaurant_id, data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{restaurant_id}", status_code=204)
async def delete_restaurant(restaurant_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    try:
        await RestaurantService.delete_restaurant(db, restaurant_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))