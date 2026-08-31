"""Local embedding provider using SentenceTransformers.

No external LLM API or API key is required. The model is downloaded/cached
by SentenceTransformers at runtime.
"""
from collections.abc import Sequence

from .provider import EmbeddingProvider, EmbeddingResult


class LocalSentenceTransformerProvider:
    def __init__(self, model_name: str, expected_dimension: int = 1536) -> None:
        from sentence_transformers import SentenceTransformer

        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
        self.dimensions = int(self.model.get_sentence_embedding_dimension())
        if self.dimensions != expected_dimension:
            raise ValueError(
                f"Embedding dimension mismatch: model={self.dimensions}, "
                f"expected={expected_dimension}"
            )

    @property
    def model(self) -> str:
        return self.model_name

    def embed(self, texts: Sequence[str]) -> EmbeddingResult:
        if not texts:
            return EmbeddingResult(vectors=[], model=self.model_name, dimensions=self.dimensions)
        vectors = self.model.encode(
            list(texts),
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )
        return EmbeddingResult(
            vectors=vectors.tolist(),
            model=self.model_name,
            dimensions=self.dimensions,
        )

    def embed_query(self, text: str) -> list[float]:
        return self.embed([text]).vectors[0]
