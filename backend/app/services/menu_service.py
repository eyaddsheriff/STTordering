# ═══════════════════════════════════════════════
# services/menu_service.py — Menu Business Logic + Search
# ═══════════════════════════════════════════════

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.menu_repo import MenuRepository
from app.repositories.restaurant_repo import RestaurantRepository
from app.repositories.category_repo import CategoryRepository
from app.schemas.menu_item import (
    MenuItemCreate, MenuItemUpdate, MenuItemResponse,
    MenuItemListResponse, MenuSearchRequest, MenuSearchResponse, MenuFilters,
)


class MenuService:
    @staticmethod
    async def get_item(db: AsyncSession, item_id: uuid.UUID) -> MenuItemResponse:
        item = await MenuRepository.get_by_id(db, item_id)
        if not item:
            raise ValueError("Menu item not found")
        return MenuItemResponse.model_validate(item)

    @staticmethod
    async def list_items(db: AsyncSession, restaurant_id: uuid.UUID | None = None, category_id: uuid.UUID | None = None, skip: int = 0, limit: int = 100) -> MenuItemListResponse:
        if restaurant_id:
            items, total = await MenuRepository.get_by_restaurant(db, restaurant_id, skip, limit)
        elif category_id:
            items = await MenuRepository.get_by_category(db, category_id)
            total = len(items)
        else:
            from sqlalchemy import select, func
            from app.models.menu_item import MenuItem
            query = select(MenuItem).where(MenuItem.is_deleted == False)
            count_query = select(func.count()).select_from(MenuItem).where(MenuItem.is_deleted == False)
            total_result = await db.execute(count_query)
            total = total_result.scalar()
            result = await db.execute(query.offset(skip).limit(limit))
            items = result.scalars().all()
        return MenuItemListResponse(items=[MenuItemResponse.model_validate(i) for i in items], total=total)

    @staticmethod
    async def search(db: AsyncSession, request: MenuSearchRequest) -> MenuSearchResponse:
        filters = request.filters or MenuFilters()
        if request.search_type == "text" and request.query:
            items, total = await MenuRepository.search_text(db, request.query, filters)
        elif request.search_type == "hybrid" and request.query:
            items, total = await MenuRepository.search_text(db, request.query, filters)
        else:
            items, total = await MenuRepository.search_filter(db, filters)
        return MenuSearchResponse(items=[MenuItemResponse.model_validate(i) for i in items], total=total, search_type=request.search_type, query=request.query)

    @staticmethod
    async def get_ingredients(db: AsyncSession) -> list[str]:
        return await MenuRepository.get_all_ingredients(db)

    @staticmethod
    async def create_item(db: AsyncSession, data: MenuItemCreate) -> MenuItemResponse:
        restaurant = await RestaurantRepository.get_by_id(db, data.restaurant_id)
        if not restaurant:
            raise ValueError("Restaurant not found")
        if data.category_id:
            category = await CategoryRepository.get_by_id(db, data.category_id)
            if not category:
                raise ValueError("Category not found")
        item = await MenuRepository.create(db, data)
        return MenuItemResponse.model_validate(item)

    @staticmethod
    async def update_item(db: AsyncSession, item_id: uuid.UUID, data: MenuItemUpdate) -> MenuItemResponse:
        item = await MenuRepository.get_by_id(db, item_id)
        if not item:
            raise ValueError("Menu item not found")
        updated = await MenuRepository.update(db, item, data)
        return MenuItemResponse.model_validate(updated)

    @staticmethod
    async def delete_item(db: AsyncSession, item_id: uuid.UUID) -> None:
        item = await MenuRepository.get_by_id(db, item_id)
        if not item:
            raise ValueError("Menu item not found")
        await MenuRepository.delete(db, item)