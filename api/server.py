"""ABFINI V0.1 HTTP API.

Exposes the provider-agnostic RAG pipeline through a small JSON API.
Runtime secrets are read only from environment variables.
"""
import hmac
import json
import os
import time
import urllib.error
import urllib.request
from collections import defaultdict
from threading import Lock
from typing import Any, Callable

from fastapi import FastAPI, Header, HTTPException, Request
from pydantic import BaseModel, Field

from embeddings.local_sentence_transformers import LocalSentenceTransformerProvider
from models.deepseek import DeepSeekProvider
from models.open_compatible import OpenCompatibleProvider
from models.openrouter import OpenRouterProvider
from models.router import ModelRouter
from rag.pipeline import answer_question

RPC_NAME = "semantic_search_document_chunks"
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-base-en-v1.5")
DEFAULT_RATE_LIMIT = 30
RATE_WINDOW_SECONDS = 60
DEFAULT_MODEL_ORDER = "deepseek,openrouter,open_model"


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    top_k: int = Field(default=5, ge=1, le=20)
    threshold: float = Field(default=0.0, ge=0.0, le=1.0)
    max_chars: int = Field(default=12000, ge=1, le=30000)


class Source(BaseModel):
    document_id: str
    chunk_index: int
    similarity: float


class ChatResponse(BaseModel):
    answer: str
    model: str
    sources: list[Source]
    retrieval: dict[str, Any]
    latency_ms: int
    request_id: str


def normalize_supabase_url(raw_url: str) -> str:
    value = raw_url.strip().rstrip("/")
    if not value:
        raise RuntimeError("SUPABASE_URL is not configured")
    if not value.startswith("https://"):
        raise RuntimeError("SUPABASE_URL must use https://")
    suffix = value[len("https://") :]
    if "/" in suffix or "?" in suffix or "#" in suffix:
        raise RuntimeError("SUPABASE_URL must be a project URL without a path")
    return value


def supabase_rpc(function_name: str, **params: Any) -> list[dict[str, Any]]:
    base = normalize_supabase_url(os.environ.get("SUPABASE_URL", ""))
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "").strip()
    if not key:
        raise RuntimeError("SUPABASE_SERVICE_ROLE_KEY is not configured")
    request = urllib.request.Request(
        f"{base}/rest/v1/rpc/{function_name}",
        data=json.dumps(params).encode("utf-8"),
        headers={
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            result = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode(errors="replace")
        raise RuntimeError(f"Supabase HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Supabase connection error: {exc.reason}") from exc
    if not isinstance(result, list):
        raise RuntimeError("Supabase semantic search did not return a JSON array")
    return result


def build_model_router() -> ModelRouter:
    """Build the configured provider chain without requiring every provider secret."""
    factories = {
        "deepseek": DeepSeekProvider.from_env,
        "openrouter": OpenRouterProvider.from_env,
        "open_model": OpenCompatibleProvider.from_env,
    }
    providers = []
    order = os.getenv("ABFINI_MODEL_ORDER", DEFAULT_MODEL_ORDER)
    for name in (item.strip().lower() for item in order.split(",")):
        if not name or name not in factories:
            continue
        try:
            provider = factories[name]()
        except ValueError:
            continue
        providers.append(provider)
    if not providers:
        raise RuntimeError("no model provider is configured")
    return ModelRouter(providers)


def create_app(
    *,
    embedding_provider: Any | None = None,
    generation_provider: Any | None = None,
    rpc: Callable[..., list[dict[str, Any]]] = supabase_rpc,
    api_key: str | None = None,
    rate_limit_per_minute: int | None = None,
) -> FastAPI:
    app = FastAPI(title="ABFINI API", version="0.1.0")
    app.state.embedding_provider = embedding_provider
    app.state.generation_provider = generation_provider
    app.state.rpc = rpc
    app.state.api_key = api_key if api_key is not None else os.getenv("ABFINI_API_KEY", "").strip()
    app.state.rate_limit = (
        rate_limit_per_minute
        if rate_limit_per_minute is not None
        else int(os.getenv("ABFINI_RATE_LIMIT_PER_MINUTE", str(DEFAULT_RATE_LIMIT)))
    )
    app.state.rate_lock = Lock()
    app.state.rate_windows: dict[str, list[float]] = defaultdict(list)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "abfini"}

    @app.post("/v1/chat", response_model=ChatResponse)
    def chat(
        request: ChatRequest,
        http_request: Request,
        authorization: str | None = Header(default=None),
    ) -> ChatResponse:
        expected_key = app.state.api_key
        if not expected_key:
            raise HTTPException(status_code=503, detail="ABFINI_API_KEY is not configured")
        expected_auth = f"Bearer {expected_key}"
        if not authorization or not hmac.compare_digest(authorization, expected_auth):
            raise HTTPException(status_code=401, detail="Invalid authorization")

        client_id = http_request.client.host if http_request.client else "unknown"
        now = time.monotonic()
        with app.state.rate_lock:
            timestamps = app.state.rate_windows[client_id]
            cutoff = now - RATE_WINDOW_SECONDS
            timestamps[:] = [timestamp for timestamp in timestamps if timestamp > cutoff]
            if len(timestamps) >= app.state.rate_limit:
                raise HTTPException(status_code=429, detail="Rate limit exceeded")
            timestamps.append(now)

        embedding_provider = app.state.embedding_provider
        if embedding_provider is None:
            embedding_provider = LocalSentenceTransformerProvider(
                EMBEDDING_MODEL, expected_dimension=768
            )
            app.state.embedding_provider = embedding_provider
        generation_provider = app.state.generation_provider
        if generation_provider is None:
            generation_provider = build_model_router()
            app.state.generation_provider = generation_provider

        started = time.perf_counter()
        request_id = f"req-{time.time_ns()}"
        try:
            result = answer_question(
                request.message,
                embedding_provider,
                generation_provider,
                app.state.rpc,
                top_k=request.top_k,
                threshold=request.threshold,
                max_chars=request.max_chars,
            )
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=502, detail="ABFINI backend unavailable") from exc

        latency_ms = int((time.perf_counter() - started) * 1000)
        sources = [
            Source(
                document_id=item.document_id,
                chunk_index=item.chunk_index,
                similarity=item.similarity,
            )
            for item in result.retrieved.results
        ]
        return ChatResponse(
            answer=result.answer,
            model=result.model,
            sources=sources,
            retrieval={
                "top_k": request.top_k,
                "threshold": request.threshold,
                "results": len(sources),
            },
            latency_ms=latency_ms,
            request_id=request_id,
        )

    return app


app = create_app()
