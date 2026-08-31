"""Common parser interface for ABFINI documents."""
from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass
class ParsedDocument:
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)


class DocumentParser(Protocol):
    def parse(self, content: bytes, filename: str) -> ParsedDocument:
        ...
