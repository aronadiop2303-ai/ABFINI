"""Embed pending ABFINI chunks and write vectors to Supabase."""
import json
import os
import urllib.error
import urllib.parse
import urllib.request

from .local_sentence_transformers import LocalSentenceTransformerProvider

MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-base-en-v1.5")
EXPECTED_DIMENSIONS = 768


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

    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw) if raw else None
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode(errors="replace")
        raise RuntimeError(f"Supabase HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Supabase connection error: {exc.reason}") from exc


def normalize_supabase_url(raw_url: str) -> str:
    """Return only the Supabase project origin, never a REST route."""
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


def main() -> None:
    base = normalize_supabase_url(os.environ.get("SUPABASE_URL", ""))

    query = urllib.parse.urlencode(
        {
            "select": "id,content",
            "embedding": "is.null",
            "order": "created_at.asc",
            "limit": "50",
        }
    )
    chunks_url = f"{base}/rest/v1/document_chunks?{query}"

    rows = request_json(chunks_url)
    if not rows:
        print("No pending chunks")
        return

    print(f"Found {len(rows)} pending chunk(s)")
    provider = LocalSentenceTransformerProvider(
        MODEL, expected_dimension=EXPECTED_DIMENSIONS
    )
    result = provider.embed([row["content"] for row in rows])
    if result.dimensions != EXPECTED_DIMENSIONS:
        raise RuntimeError(
            f"Embedding dimension mismatch: {result.dimensions} != {EXPECTED_DIMENSIONS}"
        )

    rpc_url = f"{base}/rest/v1/rpc/set_document_chunk_embedding"
    for row, vector in zip(rows, result.vectors):
        if len(vector) != EXPECTED_DIMENSIONS:
            raise RuntimeError(
                f"Chunk {row['id']} returned {len(vector)} dimensions"
            )

        vector_text = "[" + ",".join(repr(float(x)) for x in vector) + "]"
        request_json(
            rpc_url,
            method="POST",
            payload={
                "chunk_id": row["id"],
                "embedding_text": vector_text,
            },
        )
        print(f"Indexed chunk {row['id']}")

    print(f"Indexed {len(rows)} chunks with {MODEL} ({result.dimensions}D)")


if __name__ == "__main__":
    main()
