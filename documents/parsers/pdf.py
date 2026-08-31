"""PDF parser adapter. Requires PyMuPDF (package: pymupdf)."""
from .base import ParsedDocument


def parse_pdf(content: bytes, filename: str) -> ParsedDocument:
    import fitz

    document = fitz.open(stream=content, filetype="pdf")
    pages = [page.get_text("text") for page in document]
    text = "\n\n".join(pages).strip()
    return ParsedDocument(
        text=text,
        metadata={"filename": filename, "format": "pdf", "pages": len(document)},
    )
