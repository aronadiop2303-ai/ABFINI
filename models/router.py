"""Extensible model router for ABFINI V0.1.

The router is provider-agnostic. It supports proprietary APIs, open-source /
open-weight models, gateway providers, hybrid deployments, and local models.
New providers are added by implementing TextGenerationProvider; the routing
algorithm itself does not need to change.
"""
from dataclasses import dataclass
from typing import Sequence

from .model_types import ModelDescriptor, describe_provider
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

    @property
    def catalog(self) -> tuple[ModelDescriptor, ...]:
        """Return safe metadata for every configured route, without secrets."""
        return tuple(describe_provider(provider) for provider in self.providers)

    def models_by_type(self, model_type: str) -> tuple[ModelDescriptor, ...]:
        """Filter the configured catalog by taxonomy value."""
        return tuple(item for item in self.catalog if item.model_type.value == model_type)
