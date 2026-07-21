import fitz  # PyMuPDF
import docx


class ParseError(Exception):
    """Raised when a document version cannot be parsed into usable text."""
    def __init__(self, reason: str, detail: str | None = None):
        self.reason = reason
        self.detail = detail
        super().__init__(reason if detail is None else f"{reason}: {detail}")


def parse_pdf(content: bytes) -> str:
    try:
        doc = fitz.open(stream=content, filetype="pdf")
    except fitz.FileDataError as e:
        raise ParseError("corrupt_or_invalid_pdf", detail=str(e))

    try:
        pages_text = [page.get_text() for page in doc]
    finally:
        doc.close()

    if not pages_text:
        raise ParseError("empty_pdf_no_pages")

    empty_page_numbers = [
        i + 1 for i, text in enumerate(pages_text) if not text.strip()
    ]

    if len(empty_page_numbers) == len(pages_text):
        raise ParseError("scanned_pdf_no_text_layer")

    if empty_page_numbers:
        raise ParseError(
            "partial_scanned_pdf",
            detail=f"pages with no extractable text: {empty_page_numbers}",
        )

    return "\n\n".join(pages_text)


def parse_docx(content: bytes) -> str:
    import io
    try:
        document = docx.Document(io.BytesIO(content))
    except Exception as e:
        raise ParseError("corrupt_or_invalid_docx", detail=str(e))

    paragraphs = [p.text for p in document.paragraphs]
    full_text = "\n\n".join(paragraphs)

    if not full_text.strip():
        raise ParseError("empty_docx_no_text")

    return full_text


def parse_document(content: bytes, filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext == "pdf":
        return parse_pdf(content)
    elif ext == "docx":
        return parse_docx(content)
    else:
        raise ParseError("unsupported_file_type", detail=ext)