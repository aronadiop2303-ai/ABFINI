"""Typed failure modes for the ABFINI RAG pipeline.

``answer_question()`` used to raise a single generic ``ValueError`` for
every failure past basic input validation, so a caller (``api/server.py``)
could not tell "no matching knowledge" apart from "the embedding provider
is broken" or "Supabase is unreachable" without parsing the error message.
"""
from __future__ import annotations


class RAGError(Exception):
    """Base class for every typed RAG pipeline failure."""


class InvalidQuestionError(RAGError, ValueError):
    """The question or system prompt failed input validation."""


class EmbeddingFailedError(RAGError, RuntimeError):
    """The embedding provider raised while embedding the question."""


class RetrievalFailedError(RAGError, RuntimeError):
    """Retrieval failed: the RPC raised (Supabase error, network error,
    malformed response row, etc.)."""


class NoRelevantKnowledgeError(RAGError, ValueError):
    """Retrieval succeeded but produced no usable result.

    ``reason`` is ``"no_candidates"`` when the RPC returned zero rows, or
    ``"below_threshold"`` when rows were returned but every one was
    filtered out by the similarity threshold, blank content, or a
    non-finite (NaN/Infinity) similarity score.
    """

    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(f"No relevant knowledge was retrieved for the question ({reason})")


class GenerationFailedError(RAGError, RuntimeError):
    """The generation provider raised, or returned an invalid/empty answer."""
