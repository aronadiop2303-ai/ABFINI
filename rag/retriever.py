"""RAG retrieval orchestration for ABFINI V0.1."""
from dataclasses import dataclass
from typing import Sequence

from search.vector_search import SearchResult, search_chunks


@dataclass(frozen=True)
class RetrievedContext:
    results: list[SearchResult]
    context: str


def build_context(results: Sequence[SearchResult], max_chars: int = 12000) -> str:
    """Build bounded, source-labelled context from semantic-search results."""
    if max_chars < 1:
        raise ValueError("max_chars must be >= 1")
    blocks: list[str] = []
    total = 0
    for index, result in enumerate(results, 1):
        block = (
            f"[Source {index} | document={result.document_id} "
            f"| chunk={result.chunk_index} | similarity={result.similarity:.4f}]\n"
            f"{result.content.strip()}"
        )
        if not result.content.strip():
            continue
        separator = "\n\n" if blocks else ""
        remaining = max_chars - total - len(separator)
        if remaining <= 0:
            break
        if len(block) > remaining:
            block = block[:remaining].rstrip()
        blocks.append(block)
        total += len(separator) + len(block)
        if total >= max_chars:
            break
    return "\n\n".join(blocks)


def retrieve_context(query_embedding: Sequence[float], rpc, *, top_k: int = 5, threshold: float = 0.0, max_chars: int = 12000) -> RetrievedContext:
    """Retrieve relevant chunks and construct bounded RAG context."""
    results = search_chunks(query_embedding, rpc, limit=top_k, threshold=threshold)
    return RetrievedContext(results=list(results), context=build_context(results, max_chars=max_chars))
