# ═══════════════════════════════════════════════
# repositories/category_repo.py — Category CRUD
# ═══════════════════════════════════════════════

import uuid
from typing import List, Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryUpdate


class CategoryRepository:
    """CRUD operations for Category model."""

    @staticmethod
    async def get_by_id(db: AsyncSession, category_id: uuid.UUID) -> Optional[Category]:
        """Get category by ID."""
        result = await db.execute(select(Category).where(Category.id == category_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_restaurant(
        db: AsyncSession, restaurant_id: uuid.UUID
    ) -> List[Category]:
        """Get all categories for a restaurant."""
        result = await db.execute(
            select(Category).where(Category.restaurant_id == restaurant_id)
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_all(
        db: AsyncSession, skip: int = 0, limit: int = 100
    ) -> tuple[List[Category], int]:
        """Get all categories."""
        query = select(Category)
        count_query = select(func.count()).select_from(Category)
        
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        result = await db.execute(query.offset(skip).limit(limit))
        items = result.scalars().all()
        
        return list(items), total

    @staticmethod
    async def create(db: AsyncSession, data: CategoryCreate) -> Category:
        """Create a new category."""
        category = Category(**data.model_dump())
        db.add(category)
        await db.commit()
        await db.refresh(category)
        return category

    @staticmethod
    async def update(
        db: AsyncSession, category: Category, data: CategoryUpdate
    ) -> Category:
        """Update a category."""
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(category, field, value)
        await db.commit()
        await db.refresh(category)
        return category

    @staticmethod
    async def delete(db: AsyncSession, category: Category) -> None:
        """Delete a category."""
        await db.delete(category)
        await db.commit()