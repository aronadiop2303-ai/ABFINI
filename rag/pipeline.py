"""Full RAG pipeline for ABFINI V0.1.

Flow: question -> query embedding -> retrieval/ranking -> bounded context
-> provider-agnostic text generation -> answer.
"""
from dataclasses import dataclass
from typing import Any, Callable, Sequence

from embeddings.provider import EmbeddingProvider
from models.provider import GenerationRequest, GenerationResult, TextGenerationProvider
from observability.metrics import RequestMetrics
from .errors import (
    EmbeddingFailedError,
    GenerationFailedError,
    InvalidQuestionError,
    NoRelevantKnowledgeError,
    RetrievalFailedError,
)
from .retriever import RetrievedContext, retrieve_context

DEFAULT_SYSTEM_PROMPT = (
    "Tu es ABFINI. Réponds à partir du contexte fourni. "
    "Si le contexte ne permet pas de répondre, dis clairement que l'information "
    "n'est pas présente dans les connaissances récupérées. N'invente pas de faits."
)


@dataclass(frozen=True)
class RAGResponse:
    question: str
    answer: str
    model: str
    retrieved: RetrievedContext


def answer_question(
    question: str,
    embedding_provider: EmbeddingProvider,
    generation_provider: TextGenerationProvider,
    rpc: Callable[..., list[dict[str, Any]]],
    *,
    top_k: int = 5,
    threshold: float = 0.0,
    max_chars: int = 12000,
    system_prompt: str = DEFAULT_SYSTEM_PROMPT,
    metrics: RequestMetrics | None = None,
) -> RAGResponse:
    """Execute the complete ABFINI V0.1 RAG flow and return the answer.

    ``metrics``, when provided, is instrumented around each stage (embedding,
    retrieval, generation) but its overall ``finish()``/logging is the
    caller's responsibility, since only the caller knows the final status.
    """
    question = question.strip()
    if not question:
        raise InvalidQuestionError("question must not be empty")
    if not system_prompt.strip():
        raise InvalidQuestionError("system_prompt must not be empty")

    if metrics is not None:
        metrics.start_embedding()
    try:
        query_embedding = embedding_provider.embed_query(question)
    except Exception as exc:
        raise EmbeddingFailedError(str(exc)) from exc
    if metrics is not None:
        metrics.finish_embedding()

    if metrics is not None:
        metrics.start_retrieval()
    try:
        retrieved = retrieve_context(
            query_embedding,
            rpc,
            top_k=top_k,
            threshold=threshold,
            max_chars=max_chars,
        )
    except ValueError:
        raise
    except Exception as exc:
        raise RetrievalFailedError(str(exc)) from exc
    if metrics is not None:
        top_similarity = retrieved.results[0].similarity if retrieved.results else None
        metrics.finish_retrieval(results=len(retrieved.results), top_similarity=top_similarity)
    if not retrieved.results:
        reason = "below_threshold" if retrieved.raw_result_count > 0 else "no_candidates"
        raise NoRelevantKnowledgeError(reason)

    if metrics is not None:
        metrics.start_generation()
    try:
        generation = generation_provider.generate(
            GenerationRequest(
                question=question,
                context=retrieved.context,
                system_prompt=system_prompt,
            )
        )
    except Exception as exc:
        raise GenerationFailedError(str(exc)) from exc
    if not isinstance(generation, GenerationResult):
        raise GenerationFailedError("generation_provider.generate() must return GenerationResult")
    if not generation.answer.strip():
        raise GenerationFailedError("generation provider returned an empty answer")
    if metrics is not None:
        metrics.finish_generation(model=generation.model)

    return RAGResponse(
        question=question,
        answer=generation.answer.strip(),
        model=generation.model,
        retrieved=retrieved,
    )
