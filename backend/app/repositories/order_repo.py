# ═══════════════════════════════════════════════
# repositories/order_repo.py — Order CRUD
# ═══════════════════════════════════════════════

import uuid
from typing import List, Optional

from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import Order
from app.models.order_item import OrderItem
from app.schemas.order import OrderCreate, OrderUpdate, OrderItemCreate


class OrderRepository:
    @staticmethod
    async def get_by_id(db: AsyncSession, order_id: uuid.UUID) -> Optional[Order]:
        """Get order by ID with items (eager loaded)."""
        result = await db.execute(
            select(Order)
            .where(Order.id == order_id)
            .options(selectinload(Order.items))
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_customer(
        db: AsyncSession, customer_id: uuid.UUID, skip: int = 0, limit: int = 100
    ) -> tuple[List[Order], int]:
        query = (
            select(Order)
            .where(Order.customer_id == customer_id)
            .order_by(Order.created_at.desc())
            .options(selectinload(Order.items))
        )
        count_query = select(func.count()).select_from(Order).where(Order.customer_id == customer_id)
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        result = await db.execute(query.offset(skip).limit(limit))
        return list(result.scalars().all()), total

    @staticmethod
    async def get_by_restaurant(
        db: AsyncSession, restaurant_id: uuid.UUID, skip: int = 0, limit: int = 100
    ) -> tuple[List[Order], int]:
        query = (
            select(Order)
            .where(Order.restaurant_id == restaurant_id)
            .order_by(Order.created_at.desc())
            .options(selectinload(Order.items))
        )
        count_query = select(func.count()).select_from(Order).where(Order.restaurant_id == restaurant_id)
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        result = await db.execute(query.offset(skip).limit(limit))
        return list(result.scalars().all()), total

    @staticmethod
    async def get_all(
        db: AsyncSession, skip: int = 0, limit: int = 100
    ) -> tuple[List[Order], int]:
        query = (
            select(Order)
            .order_by(Order.created_at.desc())
            .options(selectinload(Order.items))
        )
        count_query = select(func.count()).select_from(Order)
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        result = await db.execute(query.offset(skip).limit(limit))
        return list(result.scalars().all()), total

    @staticmethod
    async def create(db: AsyncSession, data: OrderCreate) -> Order:
        """Create a new order."""
        order = Order(
            customer_id=data.customer_id,
            restaurant_id=data.restaurant_id,
            status=data.status,
            payment_status=data.payment_status,
            total_price=0,
        )
        db.add(order)
        await db.flush()
        return order

    @staticmethod
    async def add_item(
        db: AsyncSession, order_id: uuid.UUID, item_data: OrderItemCreate, unit_price: float
    ) -> OrderItem:
        """Add an item to an order."""
        item = OrderItem(
            order_id=order_id,
            menu_item_id=item_data.menu_item_id,
            quantity=item_data.quantity,
            unit_price=unit_price,
            special_instructions=item_data.special_instructions,
        )
        db.add(item)
        await db.flush()
        return item

    @staticmethod
    async def update_total(db: AsyncSession, order_id: uuid.UUID) -> Order:
        """Recalculate and update order total."""
        result = await db.execute(
            select(func.sum(OrderItem.unit_price * OrderItem.quantity))
            .where(OrderItem.order_id == order_id)
        )
        total = result.scalar() or 0
        
        order_result = await db.execute(select(Order).where(Order.id == order_id))
        order = order_result.scalar_one()
        order.total_price = total
        await db.flush()
        return order

    @staticmethod
    async def update(
        db: AsyncSession, order: Order, data: OrderUpdate
    ) -> Order:
        """Update an order."""
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(order, field, value)
        await db.commit()
        await db.refresh(order)
        return order

    @staticmethod
    async def delete(db: AsyncSession, order: Order) -> None:
        """Delete an order."""
        await db.delete(order)
        await db.commit()