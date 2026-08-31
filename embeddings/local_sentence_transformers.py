"""Local embedding provider using a SentenceTransformers-compatible model.

No external LLM API or API key is required. The model is downloaded/cached
by SentenceTransformers at runtime.
"""
from .provider import EmbeddingProvider


class LocalSentenceTransformerProvider:
    def __init__(self, model_name: str, expected_dimension: int = 1536) -> None:
        from sentence_transformers import SentenceTransformer

        self.model = SentenceTransformer(model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()
        if self.dimension != expected_dimension:
            raise ValueError(
                f"Embedding dimension mismatch: model={self.dimension}, "
                f"expected={expected_dimension}"
            )

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        vectors = self.model.encode(
            texts,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )
        return vectors.tolist()
