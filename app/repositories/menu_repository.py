"""All DB access for menu data lives here - no raw SQL/ORM queries in the agent code.

Matching strategy note: `search_items`/`get_item_by_name` use ILIKE substring matching plus a
difflib closeness ranking. This is a placeholder for the real semantic search planned in CLAUDE_1.md
(PostgreSQL + pgvector with BGE-M3 embeddings, Phase 2). It's "good enough" to survive near-misses
like "burger" vs "Classic Cheeseburger" or minor mis-transcriptions, but it is NOT semantic search -
rip this matching logic out when pgvector lands and replace it with an embedding similarity query.
"""

import difflib
import uuid
from dataclasses import dataclass

from sqlalchemy import select

from app.db.models import MenuItem
from app.db.session import new_session

_FUZZY_MATCH_THRESHOLD = 0.4


@dataclass
class MenuItemRow:
    id: uuid.UUID
    name: str
    price: float
    available: bool
    category_id: uuid.UUID


def _to_row(item: MenuItem) -> MenuItemRow:
    return MenuItemRow(
        id=item.id,
        name=item.name,
        price=float(item.price),
        available=item.is_available,
        category_id=item.category_id,
    )


async def search_items(query: str, limit: int = 5) -> list[MenuItemRow]:
    """Search available-or-not menu items by name. Empty query returns the full menu (up to limit)."""
    async with new_session() as session:
        result = await session.execute(
            select(MenuItem).where(MenuItem.is_deleted.is_(False)).order_by(MenuItem.name)
        )
        all_items = result.scalars().all()

    if not query:
        return [_to_row(item) for item in all_items[:limit]]

    query_lower = query.lower().strip()
    substring_hits = [item for item in all_items if query_lower in item.name.lower()]
    candidates = substring_hits if substring_hits else all_items

    def closeness(item: MenuItem) -> float:
        return difflib.SequenceMatcher(None, query_lower, item.name.lower()).ratio()

    ranked = sorted(candidates, key=closeness, reverse=True)

    if not substring_hits:
        # No item even contains the query as a substring - only keep genuinely close matches
        # instead of returning the whole menu as "close enough".
        ranked = [item for item in ranked if closeness(item) > _FUZZY_MATCH_THRESHOLD]

    return [_to_row(item) for item in ranked[:limit]]


async def get_item_by_name(name: str) -> MenuItemRow | None:
    matches = await search_items(name, limit=1)
    return matches[0] if matches else None


async def check_availability(item_id: uuid.UUID) -> bool:
    async with new_session() as session:
        item = await session.get(MenuItem, item_id)
    return bool(item and item.is_available and not item.is_deleted)


async def get_price(item_id: uuid.UUID, variant: str | None = None) -> float | None:
    if variant is not None:
        # This sample schema has no has_variant/variant concept (flagged separately) - the parameter
        # is accepted for forward compatibility with the variant design in CLAUDE_1.md, but it's
        # currently a no-op: there's nothing to select a variant *from*.
        pass

    async with new_session() as session:
        item = await session.get(MenuItem, item_id)
    return float(item.price) if item and item.price is not None else None
