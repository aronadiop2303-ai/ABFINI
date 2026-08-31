"""Persist embeddings produced by an EmbeddingProvider into Supabase."""
from collections.abc import Sequence

from .provider import EmbeddingProvider
from .worker import ChunkForEmbedding, embed_chunks


class SupabaseEmbeddingWriter:
    def __init__(self, table) -> None:
        self.table = table

    def embed_and_write(
        self,
        chunks: list[ChunkForEmbedding],
        provider: EmbeddingProvider,
    ) -> int:
        pairs = embed_chunks(chunks, provider)
        for chunk_id, vector in pairs:
            self.table.update({"embedding": vector}).eq("id", chunk_id).execute()
        return len(pairs)
