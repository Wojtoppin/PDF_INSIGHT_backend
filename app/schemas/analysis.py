from __future__ import annotations

from datetime import date as date_type
from typing import Literal

import pycountry
from pydantic import BaseModel, ConfigDict, Field, field_validator


class StrictModel(BaseModel):
    """Enforces every field we define, but silently drops any extra field the
    AI adds that we didn't ask for (see grilling decision: extra fields aren't
    a reason to fail validation and burn our one retry)."""

    model_config = ConfigDict(extra="ignore")


def _validate_iso_date(value: str) -> str:
    try:
        date_type.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"'{value}' nie jest poprawną datą ISO 8601") from exc
    return value


class DocumentMeta(StrictModel):
    fileName: str
    pages: int = Field(ge=1)
    language: str
    type: Literal["faktura", "umowa", "oferta", "raport", "inne"]
    title: str
    date: str | None = None

    @field_validator("language")
    @classmethod
    def check_language(cls, v: str) -> str:
        if not pycountry.languages.get(alpha_2=v.lower()):
            raise ValueError(f"'{v}' nie jest poprawnym kodem języka ISO 639-1")
        return v.lower()

    @field_validator("date")
    @classmethod
    def check_date(cls, v: str | None) -> str | None:
        return _validate_iso_date(v) if v is not None else v


class Entities(StrictModel):
    organizations: list[str] = Field(default_factory=list)
    people: list[str] = Field(default_factory=list)


class Amount(StrictModel):
    value: float
    currency: str
    context: str

    @field_validator("currency")
    @classmethod
    def check_currency(cls, v: str) -> str:
        if not pycountry.currencies.get(alpha_3=v.upper()):
            raise ValueError(f"'{v}' nie jest poprawnym kodem waluty ISO 4217")
        return v.upper()


class DateEntry(StrictModel):
    date: str
    context: str

    @field_validator("date")
    @classmethod
    def check_date(cls, v: str) -> str:
        return _validate_iso_date(v)


class AnalysisResult(StrictModel):
    document: DocumentMeta
    summary: str
    keyPoints: list[str] = Field(min_length=3, max_length=7)
    entities: Entities
    amounts: list[Amount] = Field(default_factory=list)
    dates: list[DateEntry] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
