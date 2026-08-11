# ═══════════════════════════════════════════════
# services/order_service.py — Order Business Logic
# ═══════════════════════════════════════════════

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.order_repo import OrderRepository
from app.repositories.menu_repo import MenuRepository
from app.repositories.restaurant_repo import RestaurantRepository
from app.schemas.order import OrderCreate, OrderUpdate, OrderResponse, OrderListResponse


class OrderService:
    @staticmethod
    async def get_order(db: AsyncSession, order_id: uuid.UUID) -> OrderResponse:
        order = await OrderRepository.get_by_id(db, order_id)
        if not order:
            raise ValueError("Order not found")
        return OrderResponse.model_validate(order)

    @staticmethod
    async def list_orders(
        db: AsyncSession,
        customer_id: uuid.UUID | None = None,
        restaurant_id: uuid.UUID | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> OrderListResponse:
        if customer_id:
            items, total = await OrderRepository.get_by_customer(db, customer_id, skip, limit)
        elif restaurant_id:
            items, total = await OrderRepository.get_by_restaurant(db, restaurant_id, skip, limit)
        else:
            items, total = await OrderRepository.get_all(db, skip, limit)
        return OrderListResponse(
            items=[OrderResponse.model_validate(i) for i in items],
            total=total,
        )

    @staticmethod
    async def create_order(db: AsyncSession, data: OrderCreate) -> OrderResponse:
        # 1. التحقق من المطعم
        restaurant = await RestaurantRepository.get_by_id(db, data.restaurant_id)
        if not restaurant:
            raise ValueError("Restaurant not found")

        # 2. إنشاء الـ Order (flush بدون commit)
        order = await OrderRepository.create(db, data)

        # 3. إضافة الـ Items مع التحقق من كل item
        for item_data in data.items:
            menu_item = await MenuRepository.get_by_id(db, item_data.menu_item_id)
            if not menu_item:
                raise ValueError(f"Menu item {item_data.menu_item_id} not found")
            if not menu_item.is_available:
                raise ValueError(f"Menu item {menu_item.name} is not available")
            await OrderRepository.add_item(db, order.id, item_data, float(menu_item.price))

        # 4. حساب الـ Total
        await OrderRepository.update_total(db, order.id)

        # 5. Commit كل حاجة مرة واحدة (Atomic)
        await db.commit()

        # ✅ الحل: بدل db.refresh — نعمل query جديد مع selectinload
        # db.refresh لا يحمل الـ relationships في Async SQLAlchemy
        order = await OrderRepository.get_by_id(db, order.id)

        return OrderResponse.model_validate(order)

    @staticmethod
    async def update_order(
        db: AsyncSession, order_id: uuid.UUID, data: OrderUpdate
    ) -> OrderResponse:
        order = await OrderRepository.get_by_id(db, order_id)
        if not order:
            raise ValueError("Order not found")
        updated = await OrderRepository.update(db, order, data)
        return OrderResponse.model_validate(updated)