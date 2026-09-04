from __future__ import annotations

from typing import Any, Callable, Sequence

from rag.pipeline import RAGResponse, answer_question
from models.provider import TextGenerationProvider
from embeddings.provider import EmbeddingProvider


class OmniRAGAdapter:
    """Adapter exposing the validated ABFINI V0.1 RAG pipeline to OMNI."""

    def __init__(self, embedding_provider: EmbeddingProvider, generation_provider: TextGenerationProvider, rpc: Callable[..., list[dict[str, Any]]], *, top_k: int = 5, threshold: float = 0.0, max_chars: int = 12000) -> None:
        self.embedding_provider = embedding_provider
        self.generation_provider = generation_provider
        self.rpc = rpc
        self.top_k = top_k
        self.threshold = threshold
        self.max_chars = max_chars

    def answer(self, question: str) -> RAGResponse:
        return answer_question(question, self.embedding_provider, self.generation_provider, self.rpc, top_k=self.top_k, threshold=self.threshold, max_chars=self.max_chars)
