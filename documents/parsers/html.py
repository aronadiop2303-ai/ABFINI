"""HTML parser adapter. Requires beautifulsoup4."""
from .base import ParsedDocument


def parse_html(content: bytes, filename: str) -> ParsedDocument:
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(content, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    text = soup.get_text(" ", strip=True)
    return ParsedDocument(text=text, metadata={"filename": filename, "format": "html"})
