"""BGE-M3 embedding generation for the pgvector semantic menu search (Phase 2).

BGE-M3 is multilingual, which is the whole reason the proposal picked it: it maps Arabic, English,
and transliterated text ("كشري" / "koshari") into the same vector space, which the difflib
character-overlap matching fundamentally cannot do.

Served through Ollama rather than loading sentence-transformers in-process. On a 16GB machine that
also runs Whisper and a 7B chat model, holding another ~2.2GB resident here starved Ollama of the
memory it needed to start its own runner (it died with GGML_ASSERT(ctx->mem_buffer != NULL), an
out-of-memory failure). Ollama already owns model lifecycle - it loads on demand, shares the GPU,
and unloads when idle - so letting it host this model too removes the contention rather than just
shifting it around. It also keeps torch out of the API process entirely.

Ollama returns L2-normalized vectors, so cosine distance is what the HNSW index
(vector_cosine_ops) in the schema expects, with no extra normalization step here.
"""

import httpx

from app.config import settings

MODEL_NAME = "bge-m3"
EMBEDDING_DIM = 1024

# Cold-start on this model is slow (Ollama has to load it into VRAM), and generate_embeddings.py
# sends the whole menu in one call.
_TIMEOUT_SECONDS = 300


def _embed_url() -> str:
    # settings.ollama_base_url points at the OpenAI-compatible path (".../v1"); the native embed
    # endpoint sits alongside it.
    return settings.ollama_base_url.rstrip("/").removesuffix("/v1") + "/api/embed"


def embed(text: str) -> list[float]:
    return embed_batch([text])[0]


def embed_batch(texts: list[str]) -> list[list[float]]:
    response = httpx.post(
        _embed_url(),
        json={"model": MODEL_NAME, "input": texts},
        timeout=_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    return response.json()["embeddings"]
