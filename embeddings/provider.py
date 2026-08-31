"""Provider-agnostic embedding interface for ABFINI V0.1.

No model vendor is hard-coded here. A concrete provider can be added later
without changing document ingestion, storage, or pgvector code.
"""
from dataclasses import dataclass
from typing import Protocol, Sequence


@dataclass(frozen=True)
class EmbeddingResult:
    vectors: list[list[float]]
    model: str
    dimensions: int


class EmbeddingProvider(Protocol):
    model: str
    dimensions: int

    def embed(self, texts: Sequence[str]) -> EmbeddingResult:
        """Return one vector per input text, preserving input order."""
        ...

    def embed_query(self, text: str) -> list[float]:
        """Return the vector for one search query."""
        ...
