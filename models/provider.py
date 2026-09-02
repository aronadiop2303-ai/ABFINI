"""Provider-agnostic text-generation interface for ABFINI V0.1."""
from dataclasses import dataclass
from typing import Protocol, Sequence


@dataclass(frozen=True)
class GenerationRequest:
    question: str
    context: str
    system_prompt: str


@dataclass(frozen=True)
class GenerationResult:
    answer: str
    model: str


class TextGenerationProvider(Protocol):
    model: str

    def generate(self, request: GenerationRequest) -> GenerationResult:
        """Generate an answer from a question and retrieved context."""
        ...
