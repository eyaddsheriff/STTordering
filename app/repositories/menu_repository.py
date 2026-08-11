"""All DB access for menu data lives here - no raw SQL/ORM queries in the agent code.

Matching strategy: `search_items` tries pgvector/BGE-M3 semantic similarity first, and falls back to
the older ILIKE-substring + difflib closeness ranking when embeddings aren't populated (or the query
is empty). The semantic path handles things character matching fundamentally cannot - transliteration
("koshari" vs "كشري"), synonyms, and descriptive queries ("something spicy") - while the fallback
keeps the system working on a fresh DB before scripts/generate_embeddings.py has been run.
"""

import difflib
import uuid
from dataclasses import dataclass

from sqlalchemy import select

from app.db.models import MenuEmbedding, MenuItem
from app.db.session import new_session

# 0.4 was dangerously loose for Arabic: completely unrelated phrases (e.g. "آيس كريم فراولة" /
# strawberry ice cream, not on the menu at all) scored ~0.43 against real items purely from
# incidental shared letters (Arabic's smaller alphabet makes character-level overlap common even
# between unrelated words), and were silently accepted as a match - the customer would be told
# their order was added when it had actually been silently swapped for something else. 0.6 was
# tested to reject unrelated phrases (max observed ~0.44) while still tolerating real typos/
# misspellings (min observed ~0.80, e.g. "كسري وسط" -> "كشري وسط").
_FUZZY_MATCH_THRESHOLD = 0.6

# Cosine distance cutoff for the semantic path (0 = identical, 2 = opposite). Serves the same safety
# purpose as _FUZZY_MATCH_THRESHOLD: an off-menu request ("strawberry ice cream") must return no
# match rather than the nearest food-ish item, so the agent tells the customer it isn't available
# instead of silently substituting something. Tuned against the seeded menu - see
# tests/test_semantic_search.py, which pins both the "real paraphrase matches" and the
# "off-menu item does NOT match" sides of this boundary.
_SEMANTIC_DISTANCE_THRESHOLD = 0.45


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


async def _semantic_search(query: str, limit: int) -> list[MenuItemRow] | None:
    """pgvector cosine-similarity search. Returns None when embeddings aren't populated yet, so the
    caller can fall back to string matching rather than silently returning no results.
    """
    async with new_session() as session:
        has_embeddings = await session.scalar(select(MenuEmbedding.menu_item_id).limit(1))
        if has_embeddings is None:
            return None

        # Imported here, after the check: pulling in sentence-transformers is slow, and there's no
        # reason to pay for it on a DB that hasn't had generate_embeddings.py run against it.
        from app.services.embeddings import embed

        query_vector = embed(query)
        distance = MenuEmbedding.embedding.cosine_distance(query_vector)
        result = await session.execute(
            select(MenuItem, distance)
            .join(MenuEmbedding, MenuEmbedding.menu_item_id == MenuItem.id)
            .where(MenuItem.is_deleted.is_(False))
            .where(distance < _SEMANTIC_DISTANCE_THRESHOLD)
            .order_by(distance)
            .limit(limit)
        )
        return [_to_row(item) for item, _distance in result.all()]


async def search_items(query: str, limit: int = 5) -> list[MenuItemRow]:
    """Search available-or-not menu items by name. Empty query returns the full menu (up to limit)."""
    async with new_session() as session:
        result = await session.execute(
            select(MenuItem).where(MenuItem.is_deleted.is_(False)).order_by(MenuItem.name)
        )
        all_items = result.scalars().all()

    if not query:
        return [_to_row(item) for item in all_items[:limit]]

    semantic_hits = await _semantic_search(query, limit)
    if semantic_hits is not None:
        return semantic_hits

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
