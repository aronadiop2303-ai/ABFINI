"""Minimal, dependency-light ABFINI document pipeline."""
import hashlib
from pathlib import Path

from documents.chunking.splitter import split_text
from documents.metadata.schema import DocumentMetadata
from documents.parsers.base import ParsedDocument
from documents.parsers.plain_text import parse_plain_text

SUPPORTED_TEXT_EXTENSIONS = {".txt", ".md", ".markdown"}


def ingest_text_document(content: bytes, filename: str, source: str | None = None) -> dict:
    """Parse a text/Markdown document and return normalized chunks + metadata."""
    suffix = Path(filename).suffix.lower()
    if suffix not in SUPPORTED_TEXT_EXTENSIONS:
        raise ValueError(f"Unsupported format for v0.1.1: {suffix or 'unknown'}")

    parsed: ParsedDocument = parse_plain_text(content, filename)
    digest = hashlib.sha256(content).hexdigest()
    metadata = DocumentMetadata(
        filename=filename,
        size_bytes=len(content),
        content_sha256=digest,
        source=source,
        extra=parsed.metadata,
    )
    chunks = split_text(parsed.text)
    return {
        "metadata": metadata,
        "text": parsed.text,
        "chunks": chunks,
    }
