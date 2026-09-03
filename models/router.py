"""Provider router for ABFINI V0.1.

Order of preference:
1. DeepSeek
2. OpenRouter fallback
3. Anthropic last resort

Providers are injected so the router remains provider-agnostic and easy to test.
"""
from dataclasses import dataclass
from typing import Sequence

from .provider import GenerationRequest, GenerationResult, TextGenerationProvider


class ModelRouterError(RuntimeError):
    """Raised when every configured model provider fails."""


@dataclass(frozen=True)
class ModelRouter:
    providers: Sequence[TextGenerationProvider]

    def __post_init__(self) -> None:
        if not self.providers:
            raise ValueError("at least one model provider is required")

    def generate(self, request: GenerationRequest) -> GenerationResult:
        """Try providers in configured priority order and return the first success."""
        errors: list[str] = []
        for provider in self.providers:
            try:
                result = provider.generate(request)
                if not isinstance(result, GenerationResult):
                    raise TypeError("provider returned an invalid GenerationResult")
                if not result.answer.strip():
                    raise ValueError("provider returned an empty answer")
                return result
            except Exception as exc:  # noqa: BLE001 - router must fail over safely.
                model = getattr(provider, "model", provider.__class__.__name__)
                errors.append(f"{model}: {exc}")
        raise ModelRouterError("all configured model providers failed") from RuntimeError(
            "; ".join(errors)
        )

    @property
    def model(self) -> str:
        """Expose the primary model for the provider protocol."""
        return getattr(self.providers[0], "model", self.providers[0].__class__.__name__)
