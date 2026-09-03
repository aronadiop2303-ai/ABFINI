"""Deterministic unit test for the complete ABFINI RAG pipeline."""
from dataclasses import dataclass

from models.provider import GenerationRequest, GenerationResult
from rag.pipeline import answer_question


@dataclass
class FakeEmbeddingProvider:
    model: str = "fake-embedding"
    dimensions: int = 768

    def embed_query(self, text: str) -> list[float]:
        assert text == "Qu'est-ce qu'ABFINI ?"
        return [1.0] + [0.0] * 767


@dataclass
class FakeGenerationProvider:
    model: str = "fake-generator"

    def generate(self, request: GenerationRequest) -> GenerationResult:
        assert "ABFINI est une couche de connaissance" in request.context
        assert request.question == "Qu'est-ce qu'ABFINI ?"
        return GenerationResult(
            answer="ABFINI est une couche de connaissance destinée à fournir un contexte exploitable.",
            model=self.model,
        )


def fake_rpc(function_name, *, query_embedding, **kwargs):
    assert function_name == "semantic_search_document_chunks"
    assert len(query_embedding) == 768
    assert kwargs["match_count"] == 5
    assert kwargs["match_threshold"] == 0.0
    return [
        {
            "id": "chunk-1",
            "document_id": "doc-1",
            "chunk_index": 0,
            "content": "ABFINI est une couche de connaissance destinée à fournir un contexte exploitable.",
            "metadata": {"source": "test"},
            "similarity": 0.95,
        }
    ]


def test_full_rag_pipeline():
    result = answer_question(
        "Qu'est-ce qu'ABFINI ?",
        FakeEmbeddingProvider(),
        FakeGenerationProvider(),
        fake_rpc,
    )
    assert result.answer.startswith("ABFINI est une couche")
    assert result.model == "fake-generator"
    assert result.retrieved.results
    print("Full RAG pipeline test: PASS")


if __name__ == "__main__":
    test_full_rag_pipeline()
