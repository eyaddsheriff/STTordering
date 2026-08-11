"""Generate BGE-M3 embeddings for every menu item and upsert them into menu_embeddings.

Run after any menu change (new items, renames, description edits):
    .venv/Scripts/python.exe scripts/generate_embeddings.py

Embeds "name + description + ingredients" rather than the name alone, so a query like
"something spicy with chicken" can match on descriptive text the name never mentions.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select  # noqa: E402
from sqlalchemy.dialects.postgresql import insert  # noqa: E402

from app.db.models import MenuEmbedding, MenuItem  # noqa: E402
from app.db.session import new_session  # noqa: E402
from app.services.embeddings import MODEL_NAME, embed_batch  # noqa: E402


def _embedding_text(item: MenuItem) -> str:
    parts = [item.name, item.description or ""]
    if item.ingredients:
        parts.append(" ".join(str(i) for i in item.ingredients))
    return " ".join(p for p in parts if p).strip()


async def main() -> None:
    async with new_session() as session:
        result = await session.execute(select(MenuItem).where(MenuItem.is_deleted.is_(False)))
        items = list(result.scalars().all())

    if not items:
        print("No menu items found - nothing to embed.")
        return

    print(f"Embedding {len(items)} menu items with {MODEL_NAME} via Ollama...")
    vectors = embed_batch([_embedding_text(item) for item in items])

    async with new_session() as session:
        for item, vector in zip(items, vectors):
            stmt = insert(MenuEmbedding).values(
                menu_item_id=item.id, embedding=vector, embedding_model=MODEL_NAME
            )
            # Re-running the script should refresh existing rows, not fail on the primary key.
            stmt = stmt.on_conflict_do_update(
                index_elements=[MenuEmbedding.menu_item_id],
                set_={"embedding": vector, "embedding_model": MODEL_NAME},
            )
            await session.execute(stmt)
        await session.commit()

    print(f"Done. {len(items)} embeddings written to menu_embeddings.")


if __name__ == "__main__":
    asyncio.run(main())
