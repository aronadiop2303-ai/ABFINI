"""Embed pending ABFINI chunks and write vectors to Supabase.

Required environment variables:
  SUPABASE_URL
  SUPABASE_SERVICE_ROLE_KEY
  EMBEDDING_MODEL (optional; must produce 768 dimensions)
"""
import json
import os
import urllib.request

from .local_sentence_transformers import LocalSentenceTransformerProvider

MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-base-en-v1.5")


def request_json(url: str, method: str = "GET", payload=None):
    body = None if payload is None else json.dumps(payload).encode()
    headers = {"apikey": os.environ["SUPABASE_SERVICE_ROLE_KEY"], "Authorization": f"Bearer {os.environ['SUPABASE_SERVICE_ROLE_KEY']}"}
    if body is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=60) as response:
        return json.loads(response.read().decode())


def main() -> None:
    base = os.environ["SUPABASE_URL"].rstrip("/")
    rows = request_json(base + "/rest/v1/document_chunks?select=id,content&embedding=is.null&order=created_at.asc&limit=50")
    if not rows:
        print("No pending chunks")
        return

    provider = LocalSentenceTransformerProvider(MODEL, expected_dimension=768)
    result = provider.embed([row["content"] for row in rows])
    rpc_url = base + "/rest/v1/rpc/set_document_chunk_embedding"
    for row, vector in zip(rows, result.vectors):
        request_json(rpc_url, method="POST", payload={"chunk_id": row["id"], "embedding_text": str(vector).replace("'", "")})
    print(f"Indexed {len(rows)} chunks with {MODEL} ({result.dimensions}D)")


if __name__ == "__main__":
    main()
