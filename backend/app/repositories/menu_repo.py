# ═══════════════════════════════════════════════
# repositories/menu_repo.py — MenuItem CRUD + Search
# ═══════════════════════════════════════════════

import uuid
from typing import List, Optional

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.menu_item import MenuItem
from app.schemas.menu_item import MenuItemCreate, MenuItemUpdate, MenuFilters


class MenuRepository:
    @staticmethod
    async def get_by_id(db: AsyncSession, item_id: uuid.UUID) -> Optional[MenuItem]:
        result = await db.execute(select(MenuItem).where(MenuItem.id == item_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_restaurant(db: AsyncSession, restaurant_id: uuid.UUID, skip: int = 0, limit: int = 100) -> tuple[List[MenuItem], int]:
        query = select(MenuItem).where(and_(MenuItem.restaurant_id == restaurant_id, MenuItem.is_deleted == False))
        count_query = select(func.count()).select_from(MenuItem).where(and_(MenuItem.restaurant_id == restaurant_id, MenuItem.is_deleted == False))
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        result = await db.execute(query.offset(skip).limit(limit))
        return list(result.scalars().all()), total

    @staticmethod
    async def get_by_category(db: AsyncSession, category_id: uuid.UUID) -> List[MenuItem]:
        result = await db.execute(select(MenuItem).where(and_(MenuItem.category_id == category_id, MenuItem.is_deleted == False)))
        return list(result.scalars().all())

    @staticmethod
    async def search_text(db: AsyncSession, query_text: str, filters: MenuFilters | None = None, skip: int = 0, limit: int = 20) -> tuple[List[MenuItem], int]:
        conditions = [MenuItem.is_deleted == False]
        if filters:
            if filters.restaurant_id: conditions.append(MenuItem.restaurant_id == filters.restaurant_id)
            if filters.category_id: conditions.append(MenuItem.category_id == filters.category_id)
            if filters.price_min is not None: conditions.append(MenuItem.price >= filters.price_min)
            if filters.price_max is not None: conditions.append(MenuItem.price <= filters.price_max)
            if filters.is_available is not None: conditions.append(MenuItem.is_available == filters.is_available)
        
        ts_query = func.plainto_tsquery("simple", query_text)
        conditions.append(MenuItem.search_vector.op("@@")(ts_query))
        rank = func.ts_rank_cd(MenuItem.search_vector, ts_query)
        
        query = select(MenuItem).where(and_(*conditions)).order_by(rank.desc())
        count_query = select(func.count()).select_from(MenuItem).where(and_(*conditions))
        
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        result = await db.execute(query.offset(skip).limit(limit))
        return list(result.scalars().all()), total

    @staticmethod
    async def search_filter(db: AsyncSession, filters: MenuFilters, skip: int = 0, limit: int = 100) -> tuple[List[MenuItem], int]:
        conditions = [MenuItem.is_deleted == False]
        if filters.restaurant_id: conditions.append(MenuItem.restaurant_id == filters.restaurant_id)
        if filters.category_id: conditions.append(MenuItem.category_id == filters.category_id)
        if filters.price_min is not None: conditions.append(MenuItem.price >= filters.price_min)
        if filters.price_max is not None: conditions.append(MenuItem.price <= filters.price_max)
        if filters.is_available is not None: conditions.append(MenuItem.is_available == filters.is_available)
        
        query = select(MenuItem).where(and_(*conditions)).order_by(MenuItem.name)
        count_query = select(func.count()).select_from(MenuItem).where(and_(*conditions))
        
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        result = await db.execute(query.offset(skip).limit(limit))
        return list(result.scalars().all()), total

    @staticmethod
    async def get_all_ingredients(db: AsyncSession) -> List[str]:
        result = await db.execute(select(func.distinct(func.jsonb_array_elements_text(MenuItem.ingredients))).where(MenuItem.ingredients != None))
        return [row[0] for row in result.all() if row[0]]

    @staticmethod
    async def create(db: AsyncSession, data: MenuItemCreate) -> MenuItem:
        item = MenuItem(**data.model_dump())
        db.add(item)
        await db.commit()
        await db.refresh(item)
        return item

    @staticmethod
    async def update(db: AsyncSession, item: MenuItem, data: MenuItemUpdate) -> MenuItem:
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(item, field, value)
        await db.commit()
        await db.refresh(item)
        return item

    @staticmethod
    async def delete(db: AsyncSession, item: MenuItem) -> None:
        item.is_deleted = True
        await db.commit()