import os

# Settings are instantiated at import time (app/config.py). Set a dummy key
# before any test imports app.config transitively, so tests don't need a real
# .env file or Gemini credentials.
os.environ.setdefault("GEMINI_API_KEY", "test-key-for-tests")

import pymupdf
import pytest


@pytest.fixture
def sample_pdf_bytes() -> bytes:
    document = pymupdf.open()
    page = document.new_page()
    page.insert_text(
        (72, 72),
        "To jest przykladowa umowa serwisowa pomiedzy stronami. " * 3,
    )
    pdf_bytes = document.tobytes()
    document.close()
    return pdf_bytes


@pytest.fixture
def blank_pdf_bytes() -> bytes:
    document = pymupdf.open()
    document.new_page()
    pdf_bytes = document.tobytes()
    document.close()
    return pdf_bytes
