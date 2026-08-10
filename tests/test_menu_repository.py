"""Tests for menu_repository.py against the real sample DB (04-seed.sql loaded via scripts/setup_db.py).

These are integration tests, not unit tests with a mock DB - they assume `sttordering` exists locally
and is seeded. Run `python scripts/setup_db.py` first if they fail with "no such table"/empty results.
"""

import uuid

import pytest
from sqlalchemy import delete, select

from app.db.models import Category, MenuItem, Restaurant
from app.db.session import new_session
from app.repositories import menu_repository

KNOWN_ITEM_NAME_AR = "كشري وسط"
KNOWN_ITEM_PRICE = 50.0


@pytest.fixture
async def unavailable_item():
    """Seed data has no unavailable items, so this fixture inserts a throwaway one for the test."""
    async with new_session() as session:
        restaurant = (await session.execute(select(Restaurant).limit(1))).scalars().first()
        category = (
            (await session.execute(select(Category).where(Category.restaurant_id == restaurant.id).limit(1)))
            .scalars()
            .first()
        )

        item = MenuItem(
            id=uuid.uuid4(),
            external_id=f"TEST_UNAVAILABLE_{uuid.uuid4().hex[:8]}",
            restaurant_id=restaurant.id,
            category_id=category.id,
            name="Test Unavailable Item",
            price=9.99,
            currency="EGP",
            is_available=False,
            is_deleted=False,
        )
        session.add(item)
        await session.commit()
        item_id = item.id

    yield item_id

    async with new_session() as session:
        await session.execute(delete(MenuItem).where(MenuItem.id == item_id))
        await session.commit()


async def test_exact_match_returns_correct_item():
    item = await menu_repository.get_item_by_name(KNOWN_ITEM_NAME_AR)

    assert item is not None
    assert item.name == KNOWN_ITEM_NAME_AR
    assert item.price == KNOWN_ITEM_PRICE
    assert item.available is True


async def test_fuzzy_match_finds_close_item():
    # "كشري" alone is a substring of several items ("كشري وسط", "كشري صغير", ...) - should still resolve.
    item = await menu_repository.get_item_by_name("كشري")

    assert item is not None
    assert "كشري" in item.name


async def test_not_found_returns_none():
    item = await menu_repository.get_item_by_name("سوشي")

    assert item is None


async def test_search_items_suggests_close_alternatives_when_not_found():
    suggestions = await menu_repository.search_items("كشري", limit=3)

    assert len(suggestions) == 3
    assert all("كشري" in item.name for item in suggestions)


async def test_unavailable_item_reports_false(unavailable_item):
    assert await menu_repository.check_availability(unavailable_item) is False


async def test_available_item_reports_true():
    item = await menu_repository.get_item_by_name(KNOWN_ITEM_NAME_AR)

    assert await menu_repository.check_availability(item.id) is True


async def test_get_price_returns_db_price():
    item = await menu_repository.get_item_by_name(KNOWN_ITEM_NAME_AR)

    price = await menu_repository.get_price(item.id)

    assert price == KNOWN_ITEM_PRICE
