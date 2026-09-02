"""Local SentenceTransformers embedding provider.

No OpenAI or external LLM API is required. The model is downloaded/cached
by SentenceTransformers at runtime.
"""
from collections.abc import Sequence
from math import isfinite, sqrt

from .provider import EmbeddingProvider, EmbeddingResult


class LocalSentenceTransformerProvider:
    def __init__(self, model_name: str, expected_dimension: int = 768) -> None:
        from sentence_transformers import SentenceTransformer

        self.model = SentenceTransformer(model_name)
        self.model_name = model_name
        self.dimensions = self.model.get_embedding_dimension()
        if self.dimensions != expected_dimension:
            raise ValueError(
                f"Embedding dimension mismatch: model={self.dimensions}, expected={expected_dimension}"
            )

    @property
    def model_id(self) -> str:
        return self.model_name

    def _validate_vector(self, vector: Sequence[float]) -> list[float]:
        values = [float(value) for value in vector]
        if len(values) != self.dimensions:
            raise ValueError(
                f"Embedding dimension mismatch: vector={len(values)}, expected={self.dimensions}"
            )
        if not all(isfinite(value) for value in values):
            raise ValueError("Embedding contains a non-finite value")
        norm = sqrt(sum(value * value for value in values))
        if norm <= 0.0:
            raise ValueError("Embedding has zero L2 norm")
        if abs(norm - 1.0) > 1e-3:
            raise ValueError(f"Embedding is not normalized: L2 norm={norm:.8f}")
        return values

    def embed(self, texts: Sequence[str]) -> EmbeddingResult:
        if not texts:
            return EmbeddingResult(vectors=[], model=self.model_name, dimensions=self.dimensions)
        vectors = self.model.encode(
            list(texts), normalize_embeddings=True, convert_to_numpy=True, show_progress_bar=False
        ).tolist()
        validated = [self._validate_vector(vector) for vector in vectors]
        return EmbeddingResult(vectors=validated, model=self.model_name, dimensions=self.dimensions)

    def embed_query(self, text: str) -> list[float]:
        result = self.embed([text])
        return result.vectors[0]
