from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
sys.path.insert(0, str(Path(__file__).parents[1]))

from models.provider import GenerationResult
from core import OmniOrchestrator, OmniPlanner, OmniToolRouter
from integrations.rag_adapter import OmniRAGAdapter


class FakeEmbedding:
    model = "test-embedding"
    dimensions = 768

    def embed_query(self, text):
        return [1.0] + [0.0] * 767


class FakeGeneration:
    model = "integration-test-model"

    def generate(self, request):
        return GenerationResult("ABFINI est une couche de connaissance.", self.model)


def fake_rpc(function_name, *, query_embedding, match_threshold, match_count):
    assert function_name == "semantic_search_document_chunks"
    return [
        {
            "id": "chunk-1",
            "document_id": "doc-1",
            "chunk_index": 0,
            "content": "ABFINI est une couche de connaissance.",
            "metadata": {},
            "similarity": 0.99,
        }
    ]


def test_orchestrator_answers_from_abfini_rag_and_remembers_it():
    adapter = OmniRAGAdapter(FakeEmbedding(), FakeGeneration(), fake_rpc, top_k=1)
    orchestrator = OmniOrchestrator(OmniPlanner(), OmniToolRouter(), adapter.as_answer_fn())

    result = orchestrator.run("Qu'est-ce qu'ABFINI ?")

    assert result.answer == "ABFINI est une couche de connaissance."
    assert result.model == "integration-test-model"
    remembered = {entry.kind: entry.content for entry in orchestrator.memory.recent()}
    assert remembered["answer"] == result.answer
    assert remembered["task"] == "Qu'est-ce qu'ABFINI ?"
