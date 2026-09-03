"""Deterministic tests for the OpenRouter provider."""
import json
from dataclasses import dataclass

from .openrouter import OpenRouterProvider
from .provider import GenerationRequest


@dataclass
class FakeResponse:
    payload: dict

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


def request() -> GenerationRequest:
    return GenerationRequest(question="Q", context="C", system_prompt="S")


def test_openrouter_provider_parses_chat_completion():
    seen = {}

    def opener(http_request, timeout):
        seen["url"] = http_request.full_url
        seen["timeout"] = timeout
        seen["authorization"] = http_request.headers["Authorization"]
        return FakeResponse({
            "model": "qwen/test-open",
            "choices": [{"message": {"content": "réponse open-weight"}}],
        })

    provider = OpenRouterProvider(
        api_key="test-key",
        model="qwen/test-open",
        opener=opener,
    )
    result = provider.generate(request())

    assert result.answer == "réponse open-weight"
    assert result.model == "qwen/test-open"
    assert seen["url"].endswith("/chat/completions")
    assert seen["authorization"] == "Bearer test-key"


def test_openrouter_provider_rejects_invalid_response():
    def opener(http_request, timeout):
        return FakeResponse({"choices": []})

    provider = OpenRouterProvider(api_key="test-key", opener=opener)
    try:
        provider.generate(request())
    except Exception as exc:
        assert "invalid response" in str(exc)
    else:
        raise AssertionError("expected provider failure")
