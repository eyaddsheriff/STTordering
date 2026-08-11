# ═══════════════════════════════════════════════
# api/routes/categories.py — Category Endpoints
# ═══════════════════════════════════════════════

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import get_db
from app.repositories.category_repo import CategoryRepository
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryResponse, CategoryListResponse

router = APIRouter(tags=["Categories"])


@router.get("", response_model=CategoryListResponse)
async def list_categories(restaurant_id: uuid.UUID | None = None, skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=1000), db: AsyncSession = Depends(get_db)):
    if restaurant_id:
        items = await CategoryRepository.get_by_restaurant(db, restaurant_id)
        return CategoryListResponse(items=[CategoryResponse.model_validate(i) for i in items], total=len(items))
    items, total = await CategoryRepository.get_all(db, skip, limit)
    return CategoryListResponse(items=[CategoryResponse.model_validate(i) for i in items], total=total)


@router.get("/{category_id}", response_model=CategoryResponse)
async def get_category(category_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    category = await CategoryRepository.get_by_id(db, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return CategoryResponse.model_validate(category)


@router.post("", response_model=CategoryResponse, status_code=201)
async def create_category(data: CategoryCreate, db: AsyncSession = Depends(get_db)):
    category = await CategoryRepository.create(db, data)
    return CategoryResponse.model_validate(category)


@router.patch("/{category_id}", response_model=CategoryResponse)
async def update_category(category_id: uuid.UUID, data: CategoryUpdate, db: AsyncSession = Depends(get_db)):
    category = await CategoryRepository.get_by_id(db, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    updated = await CategoryRepository.update(db, category, data)
    return CategoryResponse.model_validate(updated)


@router.delete("/{category_id}", status_code=204)
async def delete_category(category_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    category = await CategoryRepository.get_by_id(db, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    await CategoryRepository.delete(db, category)