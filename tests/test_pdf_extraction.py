import pytest

from app.core.errors import InvalidFileError, NoTextLayerError
from app.services.pdf_extraction import extract_text


def test_extracts_text_from_pdf_with_text_layer(sample_pdf_bytes: bytes) -> None:
    result = extract_text(sample_pdf_bytes)
    assert result.pages == 1
    assert "umowa" in result.text.lower()


def test_rejects_pdf_without_text_layer(blank_pdf_bytes: bytes) -> None:
    with pytest.raises(NoTextLayerError):
        extract_text(blank_pdf_bytes)


def test_rejects_bytes_that_are_not_a_pdf() -> None:
    with pytest.raises(InvalidFileError):
        extract_text(b"this is not a pdf")
