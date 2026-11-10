import re
from datetime import date
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

DocumentType = Literal["faktura", "umowa", "oferta", "raport", "inne"]

_ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_LANGUAGE = re.compile(r"^[a-z]{2}$")
_CURRENCY = re.compile(r"^[A-Z]{3}$")

_ABBREVIATIONS = (
    "r|ul|nr|sp|poz|art|ust|pkt|tj|np|itd|itp|ok|godz|al|os|pl|ds|dr|mgr|inż|prof|tel|wg|ww|"
    "m\\.in|zob|tzw|tzn|ew|dot|inc|ltd|co|no|vs"
)
_ABBREVIATION_DOT = re.compile(rf"\b({_ABBREVIATIONS}|[A-Za-z]\.[A-Za-z]|o\.o)\.", re.IGNORECASE)
_SENTENCE_BREAK = re.compile(r"(?<=[.!?…])\s+(?=[A-ZĄĆĘŁŃÓŚŹŻ„\"(])")
_PLACEHOLDER = "\x00"


def count_sentences(text: str) -> int:
    protected = _ABBREVIATION_DOT.sub(lambda m: m.group(1) + _PLACEHOLDER, text)
    parts = _SENTENCE_BREAK.split(protected.strip())
    return sum(1 for part in parts if re.search(r"\w", part))


def _iso_date(value: str) -> str:
    if not _ISO_DATE.match(value):
        raise ValueError("date must be YYYY-MM-DD")
    date.fromisoformat(value)
    return value


def _language(value: str) -> str:
    if not _LANGUAGE.match(value):
        raise ValueError("language must be a lowercase ISO 639-1 code")
    return value


def _currency(value: str) -> str:
    if not _CURRENCY.match(value):
        raise ValueError("currency must be a 3-letter uppercase ISO 4217 code")
    return value


def _optional_iso_date(value: str | None) -> str | None:
    return None if value is None else _iso_date(value)


IsoDate = Annotated[str, AfterValidator(_iso_date)]
OptionalIsoDate = Annotated[str | None, AfterValidator(_optional_iso_date)]
Language = Annotated[str, AfterValidator(_language)]
Currency = Annotated[str, AfterValidator(_currency)]


def _list_length(low: int, high: int):
    def check(items: list[str]) -> list[str]:
        if not low <= len(items) <= high:
            raise ValueError(f"expected {low}..{high} items, got {len(items)}")
        return items

    return AfterValidator(check)


def _sentence_range(low: int, high: int):
    def check(text: str) -> str:
        count = count_sentences(text)
        if not low <= count <= high:
            raise ValueError(f"expected {low}..{high} sentences, got {count}")
        return text

    return AfterValidator(check)


KeyPoints = Annotated[list[str], _list_length(3, 7)]
Summary = Annotated[str, _sentence_range(2, 6)]
ChunkSummary = Annotated[str, _sentence_range(1, 5)]


class CamelModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="forbid",
    )


class DocumentInfo(CamelModel):
    file_name: str
    pages: Annotated[int, Field(ge=1)]
    language: Language
    type: DocumentType
    title: str | None
    date: OptionalIsoDate


class Entities(CamelModel):
    organizations: list[str]
    people: list[str]


class Amount(CamelModel):
    value: float
    currency: Currency
    context: str


class DatedItem(CamelModel):
    date: IsoDate
    context: str


class AnalysisResult(CamelModel):
    document: DocumentInfo
    summary: Summary
    key_points: KeyPoints
    entities: Entities
    amounts: list[Amount]
    dates: list[DatedItem]
    keywords: list[str]
    suspected_injection: bool
    warnings: list[str]


class ModelOutput(CamelModel):
    language: Language
    type: DocumentType
    title: str | None
    date: OptionalIsoDate
    summary: Summary
    key_points: KeyPoints
    entities: Entities
    amounts: list[Amount]
    dates: list[DatedItem]
    keywords: list[str]
    injection_detected: bool
    injection_quotes: list[str]


class ChunkOutput(CamelModel):
    language: Language
    type: DocumentType
    title: str | None
    date: OptionalIsoDate
    summary: ChunkSummary
    key_points: list[str]
    entities: Entities
    amounts: list[Amount]
    dates: list[DatedItem]
    keywords: list[str]
    injection_detected: bool
    injection_quotes: list[str]


class FinalOutput(CamelModel):
    summary: Summary
    key_points: KeyPoints
