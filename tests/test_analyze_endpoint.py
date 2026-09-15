import json

from fastapi.testclient import TestClient

from app.api.routes import get_llm_client
from app.main import app
from app.services.llm.base import LLMUnavailableError

VALID_RESPONSE = {
    "document": {
        "fileName": "test.pdf",
        "pages": 1,
        "language": "pl",
        "type": "umowa",
        "title": "Umowa testowa",
        "date": "2026-01-01",
    },
    "summary": "To jest testowe podsumowanie dokumentu opisujace warunki umowy.",
    "keyPoints": ["Punkt pierwszy", "Punkt drugi", "Punkt trzeci"],
    "entities": {"organizations": ["Firma sp. z o.o."], "people": []},
    "amounts": [{"value": 1000.0, "currency": "PLN", "context": "wynagrodzenie"}],
    "dates": [{"date": "2026-02-01", "context": "termin platnosci"}],
    "keywords": ["umowa", "test"],
}


class FakeLLMClient:
    def __init__(self, responses: list[str]) -> None:
        self._responses = responses
        self.calls = 0

    def generate_structured(self, *, system_prompt: str, user_content: str, schema: type) -> str:
        response = self._responses[min(self.calls, len(self._responses) - 1)]
        self.calls += 1
        return response


def test_analyze_success(sample_pdf_bytes: bytes) -> None:
    app.dependency_overrides[get_llm_client] = lambda: FakeLLMClient([json.dumps(VALID_RESPONSE)])
    try:
        client = TestClient(app)
        response = client.post(
            "/api/analyze",
            files={"file": ("test.pdf", sample_pdf_bytes, "application/pdf")},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["document"]["type"] == "umowa"


def test_analyze_retries_once_then_fails(sample_pdf_bytes: bytes) -> None:
    app.dependency_overrides[get_llm_client] = lambda: FakeLLMClient(["not json", "still not json"])
    try:
        client = TestClient(app)
        response = client.post(
            "/api/analyze",
            files={"file": ("test.pdf", sample_pdf_bytes, "application/pdf")},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 502


class FlakyLLMClient:
    """Simulates a transient provider outage (e.g. Gemini 503) on every call."""

    def generate_structured(self, *, system_prompt: str, user_content: str, schema: type) -> str:
        raise LLMUnavailableError("503 UNAVAILABLE: model overloaded")


def test_analyze_returns_clean_error_when_provider_is_unavailable(sample_pdf_bytes: bytes) -> None:
    app.dependency_overrides[get_llm_client] = lambda: FlakyLLMClient()
    try:
        client = TestClient(app)
        response = client.post(
            "/api/analyze",
            files={"file": ("test.pdf", sample_pdf_bytes, "application/pdf")},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 502
    assert "error" in response.json()


def test_analyze_rejects_pdf_without_text_layer(blank_pdf_bytes: bytes) -> None:
    client = TestClient(app)
    response = client.post(
        "/api/analyze",
        files={"file": ("scan.pdf", blank_pdf_bytes, "application/pdf")},
    )
    assert response.status_code == 422


def test_analyze_rejects_non_pdf_upload() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/analyze",
        files={"file": ("notes.txt", b"hello", "text/plain")},
    )
    assert response.status_code == 400
