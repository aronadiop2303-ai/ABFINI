"""Deterministic tests for the ABFINI HTTP API."""
from dataclasses import dataclass

from fastapi.testclient import TestClient

from models.provider import GenerationRequest, GenerationResult
from api.server import create_app


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
        assert request.question == "Qu'est-ce qu'ABFINI ?"
        assert "ABFINI est une couche de connaissance" in request.context
        return GenerationResult(
            answer="ABFINI est une couche de connaissance.",
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
            "content": "ABFINI est une couche de connaissance.",
            "metadata": {"source": "test"},
            "similarity": 0.95,
        }
    ]


def make_client(*, rate_limit_per_minute=30):
    return TestClient(
        create_app(
            embedding_provider=FakeEmbeddingProvider(),
            generation_provider=FakeGenerationProvider(),
            rpc=fake_rpc,
            api_key="test-key",
            rate_limit_per_minute=rate_limit_per_minute,
        )
    )


def test_health():
    client = make_client()
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "abfini"}


def test_chat_requires_authentication():
    client = make_client()
    response = client.post("/v1/chat", json={"message": "test"})
    assert response.status_code == 401


def test_chat_returns_rag_answer():
    client = make_client()
    response = client.post(
        "/v1/chat",
        headers={"Authorization": "Bearer test-key"},
        json={"message": "Qu'est-ce qu'ABFINI ?"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["answer"] == "ABFINI est une couche de connaissance."
    assert body["model"] == "fake-generator"
    assert body["retrieval"]["results"] == 1
    assert body["sources"][0]["similarity"] == 0.95
    assert isinstance(body["latency_ms"], int)
    assert body["request_id"].startswith("req-")


def test_chat_rejects_invalid_authentication():
    client = make_client()
    response = client.post(
        "/v1/chat",
        headers={"Authorization": "Bearer wrong-key"},
        json={"message": "test"},
    )
    assert response.status_code == 401


def test_chat_rate_limit():
    client = make_client(rate_limit_per_minute=1)
    headers = {"Authorization": "Bearer test-key"}
    first = client.post(
        "/v1/chat",
        headers=headers,
        json={"message": "Qu'est-ce qu'ABFINI ?"},
    )
    second = client.post(
        "/v1/chat",
        headers=headers,
        json={"message": "Qu'est-ce qu'ABFINI ?"},
    )
    assert first.status_code == 200
    assert second.status_code == 429
