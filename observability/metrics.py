"""Lightweight, secret-safe observability for ABFINI V0.1."""
from dataclasses import dataclass, field
from time import perf_counter
from typing import Any


@dataclass
class RequestMetrics:
    request_id: str
    model: str = ""
    status: str = "in_progress"
    retrieval_results: int = 0
    top_similarity: float | None = None
    embedding_ms: int | None = None
    retrieval_ms: int | None = None
    generation_ms: int | None = None
    total_ms: int | None = None
    _started: float = field(default_factory=perf_counter, repr=False)
    _embedding_started: float | None = field(default=None, repr=False)
    _retrieval_started: float | None = field(default=None, repr=False)
    _generation_started: float | None = field(default=None, repr=False)

    def start_embedding(self) -> None:
        self._embedding_started = perf_counter()

    def finish_embedding(self) -> None:
        if self._embedding_started is not None:
            self.embedding_ms = int((perf_counter() - self._embedding_started) * 1000)

    def start_retrieval(self) -> None:
        self._retrieval_started = perf_counter()

    def finish_retrieval(self, *, results: int, top_similarity: float | None) -> None:
        if self._retrieval_started is not None:
            self.retrieval_ms = int((perf_counter() - self._retrieval_started) * 1000)
        self.retrieval_results = results
        self.top_similarity = top_similarity

    def start_generation(self) -> None:
        self._generation_started = perf_counter()

    def finish_generation(self, *, model: str) -> None:
        if self._generation_started is not None:
            self.generation_ms = int((perf_counter() - self._generation_started) * 1000)
        self.model = model

    def finish(self, *, status: str) -> None:
        self.status = status
        self.total_ms = int((perf_counter() - self._started) * 1000)

    def as_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "model": self.model,
            "status": self.status,
            "retrieval_results": self.retrieval_results,
            "top_similarity": self.top_similarity,
            "embedding_ms": self.embedding_ms,
            "retrieval_ms": self.retrieval_ms,
            "generation_ms": self.generation_ms,
            "total_ms": self.total_ms,
        }
