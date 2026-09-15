from dataclasses import dataclass

import pymupdf

from app.core.errors import InvalidFileError, NoTextLayerError

# Scanned PDFs produce ~0 extractable characters; a real text-layer document
# clears this by a wide margin even on a single sparse page. This is the drop-in
# point for OCR later: replace the raise below with a call to an OCR fallback
# (pdf2image + pytesseract) instead of failing — nothing else in the pipeline
# needs to change.
MIN_TEXT_CHARS = 30


@dataclass
class ExtractedDocument:
    text: str
    pages: int


def extract_text(pdf_bytes: bytes) -> ExtractedDocument:
    try:
        document = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    except Exception as exc:
        raise InvalidFileError("Nie udało się odczytać pliku PDF.") from exc

    try:
        pages = document.page_count
        text = "\n".join(page.get_text() for page in document)
    finally:
        document.close()

    if len(text.strip()) < MIN_TEXT_CHARS:
        raise NoTextLayerError()

    return ExtractedDocument(text=text, pages=pages)
