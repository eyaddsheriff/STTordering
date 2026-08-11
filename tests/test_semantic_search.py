"""Tests for the pgvector/BGE-M3 semantic search path in menu_repository.

Requires embeddings to be populated (scripts/generate_embeddings.py); every test skips if
menu_embeddings is empty, so the suite still passes on a fresh DB using the lexical fallback.

The point of these tests is the *boundary*, not just the happy path. Measurement showed no single
distance threshold can separate "same dish" from "different but related dish" - e.g. off-menu
سمك مشوي sits at 0.4897 while on-menu transliterated "koshari" sits at 0.6151 - so identity and
suggestion use different cutoffs. These tests pin both sides of that split.
"""

import pytest
from sqlalchemy import func, select

from app.db.models import MenuEmbedding
from app.db.session import new_session
from app.repositories import menu_repository


@pytest.fixture(autouse=True)
async def require_embeddings():
    async with new_session() as session:
        count = await session.scalar(select(func.count()).select_from(MenuEmbedding))
    if not count:
        pytest.skip("menu_embeddings is empty - run scripts/generate_embeddings.py")


async def test_transliteration_is_suggested():
    """The whole reason for embeddings: difflib cannot connect Latin "koshari" to Arabic كشري,
    because they share no characters at all.
    """
    suggestions = await menu_repository.search_items("koshari", limit=5)

    assert any("كشري" in item.name for item in suggestions), (
        f"expected a koshari item among suggestions, got {[i.name for i in suggestions]}"
    )


async def test_english_query_finds_arabic_item():
    suggestions = await menu_repository.search_items("grilled chicken", limit=5)

    assert any("فراخ" in item.name for item in suggestions), (
        f"expected a chicken item among suggestions, got {[i.name for i in suggestions]}"
    )


async def test_off_menu_item_is_never_resolved_as_identity():
    """The core safety property. These must not resolve to *some* item just because the menu has
    something vaguely related - the customer must be told we don't have it.

    سمك مشوي is the important case: grilled fish is genuinely semantically close to grilled kebab
    (0.4897), closer than some real matches, which is exactly why identity uses a strict cutoff
    instead of the wider suggestion band.
    """
    for off_menu in ("آيس كريم فراولة", "بيتزا", "سوشي", "تاكو", "برجر", "سمك مشوي", "باستا", "pizza"):
        item = await menu_repository.get_item_by_name(off_menu)
        assert item is None, f"{off_menu!r} is not on the menu but resolved to {item}"


async def test_real_items_still_resolve_with_embeddings_active():
    """Guards against the opposite failure: a threshold tight enough to be safe must still let
    genuine orders through, including a typo.
    """
    for query, expected in (("كشري كبير", "كشري كبير"), ("كسري وسط", "كشري وسط"), ("حمص", "حمص")):
        item = await menu_repository.get_item_by_name(query)
        assert item is not None, f"{query!r} should have resolved to {expected!r}"
        assert item.name == expected


async def test_falls_back_to_lexical_when_embeddings_missing(monkeypatch):
    """A checkout on a fresh machine has no embeddings until generate_embeddings.py is run, and the
    agent must still work there - degraded (no transliteration, and the سمك مشوي false positive
    above comes back, since difflib alone cannot see the difference) but functional.
    """

    async def no_embeddings(*_args, **_kwargs):
        return None

    monkeypatch.setattr(menu_repository, "_semantic_search", no_embeddings)

    item = await menu_repository.get_item_by_name("كشري وسط")
    assert item is not None and item.name == "كشري وسط"
    assert await menu_repository.get_item_by_name("آيس كريم فراولة") is None


async def test_suggestions_are_wider_than_identity():
    """A near-miss should produce something to offer the customer even when it is correctly
    refused as an identity match - that's what lets the agent say "we don't have X, but we have Y"
    instead of a bare "no".
    """
    assert await menu_repository.get_item_by_name("سمك مشوي") is None
    assert await menu_repository.search_items("سمك مشوي", limit=3), "expected alternatives to offer"
