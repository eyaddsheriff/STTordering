import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Ollama loads bge-m3 into VRAM on first use. Left to happen naturally, the first customer of
    # the day pays that wait on their first sentence; touching it here moves the cost to startup.
    # Skipped silently if embeddings aren't populated - the agent falls back to lexical matching
    # and never calls the model.
    async def warm_embeddings() -> None:
        from sqlalchemy import select

        from app.db.models import MenuEmbedding
        from app.db.session import new_session

        async with new_session() as session:
            if await session.scalar(select(MenuEmbedding.menu_item_id).limit(1)) is None:
                return

        from app.services.embeddings import embed

        await asyncio.to_thread(embed, "warmup")

    # Don't block the port opening on this - the server should accept requests immediately, and a
    # request arriving mid-warmup just waits on the same cached model.
    asyncio.create_task(warm_embeddings())
    yield


app = FastAPI(title="STT Ordering Assistant", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
