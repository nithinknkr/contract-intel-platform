from pathlib import Path

import pytest

from app.services.parsing import parse_document, ParseError

FIXTURES = Path(__file__).parent.parent / "fixtures"


def test_parse_valid_pdf():
    content = (FIXTURES / "sample_valid.pdf").read_bytes()
    text = parse_document(content, "sample_valid.pdf")
    assert "liability clause" in text


def test_parse_valid_docx():
    content = (FIXTURES / "sample_valid.docx").read_bytes()
    text = parse_document(content, "sample_valid.docx")
    assert "auto-renewal clause" in text


def test_parse_corrupt_pdf_raises_parse_error():
    content = (FIXTURES / "corrupt.pdf").read_bytes()
    with pytest.raises(ParseError) as exc_info:
        parse_document(content, "corrupt.pdf")
    assert exc_info.value.reason == "corrupt_or_invalid_pdf"


def test_parse_corrupt_docx_raises_parse_error():
    content = b"this is not a real docx"
    with pytest.raises(ParseError) as exc_info:
        parse_document(content, "fake.docx")
    assert exc_info.value.reason == "corrupt_or_invalid_docx"