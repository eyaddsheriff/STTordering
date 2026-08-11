# ═══════════════════════════════════════════════
# repositories/customer_repo.py — Customer CRUD
# ═══════════════════════════════════════════════

import uuid
from typing import List, Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.customer import Customer
from app.models.customer_preference import CustomerPreference
from app.schemas.customer import CustomerCreate, CustomerUpdate
from app.schemas.customer_preference import CustomerPreferenceCreate, CustomerPreferenceUpdate


class CustomerRepository:
    @staticmethod
    async def get_by_id(db: AsyncSession, customer_id: uuid.UUID) -> Optional[Customer]:
        result = await db.execute(select(Customer).where(Customer.id == customer_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_phone(db: AsyncSession, phone: str) -> Optional[Customer]:
        result = await db.execute(select(Customer).where(Customer.phone == phone))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_all(db: AsyncSession, skip: int = 0, limit: int = 100) -> tuple[List[Customer], int]:
        query = select(Customer)
        count_query = select(func.count()).select_from(Customer)
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        result = await db.execute(query.offset(skip).limit(limit))
        return list(result.scalars().all()), total

    @staticmethod
    async def create(db: AsyncSession, data: CustomerCreate) -> Customer:
        customer = Customer(**data.model_dump())
        db.add(customer)
        await db.commit()
        await db.refresh(customer)
        return customer

    @staticmethod
    async def update(db: AsyncSession, customer: Customer, data: CustomerUpdate) -> Customer:
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(customer, field, value)
        await db.commit()
        await db.refresh(customer)
        return customer

    @staticmethod
    async def delete(db: AsyncSession, customer: Customer) -> None:
        await db.delete(customer)
        await db.commit()

    @staticmethod
    async def get_preferences(db: AsyncSession, customer_id: uuid.UUID) -> Optional[CustomerPreference]:
        result = await db.execute(select(CustomerPreference).where(CustomerPreference.customer_id == customer_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def create_preferences(db: AsyncSession, data: CustomerPreferenceCreate) -> CustomerPreference:
        prefs = CustomerPreference(**data.model_dump())
        db.add(prefs)
        await db.commit()
        await db.refresh(prefs)
        return prefs

    @staticmethod
    async def update_preferences(db: AsyncSession, prefs: CustomerPreference, data: CustomerPreferenceUpdate) -> CustomerPreference:
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(prefs, field, value)
        await db.commit()
        await db.refresh(prefs)
        return prefs