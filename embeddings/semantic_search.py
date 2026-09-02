"""Semantic search against ABFINI document chunks."""

import json
import os
import urllib.error
import urllib.parse
import urllib.request

from .local_sentence_transformers import LocalSentenceTransformerProvider

MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-base-en-v1.5")
EXPECTED_DIMENSIONS = 768
RPC_NAME = "semantic_search_document_chunks"


def request_json(url: str, method: str = "GET", payload=None):
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not key:
        raise RuntimeError("SUPABASE_SERVICE_ROLE_KEY is not configured")

    body = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Accept": "application/json",
    }
    if body is not None:
        headers["Content-Type"] = "application/json"

    request = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw) if raw else None
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode(errors="replace")
        raise RuntimeError(f"Supabase HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Supabase connection error: {exc.reason}") from exc


def normalize_supabase_url(raw_url: str) -> str:
    value = raw_url.strip().rstrip("/")
    if not value:
        raise RuntimeError("SUPABASE_URL is not configured")

    parsed = urllib.parse.urlsplit(value)
    if parsed.scheme != "https" or not parsed.netloc:
        raise RuntimeError("SUPABASE_URL must be a full https:// Supabase project URL")

    allowed_paths = {"", "/", "/rest/v1", "/rest/v1/"}
    if parsed.path not in allowed_paths or parsed.query or parsed.fragment:
        raise RuntimeError(
            "SUPABASE_URL must contain only the Supabase project origin "
            "(for example https://<project>.supabase.co)"
        )

    return f"{parsed.scheme}://{parsed.netloc}"


def semantic_search(
    query: str,
    match_threshold: float = 0.0,
    match_count: int = 5,
):
    """Embed a natural-language query and retrieve matching ABFINI chunks."""
    query = query.strip()
    if not query:
        raise ValueError("query must not be empty")
    if not 0.0 <= match_threshold <= 1.0:
        raise ValueError("match_threshold must be between 0.0 and 1.0")
    if match_count < 1:
        raise ValueError("match_count must be >= 1")

    base = normalize_supabase_url(os.environ.get("SUPABASE_URL", ""))
    provider = LocalSentenceTransformerProvider(
        MODEL,
        expected_dimension=EXPECTED_DIMENSIONS,
    )
    query_vector = provider.embed_query(query)

    if len(query_vector) != EXPECTED_DIMENSIONS:
        raise RuntimeError(
            f"Query embedding dimension mismatch: {len(query_vector)} != {EXPECTED_DIMENSIONS}"
        )

    vector_text = "[" + ",".join(f"{float(x):.10g}" for x in query_vector) + "]"
    rpc_url = f"{base}/rest/v1/rpc/{RPC_NAME}"

    return request_json(
        rpc_url,
        method="POST",
        payload={
            "query_embedding": vector_text,
            "match_threshold": float(match_threshold),
            "match_count": int(match_count),
        },
    )


def main() -> None:
    query = os.getenv("SEMANTIC_QUERY", "Qu'est-ce qu'ABFINI ?")
    results = semantic_search(
        query=query,
        match_threshold=float(os.getenv("MATCH_THRESHOLD", "0.0")),
        match_count=int(os.getenv("MATCH_COUNT", "5")),
    )

    if not isinstance(results, list):
        raise RuntimeError("Supabase semantic search did not return a JSON array")

    print(f"Query: {query}")
    print(f"Results: {len(results)}")
    for index, result in enumerate(results, start=1):
        print(f"Result {index}: {json.dumps(result, ensure_ascii=False)}")

    if not results:
        raise RuntimeError("Semantic search returned no results")


if __name__ == "__main__":
    main()
