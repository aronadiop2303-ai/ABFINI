"""Offline tests for the DeepSeek generation provider."""
import json
from io import BytesIO

from models.deepseek import DeepSeekProvider
from models.provider import GenerationRequest


class FakeResponse:
    def __init__(self, payload: dict):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


def test_deepseek_provider_request_and_response():
    captured = {}

    def fake_opener(request, timeout):
        captured["request"] = request
        captured["timeout"] = timeout
        return FakeResponse(
            {
                "model": "deepseek-v4-pro",
                "choices": [{"message": {"content": "Réponse fondée sur le contexte."}}],
            }
        )

    provider = DeepSeekProvider(
        api_key="test-key",
        model="deepseek-v4-pro",
        opener=fake_opener,
    )
    result = provider.generate(
        GenerationRequest(
            question="Qu'est-ce qu'ABFINI ?",
            context="ABFINI est une couche de connaissance.",
            system_prompt="Réponds uniquement à partir du contexte.",
        )
    )

    assert result.answer == "Réponse fondée sur le contexte."
    assert result.model == "deepseek-v4-pro"
    assert captured["timeout"] == 60.0
    assert captured["request"].get_header("Authorization") == "Bearer test-key"
    payload = json.loads(captured["request"].data.decode("utf-8"))
    assert payload["model"] == "deepseek-v4-pro"
    assert payload["stream"] is False
    assert payload["messages"][0]["role"] == "system"
    assert "ABFINI est une couche de connaissance." in payload["messages"][1]["content"]


if __name__ == "__main__":
    test_deepseek_provider_request_and_response()
    print("DeepSeek provider test: PASS")
