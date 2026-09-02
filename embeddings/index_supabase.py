"""Embed pending ABFINI chunks and write vectors to Supabase."""
import json
import os
import urllib.error
import urllib.request

from .local_sentence_transformers import LocalSentenceTransformerProvider

MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-base-en-v1.5")
EXPECTED_DIMENSIONS = 768


def request_json(url: str, method: str = "GET", payload=None):
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not key:
        raise RuntimeError("SUPABASE_SERVICE_ROLE_KEY is not configured")
    body = None if payload is None else json.dumps(payload).encode()
    headers = {"apikey": key, "Authorization": f"Bearer {key}"}
    if body is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            raw = response.read().decode()
            return json.loads(raw) if raw else None
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode(errors="replace")
        raise RuntimeError(f"Supabase HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Supabase connection error: {exc.reason}") from exc


def main() -> None:
    base = os.environ.get("SUPABASE_URL", "").rstrip("/")
    if not base:
        raise RuntimeError("SUPABASE_URL is not configured")
    if not base.startswith("https://"):
        raise RuntimeError("SUPABASE_URL must start with https://")

    rows = request_json(
        base + "/rest/v1/document_chunks?select=id,content&embedding=is.null&order=created_at.asc&limit=50"
    )
    if not rows:
        print("No pending chunks")
        return

    print(f"Found {len(rows)} pending chunk(s)")
    provider = LocalSentenceTransformerProvider(MODEL, expected_dimension=EXPECTED_DIMENSIONS)
    result = provider.embed([row["content"] for row in rows])
    if result.dimensions != EXPECTED_DIMENSIONS:
        raise RuntimeError(f"Embedding dimension mismatch: {result.dimensions} != {EXPECTED_DIMENSIONS}")

    rpc_url = base + "/rest/v1/rpc/set_document_chunk_embedding"
    for row, vector in zip(rows, result.vectors):
        if len(vector) != EXPECTED_DIMENSIONS:
            raise RuntimeError(f"Chunk {row['id']} returned {len(vector)} dimensions")
        vector_text = "[" + ",".join(f"{float(x):.10g}" for x in vector) + "]"
        request_json(
            rpc_url,
            method="POST",
            payload={"chunk_id": row["id"], "embedding_text": vector_text},
        )
        print(f"Indexed chunk {row['id']}")

    print(f"Indexed {len(rows)} chunks with {MODEL} ({result.dimensions}D)")


if __name__ == "__main__":
    main()
