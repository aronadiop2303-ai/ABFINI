from documents.pipeline.document_pipeline import ingest_text_document


def test_ingest_markdown_document():
    result = ingest_text_document(b"Bonjour\n\nABFINI document test.", "test.md")
    assert result["metadata"].filename == "test.md"
    assert result["metadata"].content_sha256
    assert result["chunks"]


def test_reject_unsupported_format():
    try:
        ingest_text_document(b"x", "test.pdf")
    except ValueError as exc:
        assert "Unsupported format" in str(exc)
    else:
        raise AssertionError("Expected unsupported format error")
