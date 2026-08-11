# ═══════════════════════════════════════════════
# services/customer_service.py — Customer Business Logic
# ═══════════════════════════════════════════════

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.customer_repo import CustomerRepository
from app.schemas.customer import CustomerCreate, CustomerUpdate, CustomerResponse
from app.schemas.customer_preference import CustomerPreferenceUpdate, CustomerPreferenceResponse, CustomerPreferenceCreate


class CustomerService:
    @staticmethod
    async def get_customer(db: AsyncSession, customer_id: uuid.UUID) -> CustomerResponse:
        customer = await CustomerRepository.get_by_id(db, customer_id)
        if not customer:
            raise ValueError("Customer not found")
        return CustomerResponse.model_validate(customer)

    @staticmethod
    async def get_customer_by_phone(db: AsyncSession, phone: str) -> CustomerResponse | None:
        customer = await CustomerRepository.get_by_phone(db, phone)
        if not customer:
            return None
        return CustomerResponse.model_validate(customer)

    @staticmethod
    async def create_customer(db: AsyncSession, data: CustomerCreate) -> CustomerResponse:
        existing = await CustomerRepository.get_by_phone(db, data.phone)
        if existing:
            raise ValueError("Customer with this phone already exists")
        customer = await CustomerRepository.create(db, data)
        return CustomerResponse.model_validate(customer)

    @staticmethod
    async def update_customer(db: AsyncSession, customer_id: uuid.UUID, data: CustomerUpdate) -> CustomerResponse:
        customer = await CustomerRepository.get_by_id(db, customer_id)
        if not customer:
            raise ValueError("Customer not found")
        updated = await CustomerRepository.update(db, customer, data)
        return CustomerResponse.model_validate(updated)

    @staticmethod
    async def get_preferences(db: AsyncSession, customer_id: uuid.UUID) -> CustomerPreferenceResponse | None:
        prefs = await CustomerRepository.get_preferences(db, customer_id)
        if not prefs:
            return None
        return CustomerPreferenceResponse.model_validate(prefs)

    @staticmethod
    async def create_or_update_preferences(db: AsyncSession, customer_id: uuid.UUID, data: CustomerPreferenceUpdate) -> CustomerPreferenceResponse:
        prefs = await CustomerRepository.get_preferences(db, customer_id)
        if prefs:
            updated = await CustomerRepository.update_preferences(db, prefs, data)
        else:
            create_data = CustomerPreferenceCreate(customer_id=customer_id, **data.model_dump(exclude_unset=True))
            updated = await CustomerRepository.create_preferences(db, create_data)
        return CustomerPreferenceResponse.model_validate(updated)