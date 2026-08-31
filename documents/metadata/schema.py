"""Normalized metadata model for ingested documents."""
from dataclasses import dataclass, field
from typing import Any


@dataclass
class DocumentMetadata:
    filename: str
    mime_type: str | None = None
    size_bytes: int | None = None
    content_sha256: str | None = None
    source: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)
