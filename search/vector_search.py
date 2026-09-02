"""Vector-search client contract for ABFINI V0.1."""
from dataclasses import dataclass
from typing import Any, Callable, Sequence


EMBEDDING_DIMENSIONS = 768
RPC_NAME = "semantic_search_document_chunks"


@dataclass(frozen=True)
class SearchResult:
    id: str
    document_id: str
    chunk_index: int
    content: str
    metadata: dict[str, Any]
    similarity: float


def search_chunks(
    query_embedding: Sequence[float],
    rpc: Callable[..., list[dict[str, Any]]],
    *,
    limit: int = 5,
    threshold: float = 0.0,
) -> list[SearchResult]:
    """Call the unambiguous semantic-search RPC and normalize results."""
    if len(query_embedding) != EMBEDDING_DIMENSIONS:
        raise ValueError(
            f"query_embedding must contain exactly {EMBEDDING_DIMENSIONS} values"
        )
    if limit < 1:
        raise ValueError("limit must be >= 1")
    if not 0.0 <= threshold <= 1.0:
        raise ValueError("threshold must be between 0.0 and 1.0")

    rows = rpc(
        RPC_NAME,
        query_embedding=list(query_embedding),
        match_count=limit,
        match_threshold=threshold,
    )
    return [
        SearchResult(
            id=str(row["id"]),
            document_id=str(row["document_id"]),
            chunk_index=int(row["chunk_index"]),
            content=str(row["content"]),
            metadata=dict(row.get("metadata") or {}),
            similarity=float(row["similarity"]),
        )
        for row in rows
    ]
