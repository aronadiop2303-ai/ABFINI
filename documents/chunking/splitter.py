"""Deterministic text chunking for the first ABFINI document pipeline."""


def split_text(text: str, chunk_size: int = 1200, overlap: int = 150) -> list[str]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be > 0")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be >= 0 and < chunk_size")

    normalized = " ".join(text.split())
    if not normalized:
        return []

    chunks: list[str] = []
    start = 0
    step = chunk_size - overlap
    while start < len(normalized):
        chunk = normalized[start : start + chunk_size].strip()
        if chunk:
            chunks.append(chunk)
        start += step
    return chunks
