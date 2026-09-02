"""Unit smoke test for the ABFINI RAG retrieval pipeline."""

from rag.retriever import retrieve_context


def fake_rpc(name, **kwargs):
    assert name == "semantic_search_document_chunks"
    assert len(kwargs["query_embedding"]) == 768
    return [
        {
            "id": "low",
            "document_id": "doc",
            "chunk_index": 2,
            "content": "low relevance",
            "metadata": {},
            "similarity": 0.30,
        },
        {
            "id": "high",
            "document_id": "doc",
            "chunk_index": 0,
            "content": "ABFINI est une couche de connaissance.",
            "metadata": {},
            "similarity": 0.92,
        },
    ]


def main() -> None:
    result = retrieve_context([0.0] * 768, fake_rpc, top_k=2, threshold=0.5)
    assert [item.id for item in result.results] == ["high"]
    assert "ABFINI est une couche de connaissance." in result.context
    assert "similarity=0.9200" in result.context
    print("RAG retriever test: PASS")


if __name__ == "__main__":
    main()
