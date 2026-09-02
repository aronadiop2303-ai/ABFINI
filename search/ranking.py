"""Ranking and filtering for ABFINI semantic-search results."""
from typing import Sequence

from .vector_search import SearchResult


def rank_results(
    results: Sequence[SearchResult],
    *,
    threshold: float = 0.0,
    top_k: int = 5,
) -> list[SearchResult]:
    """Filter by similarity and return the strongest results first."""
    if not 0.0 <= threshold <= 1.0:
        raise ValueError("threshold must be between 0.0 and 1.0")
    if top_k < 1:
        raise ValueError("top_k must be >= 1")

    filtered = [
        result
        for result in results
        if result.content.strip() and threshold <= result.similarity <= 1.0
    ]
    return sorted(
        filtered,
        key=lambda result: (-result.similarity, result.chunk_index, result.id),
    )[:top_k]
