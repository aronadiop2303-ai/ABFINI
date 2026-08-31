"""Vector-search client contract for ABFINI V0.1."""
from dataclasses import dataclass
from typing import Any, Callable, Sequence


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
    """Call ABFINI's match_document_chunks RPC and normalize results."""
    if len(query_embedding) != 1536:
        raise ValueError("query_embedding must contain exactly 1536 values")
    if limit < 1:
        raise ValueError("limit must be >= 1")

    rows = rpc(
        "match_document_chunks",
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
