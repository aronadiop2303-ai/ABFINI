"""Deterministic tests for ABFINI observability."""
from observability.metrics import RequestMetrics


def test_request_metrics_lifecycle():
    metrics = RequestMetrics(request_id="req-test")
    metrics.start_embedding()
    metrics.finish_embedding()
    metrics.start_retrieval()
    metrics.finish_retrieval(results=3, top_similarity=0.87)
    metrics.start_generation()
    metrics.finish_generation(model="fake-generator")
    metrics.finish(status="success")

    data = metrics.as_dict()
    assert data["request_id"] == "req-test"
    assert data["model"] == "fake-generator"
    assert data["status"] == "success"
    assert data["retrieval_results"] == 3
    assert data["top_similarity"] == 0.87
    assert data["embedding_ms"] is not None
    assert data["retrieval_ms"] is not None
    assert data["generation_ms"] is not None
    assert data["total_ms"] is not None


def test_metrics_are_secret_safe():
    metrics = RequestMetrics(request_id="req-test")
    metrics.finish(status="error")
    data = metrics.as_dict()
    assert "api_key" not in data
    assert "authorization" not in data
    assert "DEEPSEEK_API_KEY" not in str(data)


if __name__ == "__main__":
    test_request_metrics_lifecycle()
    test_metrics_are_secret_safe()
    print("Observability metrics test: PASS")
