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

# Two cutoffs, not one, because measurement showed a single global threshold CANNOT separate
# "same dish" from "different but related dish" (cosine distance: 0 = identical, 2 = opposite).
# Measured against the seeded menu:
#     سمك مشوي  (grilled fish, NOT on the menu) -> 0.4897 from كباب مشوي
#     koshari   (transliteration, IS on the menu) -> 0.6151 from كشري سوبريم
# The off-menu item is *closer* than a real match, so any single threshold either rejects real
# orders or accepts off-menu ones. That's inherent: embeddings measure relatedness, and grilled
# fish genuinely is related to grilled kebab - it's just not the same dish, which is what ordering
# actually needs to know.
#
# So: only a strong match may silently resolve to an item (identity), while the wider band is
# treated as "did you mean...?" material the agent asks about (suggestions). Nothing in the wider
# band is ever added to an order on its own.
_SEMANTIC_IDENTITY_DISTANCE = 0.40  # auto-accept as "this is the item"; measured margin to the
# nearest off-menu item (0.4897) is ~0.09
_SEMANTIC_SUGGEST_DISTANCE = 0.65  # only offered as a suggestion for the agent to confirm


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


async def _all_items() -> list[MenuItem]:
    async with new_session() as session:
        result = await session.execute(
            select(MenuItem).where(MenuItem.is_deleted.is_(False)).order_by(MenuItem.name)
        )
        return list(result.scalars().all())


def _closeness(query: str, item: MenuItem) -> float:
    return difflib.SequenceMatcher(None, query.lower().strip(), item.name.lower()).ratio()


def _substring_hits(all_items: list[MenuItem], query: str) -> list[MenuItemRow]:
    """Items whose name literally contains the query. The strongest evidence available: the
    customer said characters that actually appear in the item's name.
    """
    query_lower = query.lower().strip()
    hits = [item for item in all_items if query_lower in item.name.lower()]
    return [_to_row(item) for item in sorted(hits, key=lambda i: _closeness(query, i), reverse=True)]


def _fuzzy_hits(all_items: list[MenuItem], query: str) -> list[MenuItemRow]:
    """Items close enough by character overlap to be a plausible typo/mis-transcription.

    Weak evidence on its own - see the caller in get_item_by_name for why this is not sufficient
    to identify an item when embeddings are available.
    """
    ranked = sorted(all_items, key=lambda i: _closeness(query, i), reverse=True)
    return [_to_row(i) for i in ranked if _closeness(query, i) > _FUZZY_MATCH_THRESHOLD]


def _lexical_search(all_items: list[MenuItem], query: str, limit: int) -> list[MenuItemRow]:
    """ILIKE-substring first, falling back to difflib closeness. Blind to transliteration and
    synonyms - that's what the semantic path is for.
    """
    hits = _substring_hits(all_items, query) or _fuzzy_hits(all_items, query)
    return hits[:limit]


async def _semantic_search(query: str, limit: int, max_distance: float) -> list[MenuItemRow] | None:
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

        distance = MenuEmbedding.embedding.cosine_distance(embed(query))
        result = await session.execute(
            select(MenuItem, distance)
            .join(MenuEmbedding, MenuEmbedding.menu_item_id == MenuItem.id)
            .where(MenuItem.is_deleted.is_(False))
            .where(distance < max_distance)
            .order_by(distance)
            .limit(limit)
        )
        return [_to_row(item) for item, _distance in result.all()]


async def search_items(query: str, limit: int = 5) -> list[MenuItemRow]:
    """Find candidate items to *offer* the customer - "did you mean...?" suggestions and browsing.

    Deliberately wider than get_item_by_name: results here are things the agent mentions, never
    things it silently adds to an order. Empty query returns the full menu (up to limit).
    """
    all_items = await _all_items()
    if not query:
        return [_to_row(item) for item in all_items[:limit]]

    results = _lexical_search(all_items, query, limit)

    # Semantic hits widen recall (transliteration, synonyms, "something sweet"), but go *after*
    # lexical ones: if the customer's actual letters appear in an item name, that's the better bet.
    semantic = await _semantic_search(query, limit, _SEMANTIC_SUGGEST_DISTANCE)
    if semantic:
        seen = {row.id for row in results}
        results.extend(row for row in semantic if row.id not in seen)

    return results[:limit]


async def get_item_by_name(name: str) -> MenuItemRow | None:
    """Resolve a spoken item name to exactly one menu item, or None.

    This is the order-validation gate, so it is intentionally stricter than search_items: it must
    return None for anything not actually on the menu rather than the nearest lookalike, because a
    false positive here means the customer is charged for a dish they never asked for.
    """
    all_items = await _all_items()

    # 1. The query literally appears in the item name - accept.
    substring = _substring_hits(all_items, name)
    if substring:
        return substring[0]

    semantic = await _semantic_search(name, limit=1, max_distance=_SEMANTIC_IDENTITY_DISTANCE)
    fuzzy = _fuzzy_hits(all_items, name)

    # 2. No embeddings yet -> difflib alone, the pre-pgvector behaviour.
    if semantic is None:
        return fuzzy[0] if fuzzy else None

    # 3. Both signals available, so require them to AGREE before treating a mere character-overlap
    #    hit as identity. They fail in different ways, which is exactly why the combination is
    #    safer than either alone: "سمك مشوي" (grilled fish, not on the menu) scores 0.7059 against
    #    "كباب مشوي" on difflib - well past the 0.6 bar - purely because both end in "مشوي", and
    #    would otherwise be silently sold as grilled kebab. Embeddings correctly place it at 0.4897,
    #    outside the identity band, and veto the match. Raising the difflib threshold instead was
    #    not viable: it would have to fit between 0.7059 and a real typo at 0.8750.
    if fuzzy and semantic and fuzzy[0].id == semantic[0].id:
        return fuzzy[0]

    # 4. A confident semantic match with no lexical support is still trustworthy - it cleared the
    #    strict identity distance, which off-menu items measurably do not.
    return semantic[0] if semantic else None


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
