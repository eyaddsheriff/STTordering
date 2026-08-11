"""BGE-M3 embedding generation for the pgvector semantic menu search (Phase 2).

BGE-M3 is multilingual, which is the whole reason the proposal picked it: it maps Arabic, English,
and transliterated text ("كشري" / "koshari" / "Kishari") into the same vector space, which the old
difflib character-overlap matching fundamentally could not do.

The model is loaded lazily and cached - it's ~2.2GB, so importing this module must stay cheap for
tests and for the API's startup path.
"""

from functools import lru_cache

from sentence_transformers import SentenceTransformer

MODEL_NAME = "BAAI/bge-m3"
EMBEDDING_DIM = 1024


@lru_cache(maxsize=1)
def _model() -> SentenceTransformer:
    return SentenceTransformer(MODEL_NAME)


def embed(text: str) -> list[float]:
    return embed_batch([text])[0]


def embed_batch(texts: list[str]) -> list[list[float]]:
    # normalize_embeddings=True makes cosine distance equivalent to a dot product, which is what
    # the HNSW index (vector_cosine_ops) in the schema is built for.
    vectors = _model().encode(texts, normalize_embeddings=True, show_progress_bar=False)
    return [v.tolist() for v in vectors]
