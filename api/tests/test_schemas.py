import copy

import pytest
from pydantic import ValidationError

from app.schemas import AnalysisResult, ChunkOutput, count_sentences, date_precision

VALID = {
    "document": {
        "fileName": "umowa.pdf",
        "pages": 12,
        "language": "pl",
        "type": "umowa",
        "subtype": None,
        "title": "Umowa ramowa nr 14/2026",
        "date": "2026-03-12",
    },
    "summary": "Umowa dotyczy wdrożenia systemu CRM. Wynagrodzenie wynosi 184 500,00 zł netto.",
    "keyPoints": ["Wdrożenie CRM", "184 500 PLN netto", "Zaliczka 30%"],
    "entities": {
        "organizations": ["Nordwave Logistics sp. z o.o.", "Kwadrat Software S.A."],
        "people": ["Anna Kowalczyk"],
    },
    "amounts": [{"value": 184500.0, "currency": "PLN", "context": "wdrożenie netto"}],
    "dates": [{"date": "2026-03-12", "precision": "day", "context": "data zawarcia"}],
    "keywords": ["CRM"],
    "suspectedInjection": False,
    "warnings": [],
}


def variant(**changes: object) -> dict:
    data = copy.deepcopy(VALID)
    data.update(changes)
    return data


def test_valid_roundtrip_uses_camel_case() -> None:
    result = AnalysisResult.model_validate(VALID)
    dumped = result.model_dump(by_alias=True)
    assert dumped == VALID
    assert result.document.file_name == "umowa.pdf"


def test_currency_symbol_rejected() -> None:
    data = variant(amounts=[{"value": 1.0, "currency": "zł", "context": "x"}])
    with pytest.raises(ValidationError):
        AnalysisResult.model_validate(data)


def test_bad_dates_rejected() -> None:
    with pytest.raises(ValidationError):
        AnalysisResult.model_validate(
            variant(dates=[{"date": "2026-02-30", "precision": "day", "context": "x"}])
        )
    with pytest.raises(ValidationError):
        AnalysisResult.model_validate(
            variant(dates=[{"date": "12.03.2026", "precision": "day", "context": "x"}])
        )
    data = copy.deepcopy(VALID)
    data["document"]["date"] = "2026-13-01"
    with pytest.raises(ValidationError):
        AnalysisResult.model_validate(data)


@pytest.mark.parametrize(
    ("value", "precision"),
    [("2024", "year"), ("2024-05", "month"), ("2024-05-17", "day")],
)
def test_reduced_precision_dates_are_valid(value: str, precision: str) -> None:
    item = {"date": value, "precision": precision, "context": "x"}
    result = AnalysisResult.model_validate(variant(dates=[item]))
    assert result.dates[0].precision == precision
    assert date_precision(value) == precision


@pytest.mark.parametrize(
    ("value", "precision"),
    [
        ("2024", "day"),
        ("2024-05", "year"),
        ("2024-13", "month"),
        ("24", "year"),
        ("2024-5", "month"),
    ],
)
def test_inconsistent_or_invalid_date_precision_rejected(value: str, precision: str) -> None:
    item = {"date": value, "precision": precision, "context": "x"}
    with pytest.raises(ValidationError):
        AnalysisResult.model_validate(variant(dates=[item]))


def test_document_date_must_be_a_full_day() -> None:
    for value in ("2026", "2026-03"):
        data = copy.deepcopy(VALID)
        data["document"]["date"] = value
        with pytest.raises(ValidationError):
            AnalysisResult.model_validate(data)


def test_subtype_is_optional_lowercase_and_short() -> None:
    data = copy.deepcopy(VALID)
    del data["document"]["subtype"]
    assert AnalysisResult.model_validate(data).document.subtype is None
    for good in ("cv", "protokół"):
        data["document"]["subtype"] = good
        assert AnalysisResult.model_validate(data).document.subtype == good
    for bad in ("CV", "", " cv", "x" * 31):
        data["document"]["subtype"] = bad
        with pytest.raises(ValidationError):
            AnalysisResult.model_validate(data)


def test_key_points_bounds() -> None:
    with pytest.raises(ValidationError):
        AnalysisResult.model_validate(variant(keyPoints=[f"p{i}" for i in range(8)]))
    with pytest.raises(ValidationError):
        AnalysisResult.model_validate(variant(keyPoints=["a", "b"]))
    AnalysisResult.model_validate(variant(keyPoints=[f"p{i}" for i in range(7)]))


def test_missing_field_rejected() -> None:
    data = copy.deepcopy(VALID)
    del data["warnings"]
    with pytest.raises(ValidationError):
        AnalysisResult.model_validate(data)


def test_document_constraints() -> None:
    for key, value in [("pages", 0), ("language", "PL"), ("language", "pol"), ("type", "pismo")]:
        data = copy.deepcopy(VALID)
        data["document"][key] = value
        with pytest.raises(ValidationError):
            AnalysisResult.model_validate(data)


def test_summary_sentence_bounds() -> None:
    with pytest.raises(ValidationError):
        AnalysisResult.model_validate(variant(summary="Tylko jedno zdanie."))
    with pytest.raises(ValidationError):
        AnalysisResult.model_validate(variant(summary=" ".join(["To jest zdanie."] * 7)))


def test_chunk_output_allows_single_sentence_summary() -> None:
    chunk = {
        "language": "pl",
        "type": "inne",
        "subtype": None,
        "title": None,
        "date": None,
        "summary": "Jedno zdanie.",
        "keyPoints": [],
        "entities": {"organizations": [], "people": []},
        "amounts": [],
        "dates": [],
        "keywords": [],
        "injectionDetected": False,
        "injectionQuotes": [],
    }
    assert ChunkOutput.model_validate(chunk).summary == "Jedno zdanie."


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Jedno. Drugie. Trzecie.", 3),
        ("Umowa nr 14/2026 została zawarta w dniu 12.03.2026 r. między stronami.", 1),
        ("Siedziba: ul. Portowa 18, Gdańsk. Strony podpisały umowę.", 2),
        ("Nordwave Logistics sp. z o.o. zawarła umowę z Kwadrat Software S.A. na rok. Koniec.", 2),
        ("Wynagrodzenie to 184 500,00 zł netto. Płatne w 14 dni. Dodatkowo 8 600 EUR rocznie.", 3),
        ("Czy to działa? Tak! Na pewno.", 3),
        ("", 0),
    ],
)
def test_count_sentences(text: str, expected: int) -> None:
    assert count_sentences(text) == expected
