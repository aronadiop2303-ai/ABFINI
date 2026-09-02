"""End-to-end ABFINI RAG retrieval test against Supabase."""

import json
import os
import urllib.error
import urllib.parse
import urllib.request

from embeddings.local_sentence_transformers import LocalSentenceTransformerProvider
from rag.retriever import retrieve_context

MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-base-en-v1.5")
EXPECTED_DIMENSIONS = 768
RPC_NAME = "semantic_search_document_chunks"


def normalize_url(raw_url: str) -> str:
    value = raw_url.strip().rstrip("/")
    parsed = urllib.parse.urlsplit(value)
    if parsed.scheme != "https" or not parsed.netloc:
        raise RuntimeError("SUPABASE_URL must be a full https:// Supabase project URL")
    if parsed.path not in {"", "/", "/rest/v1", "/rest/v1/"} or parsed.query or parsed.fragment:
        raise RuntimeError("SUPABASE_URL must contain only the Supabase project origin")
    return f"{parsed.scheme}://{parsed.netloc}"


def supabase_rpc(name: str, **kwargs):
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not key:
        raise RuntimeError("SUPABASE_SERVICE_ROLE_KEY is not configured")
    base = normalize_url(os.environ.get("SUPABASE_URL", ""))
    url = f"{base}/rest/v1/rpc/{urllib.parse.quote(name, safe='')}"
    payload = dict(kwargs)
    if isinstance(payload.get("query_embedding"), list):
        payload["query_embedding"] = "[" + ",".join(f"{float(x):.10g}" for x in payload["query_embedding"]) + "]"
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
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
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode(errors="replace")
        raise RuntimeError(f"Supabase HTTP {exc.code}: {detail}") from exc


def main() -> None:
    query = os.getenv("RAG_QUERY", "Qu'est-ce qu'ABFINI ?")
    provider = LocalSentenceTransformerProvider(MODEL, expected_dimension=EXPECTED_DIMENSIONS)
    vector = provider.embed_query(query)
    assert len(vector) == EXPECTED_DIMENSIONS

    result = retrieve_context(
        vector,
        supabase_rpc,
        top_k=int(os.getenv("RAG_TOP_K", "5")),
        threshold=float(os.getenv("RAG_THRESHOLD", "0.0")),
        max_chars=int(os.getenv("RAG_MAX_CHARS", "12000")),
    )

    assert result.results, "RAG retrieval returned no results"
    assert result.context, "RAG context is empty"
    assert any("ABFINI" in item.content for item in result.results), "Expected ABFINI content was not retrieved"
    print(f"Query: {query}")
    print(f"Retrieved: {len(result.results)}")
    print(result.context)
    print("RAG end-to-end test: PASS")


if __name__ == "__main__":
    main()
