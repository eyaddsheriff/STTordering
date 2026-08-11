# ═══════════════════════════════════════════════
# repositories/restaurant_repo.py — Restaurant CRUD
# ═══════════════════════════════════════════════

import uuid
from typing import List, Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.restaurant import Restaurant
from app.schemas.restaurant import RestaurantCreate, RestaurantUpdate


class RestaurantRepository:
    """CRUD operations for Restaurant model."""

    @staticmethod
    async def get_by_id(db: AsyncSession, restaurant_id: uuid.UUID) -> Optional[Restaurant]:
        """Get restaurant by ID."""
        result = await db.execute(select(Restaurant).where(Restaurant.id == restaurant_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_external_id(db: AsyncSession, external_id: str) -> Optional[Restaurant]:
        """Get restaurant by external_id."""
        result = await db.execute(
            select(Restaurant).where(Restaurant.external_id == external_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_all(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        is_open: bool | None = None,
    ) -> tuple[List[Restaurant], int]:
        """Get all restaurants with optional filtering."""
        query = select(Restaurant).where(Restaurant.is_deleted == False)
        
        if is_open is not None:
            query = query.where(Restaurant.is_open == is_open)
        
        # Count total
        count_query = select(func.count()).select_from(Restaurant).where(Restaurant.is_deleted == False)
        if is_open is not None:
            count_query = count_query.where(Restaurant.is_open == is_open)
        
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # Paginated results
        result = await db.execute(query.offset(skip).limit(limit))
        items = result.scalars().all()
        
        return list(items), total

    @staticmethod
    async def create(db: AsyncSession, data: RestaurantCreate) -> Restaurant:
        """Create a new restaurant."""
        restaurant = Restaurant(**data.model_dump())
        db.add(restaurant)
        await db.commit()
        await db.refresh(restaurant)
        return restaurant

    @staticmethod
    async def update(
        db: AsyncSession, restaurant: Restaurant, data: RestaurantUpdate
    ) -> Restaurant:
        """Update a restaurant."""
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(restaurant, field, value)
        await db.commit()
        await db.refresh(restaurant)
        return restaurant

    @staticmethod
    async def delete(db: AsyncSession, restaurant: Restaurant) -> None:
        """Soft delete a restaurant."""
        restaurant.is_deleted = True
        await db.commit()