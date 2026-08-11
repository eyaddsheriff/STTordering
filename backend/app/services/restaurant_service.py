# ═══════════════════════════════════════════════
# services/restaurant_service.py — Restaurant Business Logic
# ═══════════════════════════════════════════════

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.restaurant_repo import RestaurantRepository
from app.schemas.restaurant import RestaurantCreate, RestaurantUpdate, RestaurantResponse, RestaurantListResponse


class RestaurantService:
    @staticmethod
    async def get_restaurant(db: AsyncSession, restaurant_id: uuid.UUID) -> RestaurantResponse:
        restaurant = await RestaurantRepository.get_by_id(db, restaurant_id)
        if not restaurant:
            raise ValueError("Restaurant not found")
        return RestaurantResponse.model_validate(restaurant)

    @staticmethod
    async def list_restaurants(db: AsyncSession, skip: int = 0, limit: int = 100, is_open: bool | None = None) -> RestaurantListResponse:
        items, total = await RestaurantRepository.get_all(db, skip, limit, is_open)
        return RestaurantListResponse(items=[RestaurantResponse.model_validate(i) for i in items], total=total)

    @staticmethod
    async def create_restaurant(db: AsyncSession, data: RestaurantCreate) -> RestaurantResponse:
        existing = await RestaurantRepository.get_by_external_id(db, data.external_id)
        if existing:
            raise ValueError("Restaurant with this external_id already exists")
        restaurant = await RestaurantRepository.create(db, data)
        return RestaurantResponse.model_validate(restaurant)

    @staticmethod
    async def update_restaurant(db: AsyncSession, restaurant_id: uuid.UUID, data: RestaurantUpdate) -> RestaurantResponse:
        restaurant = await RestaurantRepository.get_by_id(db, restaurant_id)
        if not restaurant:
            raise ValueError("Restaurant not found")
        updated = await RestaurantRepository.update(db, restaurant, data)
        return RestaurantResponse.model_validate(updated)

    @staticmethod
    async def delete_restaurant(db: AsyncSession, restaurant_id: uuid.UUID) -> None:
        restaurant = await RestaurantRepository.get_by_id(db, restaurant_id)
        if not restaurant:
            raise ValueError("Restaurant not found")
        await RestaurantRepository.delete(db, restaurant)