"""Deterministic unit test for the complete ABFINI RAG pipeline.

Kept pytest-free on purpose: the "full-rag" CI job runs this file as a
plain script (``python -m rag.test_pipeline``) without pytest installed.
"""
from dataclasses import dataclass

from models.provider import GenerationRequest, GenerationResult
from observability.metrics import RequestMetrics
from rag.errors import (
    EmbeddingFailedError,
    GenerationFailedError,
    InvalidQuestionError,
    NoRelevantKnowledgeError,
    RetrievalFailedError,
)
from rag.pipeline import answer_question


def assert_raises(exc_type, fn):
    try:
        fn()
    except exc_type as exc:
        return exc
    raise AssertionError(f"expected {exc_type.__name__} to be raised")


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


def test_full_rag_pipeline_populates_metrics():
    metrics = RequestMetrics(request_id="req-test")
    result = answer_question(
        "Qu'est-ce qu'ABFINI ?",
        FakeEmbeddingProvider(),
        FakeGenerationProvider(),
        fake_rpc,
        metrics=metrics,
    )
    assert metrics.embedding_ms is not None
    assert metrics.retrieval_ms is not None
    assert metrics.generation_ms is not None
    assert metrics.retrieval_results == len(result.retrieved.results) == 1
    assert metrics.top_similarity == 0.95
    assert metrics.model == "fake-generator"
    # answer_question does not call finish(): only the caller knows the
    # final status, so total_ms/status remain untouched until it does.
    assert metrics.total_ms is None
    assert metrics.status == "in_progress"


def test_answer_question_raises_invalid_question_error_on_empty_question():
    assert_raises(
        InvalidQuestionError,
        lambda: answer_question("   ", FakeEmbeddingProvider(), FakeGenerationProvider(), fake_rpc),
    )


def rpc_returning_nothing(function_name, *, query_embedding, **kwargs):
    return []


def test_answer_question_raises_no_relevant_knowledge_error_with_no_candidates():
    exc = assert_raises(
        NoRelevantKnowledgeError,
        lambda: answer_question(
            "Qu'est-ce qu'ABFINI ?",
            FakeEmbeddingProvider(),
            FakeGenerationProvider(),
            rpc_returning_nothing,
        ),
    )
    assert exc.reason == "no_candidates"


def rpc_returning_low_similarity(function_name, *, query_embedding, **kwargs):
    return [
        {
            "id": "chunk-1",
            "document_id": "doc-1",
            "chunk_index": 0,
            "content": "hors sujet",
            "metadata": {},
            "similarity": 0.01,
        }
    ]


def test_answer_question_raises_no_relevant_knowledge_error_below_threshold():
    exc = assert_raises(
        NoRelevantKnowledgeError,
        lambda: answer_question(
            "Qu'est-ce qu'ABFINI ?",
            FakeEmbeddingProvider(),
            FakeGenerationProvider(),
            rpc_returning_low_similarity,
            threshold=0.5,
        ),
    )
    assert exc.reason == "below_threshold"


@dataclass
class BrokenEmbeddingProvider:
    model: str = "broken-embedding"
    dimensions: int = 768

    def embed_query(self, text: str) -> list[float]:
        raise RuntimeError("embedding backend unreachable")


def test_answer_question_raises_embedding_failed_error():
    assert_raises(
        EmbeddingFailedError,
        lambda: answer_question(
            "Qu'est-ce qu'ABFINI ?", BrokenEmbeddingProvider(), FakeGenerationProvider(), fake_rpc
        ),
    )


def broken_rpc(function_name, *, query_embedding, **kwargs):
    raise RuntimeError("Supabase HTTP 503: backend unavailable")


def test_answer_question_raises_retrieval_failed_error():
    assert_raises(
        RetrievalFailedError,
        lambda: answer_question(
            "Qu'est-ce qu'ABFINI ?", FakeEmbeddingProvider(), FakeGenerationProvider(), broken_rpc
        ),
    )


@dataclass
class BrokenGenerationProvider:
    model: str = "broken-generator"

    def generate(self, request: GenerationRequest) -> GenerationResult:
        raise RuntimeError("all configured model providers failed")


def test_answer_question_raises_generation_failed_error_when_provider_raises():
    assert_raises(
        GenerationFailedError,
        lambda: answer_question(
            "Qu'est-ce qu'ABFINI ?", FakeEmbeddingProvider(), BrokenGenerationProvider(), fake_rpc
        ),
    )


@dataclass
class EmptyAnswerGenerationProvider:
    model: str = "empty-generator"

    def generate(self, request: GenerationRequest) -> GenerationResult:
        return GenerationResult(answer="   ", model=self.model)


def test_answer_question_raises_generation_failed_error_on_empty_answer():
    assert_raises(
        GenerationFailedError,
        lambda: answer_question(
            "Qu'est-ce qu'ABFINI ?",
            FakeEmbeddingProvider(),
            EmptyAnswerGenerationProvider(),
            fake_rpc,
        ),
    )


if __name__ == "__main__":
    test_full_rag_pipeline()
    test_full_rag_pipeline_populates_metrics()
    test_answer_question_raises_invalid_question_error_on_empty_question()
    test_answer_question_raises_no_relevant_knowledge_error_with_no_candidates()
    test_answer_question_raises_no_relevant_knowledge_error_below_threshold()
    test_answer_question_raises_embedding_failed_error()
    test_answer_question_raises_retrieval_failed_error()
    test_answer_question_raises_generation_failed_error_when_provider_raises()
    test_answer_question_raises_generation_failed_error_on_empty_answer()
    print("RAG pipeline typed-error tests: PASS")
