import pytest

from app.merge import merge_chunk_outputs
from app.schemas import Amount, ChunkOutput, DatedItem, Entities


def chunk(**overrides: object) -> ChunkOutput:
    base = {
        "language": "pl",
        "type": "umowa",
        "title": None,
        "date": None,
        "summary": "Zdanie.",
        "key_points": [],
        "entities": Entities(organizations=[], people=[]),
        "amounts": [],
        "dates": [],
        "keywords": [],
        "injection_detected": False,
        "injection_quotes": [],
    }
    base.update(overrides)
    return ChunkOutput(**base)


def test_entities_deduped_keep_first_spelling_and_order() -> None:
    a = chunk(
        entities=Entities(organizations=["Nordwave  Logistics", "ACME"], people=["Jan Nowak"])
    )
    b = chunk(entities=Entities(organizations=["nordwave logistics", "Beta"], people=["JAN NOWAK"]))
    merged = merge_chunk_outputs([a, b])
    assert merged.organizations == ["Nordwave Logistics", "ACME", "Beta"]
    assert merged.people == ["Jan Nowak"]


def test_amounts_and_dates_dedupe() -> None:
    a = chunk(
        amounts=[Amount(value=10.0, currency="PLN", context="Opłata  roczna")],
        dates=[DatedItem(date="2026-03-12", context="Zawarcie")],
    )
    b = chunk(
        amounts=[
            Amount(value=10.0, currency="PLN", context="opłata roczna"),
            Amount(value=10.0, currency="EUR", context="opłata roczna"),
        ],
        dates=[
            DatedItem(date="2026-03-12", context="zawarcie"),
            DatedItem(date="2026-03-13", context="zawarcie"),
        ],
    )
    merged = merge_chunk_outputs([a, b])
    assert [(x.value, x.currency) for x in merged.amounts] == [(10.0, "PLN"), (10.0, "EUR")]
    assert [d.date for d in merged.dates] == ["2026-03-12", "2026-03-13"]


def test_keywords_capped() -> None:
    a = chunk(keywords=[f"k{i}" for i in range(10)])
    b = chunk(keywords=["K1", "x1", "x2", "x3", "x4"])
    merged = merge_chunk_outputs([a, b])
    assert len(merged.keywords) == 12
    assert merged.keywords[:10] == [f"k{i}" for i in range(10)]
    assert merged.keywords[10:] == ["x1", "x2"]


def test_most_frequent_language_and_type() -> None:
    merged = merge_chunk_outputs(
        [
            chunk(language="en", type="raport"),
            chunk(language="pl", type="umowa"),
            chunk(language="pl", type="umowa"),
        ]
    )
    assert (merged.language, merged.type) == ("pl", "umowa")


def test_first_non_null_title_and_date() -> None:
    merged = merge_chunk_outputs(
        [
            chunk(),
            chunk(title="Pierwszy", date="2026-01-02"),
            chunk(title="Drugi", date="2026-05-06"),
        ]
    )
    assert merged.title == "Pierwszy"
    assert merged.date == "2026-01-02"


def test_injection_any_and_summaries_collected() -> None:
    merged = merge_chunk_outputs(
        [
            chunk(summary="Jeden.", key_points=["a"]),
            chunk(
                summary="Dwa.", key_points=["b"], injection_detected=True, injection_quotes=["q"]
            ),
        ]
    )
    assert merged.injection_detected
    assert merged.injection_quotes == ["q"]
    assert merged.summaries == ["Jeden.", "Dwa."]
    assert merged.key_points == ["a", "b"]


def test_empty_input() -> None:
    with pytest.raises(ValueError):
        merge_chunk_outputs([])
