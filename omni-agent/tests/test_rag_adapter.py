from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))

from models.provider import GenerationResult
from integrations.rag_adapter import OmniRAGAdapter


class FakeEmbedding:
    model = "test-embedding"
    dimensions = 768

    def embed_query(self, text):
        return [1.0] + [0.0] * 767


class FakeGeneration:
    model = "integration-test-model"

    def generate(self, request):
        assert request.question == "Qu'est-ce qu'ABFINI ?"
        assert "ABFINI" in request.context
        return GenerationResult("ABFINI est une couche de connaissance.", self.model)


def test_omni_rag_adapter_runs_full_rag_contract():
    def rpc(query_embedding, match_threshold, match_count):
        assert len(query_embedding) == 768
        return [{"id": "chunk-1", "document_id": "doc-1", "chunk_index": 0, "content": "ABFINI est une couche de connaissance.", "metadata": {}, "similarity": 0.99}]

    adapter = OmniRAGAdapter(FakeEmbedding(), FakeGeneration(), rpc, top_k=1)
    result = adapter.answer("Qu'est-ce qu'ABFINI ?")
    assert result.answer.startswith("ABFINI")
    assert result.model == "integration-test-model"
    assert len(result.retrieved.results) == 1
