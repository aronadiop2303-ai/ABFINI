"""Smoke tests for ABFINI semantic result ranking."""

from search.ranking import rank_results
from search.vector_search import SearchResult


def result(id: str, similarity: float, content: str = "content", chunk_index: int = 0):
    return SearchResult(
        id=id,
        document_id="doc",
        chunk_index=chunk_index,
        content=content,
        metadata={},
        similarity=similarity,
    )


def main() -> None:
    ranked = rank_results(
        [
            result("low", 0.20),
            result("high", 0.91),
            result("mid", 0.65),
            result("empty", 0.99, "   "),
        ],
        threshold=0.60,
        top_k=2,
    )

    assert [item.id for item in ranked] == ["high", "mid"]
    assert all(item.similarity >= 0.60 for item in ranked)
    assert len(ranked) == 2
    print("Ranking test: PASS")


if __name__ == "__main__":
    main()
