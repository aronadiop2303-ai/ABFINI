"""Real ABFINI RAG + DeepSeek integration test.

Requires runtime secrets/configuration:
- SUPABASE_URL
- SUPABASE_SERVICE_ROLE_KEY
- DEEPSEEK_API_KEY
"""
import json
import os
import urllib.error
import urllib.request

from embeddings.local_sentence_transformers import LocalSentenceTransformerProvider
from models.deepseek import DeepSeekProvider
from rag.pipeline import answer_question


RPC_NAME = "semantic_search_document_chunks"
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-base-en-v1.5")


def normalize_supabase_url(raw_url: str) -> str:
    value = raw_url.strip().rstrip("/")
    if not value:
        raise RuntimeError("SUPABASE_URL is not configured")
    if not value.startswith("https://") or "/" in value[len("https://") :].rstrip("/"):
        raise RuntimeError("SUPABASE_URL must be a full https:// Supabase project URL")
    return value


def supabase_rpc(function_name: str, **params):
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
            raw = response.read().decode("utf-8")
            result = json.loads(raw) if raw else None
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode(errors="replace")
        raise RuntimeError(f"Supabase HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Supabase connection error: {exc.reason}") from exc

    if not isinstance(result, list):
        raise RuntimeError("Supabase semantic search did not return a JSON array")
    return result


def main() -> None:
    question = os.getenv("RAG_QUERY", "Qu'est-ce qu'ABFINI ?")
    top_k = int(os.getenv("RAG_TOP_K", "5"))
    threshold = float(os.getenv("RAG_THRESHOLD", "0.0"))
    max_chars = int(os.getenv("RAG_MAX_CHARS", "12000"))

    embedding_provider = LocalSentenceTransformerProvider(
        EMBEDDING_MODEL,
        expected_dimension=768,
    )
    generation_provider = DeepSeekProvider.from_env()

    result = answer_question(
        question,
        embedding_provider,
        generation_provider,
        supabase_rpc,
        top_k=top_k,
        threshold=threshold,
        max_chars=max_chars,
    )

    print(f"Question: {result.question}")
    print(f"Model: {result.model}")
    print(f"Retrieved results: {len(result.retrieved.results)}")
    for index, retrieved in enumerate(result.retrieved.results, start=1):
        print(
            f"Source {index}: document={retrieved.document_id} "
            f"chunk={retrieved.chunk_index} similarity={retrieved.similarity:.4f}"
        )
    print("Answer:")
    print(result.answer)

    if not result.answer.strip():
        raise RuntimeError("DeepSeek returned an empty answer")
    if not result.retrieved.results:
        raise RuntimeError("RAG retrieval returned no results")


if __name__ == "__main__":
    main()
