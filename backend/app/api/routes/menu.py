# ═══════════════════════════════════════════════
# api/routes/menu.py — Menu Endpoints + Search
# ═══════════════════════════════════════════════

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import get_db
from app.schemas.menu_item import MenuItemCreate, MenuItemUpdate, MenuItemResponse, MenuItemListResponse, MenuSearchRequest, MenuSearchResponse
from app.services.menu_service import MenuService

router = APIRouter(tags=["Menu"]) 


@router.get("", response_model=MenuItemListResponse)
async def list_menu_items(restaurant_id: uuid.UUID | None = None, category_id: uuid.UUID | None = None, skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=1000), db: AsyncSession = Depends(get_db)):
    return await MenuService.list_items(db, restaurant_id, category_id, skip, limit)


@router.get("/ingredients", response_model=list[str])
async def get_all_ingredients(db: AsyncSession = Depends(get_db)):
    return await MenuService.get_ingredients(db)


@router.get("/{item_id}", response_model=MenuItemResponse)
async def get_menu_item(item_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    try:
        return await MenuService.get_item(db, item_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/search", response_model=MenuSearchResponse)
async def search_menu(request: MenuSearchRequest, db: AsyncSession = Depends(get_db)):
    return await MenuService.search(db, request)


@router.post("", response_model=MenuItemResponse, status_code=201)
async def create_menu_item(data: MenuItemCreate, db: AsyncSession = Depends(get_db)):
    try:
        return await MenuService.create_item(db, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{item_id}", response_model=MenuItemResponse)
async def update_menu_item(item_id: uuid.UUID, data: MenuItemUpdate, db: AsyncSession = Depends(get_db)):
    try:
        return await MenuService.update_item(db, item_id, data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{item_id}", status_code=204)
async def delete_menu_item(item_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    try:
        await MenuService.delete_item(db, item_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))