"""Embedding worker primitives with strict provider/result validation."""
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

    result = provider.embed([chunk.content for chunk in pending])
    if len(result.vectors) != len(pending):
        raise RuntimeError("Embedding provider returned an unexpected number of vectors")
    if result.dimensions != provider.dimensions:
        raise RuntimeError("Embedding result dimensions do not match provider")

    for vector in result.vectors:
        if len(vector) != provider.dimensions:
            raise RuntimeError("Embedding provider returned an invalid vector dimension")

    return [(chunk.chunk_id, vector) for chunk, vector in zip(pending, result.vectors)]
