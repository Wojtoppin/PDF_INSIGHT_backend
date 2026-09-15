import pytest
from pydantic import ValidationError

from app.schemas.analysis import AnalysisResult

VALID_PAYLOAD = {
    "document": {
        "fileName": "umowa.pdf",
        "pages": 4,
        "language": "pl",
        "type": "umowa",
        "title": "Umowa serwisowa",
        "date": "2026-09-01",
    },
    "summary": "Umowa okresla zasady wspolpracy pomiedzy stronami.",
    "keyPoints": ["Okres umowy 12 mies.", "Wynagrodzenie miesieczne", "Okres wypowiedzenia 30 dni"],
    "entities": {"organizations": ["Przyklad sp. z o.o."], "people": []},
    "amounts": [{"value": 12500.0, "currency": "PLN", "context": "wynagrodzenie"}],
    "dates": [{"date": "2026-10-01", "context": "termin platnosci"}],
    "keywords": ["serwis", "SLA"],
}


def test_valid_payload_passes() -> None:
    result = AnalysisResult.model_validate(VALID_PAYLOAD)
    assert result.document.type == "umowa"
    assert result.document.language == "pl"


def test_extra_fields_are_silently_dropped() -> None:
    payload = {**VALID_PAYLOAD, "unexpectedField": "should be ignored"}
    payload["document"] = {**VALID_PAYLOAD["document"], "confidenceScore": 0.9}
    result = AnalysisResult.model_validate(payload)
    assert not hasattr(result, "unexpectedField")


def test_invalid_date_is_rejected() -> None:
    payload = {**VALID_PAYLOAD, "document": {**VALID_PAYLOAD["document"], "date": "01-09-2026"}}
    with pytest.raises(ValidationError):
        AnalysisResult.model_validate(payload)


def test_invalid_currency_is_rejected() -> None:
    payload = {**VALID_PAYLOAD, "amounts": [{"value": 100.0, "currency": "ZZZ", "context": "x"}]}
    with pytest.raises(ValidationError):
        AnalysisResult.model_validate(payload)


def test_unknown_document_type_is_rejected() -> None:
    payload = {**VALID_PAYLOAD, "document": {**VALID_PAYLOAD["document"], "type": "cos_innego"}}
    with pytest.raises(ValidationError):
        AnalysisResult.model_validate(payload)


def test_too_few_key_points_is_rejected() -> None:
    payload = {**VALID_PAYLOAD, "keyPoints": ["only one"]}
    with pytest.raises(ValidationError):
        AnalysisResult.model_validate(payload)


def test_null_document_date_is_allowed() -> None:
    payload = {**VALID_PAYLOAD, "document": {**VALID_PAYLOAD["document"], "date": None}}
    result = AnalysisResult.model_validate(payload)
    assert result.document.date is None
