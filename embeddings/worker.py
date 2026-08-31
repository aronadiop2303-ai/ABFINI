"""Embedding worker primitives.

The worker only consumes chunks and a provider. Database wiring is kept out
of the provider so Supabase/PostgreSQL can be replaced or tested separately.
"""
from dataclasses import dataclass

from .provider import EmbeddingProvider


@dataclass(frozen=True)
class ChunkForEmbedding:
    chunk_id: str
    content: str


def embed_chunks(
    chunks: list[ChunkForEmbedding], provider: EmbeddingProvider
) -> list[tuple[str, list[float]]]:
    pending = [chunk for chunk in chunks if chunk.content.strip()]
    if not pending:
        return []

    vectors = provider.embed([chunk.content for chunk in pending])
    if len(vectors) != len(pending):
        raise RuntimeError("Embedding provider returned an unexpected number of vectors")

    for vector in vectors:
        if len(vector) != provider.dimension:
            raise RuntimeError("Embedding provider returned an invalid vector dimension")

    return [(chunk.chunk_id, vector) for chunk, vector in zip(pending, vectors)]
