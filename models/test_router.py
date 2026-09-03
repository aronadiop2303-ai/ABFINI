"""Deterministic tests for the ABFINI model router."""
from dataclasses import dataclass

from .provider import GenerationRequest, GenerationResult
from .router import ModelRouter, ModelRouterError


@dataclass
class FakeProvider:
    model: str
    answer: str = ""
    error: Exception | None = None

    def generate(self, request: GenerationRequest) -> GenerationResult:
        if self.error is not None:
            raise self.error
        return GenerationResult(answer=self.answer, model=self.model)


def request() -> GenerationRequest:
    return GenerationRequest(question="Q", context="C", system_prompt="S")


def test_primary_provider_wins() -> None:
    primary = FakeProvider("deepseek", answer="réponse primaire")
    fallback = FakeProvider("openrouter", answer="réponse fallback")
    result = ModelRouter([primary, fallback]).generate(request())
    assert result.answer == "réponse primaire"
    assert result.model == "deepseek"


def test_fallback_is_used_when_primary_fails() -> None:
    primary = FakeProvider("deepseek", error=RuntimeError("temporary failure"))
    fallback = FakeProvider("openrouter", answer="réponse fallback")
    result = ModelRouter([primary, fallback]).generate(request())
    assert result.answer == "réponse fallback"
    assert result.model == "openrouter"


def test_last_resort_is_used() -> None:
    providers = [
        FakeProvider("deepseek", error=RuntimeError("down")),
        FakeProvider("openrouter", error=RuntimeError("down")),
        FakeProvider("anthropic", answer="dernier recours"),
    ]
    result = ModelRouter(providers).generate(request())
    assert result.model == "anthropic"


def test_all_failures_raise_without_exposing_provider_error_details() -> None:
    providers = [
        FakeProvider("deepseek", error=RuntimeError("secret-like detail")),
        FakeProvider("openrouter", error=RuntimeError("another detail")),
    ]
    try:
        ModelRouter(providers).generate(request())
    except ModelRouterError as exc:
        assert str(exc) == "all configured model providers failed"
    else:
        raise AssertionError("expected ModelRouterError")


def test_empty_provider_list_rejected() -> None:
    try:
        ModelRouter([])
    except ValueError as exc:
        assert "at least one" in str(exc)
    else:
        raise AssertionError("expected ValueError")
