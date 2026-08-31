"""Parser for UTF-8 text and Markdown documents."""
from .base import ParsedDocument


def parse_plain_text(content: bytes, filename: str) -> ParsedDocument:
    text = content.decode("utf-8-sig")
    return ParsedDocument(text=text, metadata={"filename": filename, "format": "text"})
