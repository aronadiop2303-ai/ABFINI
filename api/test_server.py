"""Deterministic tests for the ABFINI HTTP API."""
from dataclasses import dataclass, field

from fastapi.testclient import TestClient

from models.model_types import ModelDescriptor, ModelType
from models.provider import GenerationRequest, GenerationResult
from api.server import create_app


@dataclass
class FakeEmbeddingProvider:
    model: str = "fake-embedding"
    dimensions: int = 768

    def embed_query(self, text: str) -> list[float]:
        assert text in ("Qu'est-ce qu'ABFINI ?", "ping")
        return [1.0] + [0.0] * 767


@dataclass
class FakeGenerationProvider:
    model: str = "fake-generator"
    catalog: tuple[ModelDescriptor, ...] = field(
        default_factory=lambda: (
            ModelDescriptor(model="fake-generator", provider="FakeGenerationProvider", model_type=ModelType.LOCAL),
        )
    )

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


def test_chat_logs_complete_request_metrics(caplog):
    import logging

    client = make_client()
    with caplog.at_level(logging.INFO, logger="abfini.api"):
        response = client.post(
            "/v1/chat",
            headers={"Authorization": "Bearer test-key"},
            json={"message": "Qu'est-ce qu'ABFINI ?"},
        )
    assert response.status_code == 200

    records = [r for r in caplog.records if r.name == "abfini.api"]
    assert len(records) == 1
    metrics = records[0].metrics
    assert metrics["request_id"] == response.json()["request_id"]
    assert metrics["status"] == "success"
    assert metrics["model"] == "fake-generator"
    assert metrics["retrieval_results"] == 1
    assert metrics["top_similarity"] == 0.95
    assert metrics["embedding_ms"] is not None
    assert metrics["retrieval_ms"] is not None
    assert metrics["generation_ms"] is not None
    assert metrics["total_ms"] == response.json()["latency_ms"]


def rpc_returning_nothing(function_name, *, query_embedding, **kwargs):
    return []


def test_chat_returns_404_when_no_relevant_knowledge():
    client = TestClient(
        create_app(
            embedding_provider=FakeEmbeddingProvider(),
            generation_provider=FakeGenerationProvider(),
            rpc=rpc_returning_nothing,
            api_key="test-key",
        )
    )
    response = client.post(
        "/v1/chat",
        headers={"Authorization": "Bearer test-key"},
        json={"message": "Qu'est-ce qu'ABFINI ?"},
    )
    assert response.status_code == 404


def broken_rpc(function_name, *, query_embedding, **kwargs):
    raise RuntimeError("Supabase HTTP 503: backend unavailable")


def test_chat_returns_502_when_retrieval_backend_fails():
    client = TestClient(
        create_app(
            embedding_provider=FakeEmbeddingProvider(),
            generation_provider=FakeGenerationProvider(),
            rpc=broken_rpc,
            api_key="test-key",
        )
    )
    response = client.post(
        "/v1/chat",
        headers={"Authorization": "Bearer test-key"},
        json={"message": "Qu'est-ce qu'ABFINI ?"},
    )
    assert response.status_code == 502


def test_health_dependencies_reports_real_per_dependency_status():
    client = make_client()
    response = client.get("/health/dependencies")
    assert response.status_code == 200
    body = response.json()
    assert body["service"] == "abfini"
    assert body["status"] in ("ok", "degraded")
    assert body["dependencies"]["embedding"]["status"] == "ok"
    assert body["dependencies"]["embedding"]["model"] == "fake-embedding"
    assert body["dependencies"]["model_router"]["status"] == "ok"
    assert body["dependencies"]["model_router"]["providers"][0]["provider"] == "FakeGenerationProvider"
    # No SUPABASE_URL/SUPABASE_SERVICE_ROLE_KEY is set in the test environment,
    # so the Supabase dependency must honestly report an error, never a fake "ok".
    assert body["dependencies"]["supabase"]["status"] == "error"
    assert body["status"] == "degraded"


def test_cors_disabled_by_default():
    client = make_client()
    response = client.get(
        "/health",
        headers={"Origin": "https://example.com"},
    )
    assert "access-control-allow-origin" not in response.headers


def test_cors_allows_configured_origin(monkeypatch):
    monkeypatch.setenv("ABFINI_CORS_ORIGINS", "https://abfini-web.vercel.app")
    client = TestClient(
        create_app(
            embedding_provider=FakeEmbeddingProvider(),
            generation_provider=FakeGenerationProvider(),
            rpc=fake_rpc,
            api_key="test-key",
        )
    )
    response = client.get(
        "/health",
        headers={"Origin": "https://abfini-web.vercel.app"},
    )
    assert response.headers["access-control-allow-origin"] == "https://abfini-web.vercel.app"


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
