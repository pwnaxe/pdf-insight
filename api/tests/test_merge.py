import pytest

from app.merge import merge_chunk_outputs
from app.schemas import Amount, ChunkOutput, DateMention, Entities


def chunk(**overrides: object) -> ChunkOutput:
    base = {
        "language": "pl",
        "type": "umowa",
        "subtype": None,
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


def test_organizations_with_legal_form_merge_keep_full_name() -> None:
    a = chunk(entities=Entities(organizations=["Nordwave Logistics", "Acme GmbH"], people=[]))
    b = chunk(
        entities=Entities(
            organizations=["Nordwave Logistics sp. z o.o.", "ACME", "Kwadrat Software S.A."],
            people=[],
        )
    )
    c = chunk(
        entities=Entities(organizations=["Kwadrat Software", "Foo Ltd", "Foo Inc."], people=[])
    )
    merged = merge_chunk_outputs([a, b, c])
    assert merged.organizations == [
        "Nordwave Logistics sp. z o.o.",
        "Acme GmbH",
        "Kwadrat Software S.A.",
        "Foo Inc.",
    ]


@pytest.mark.parametrize("suffix", ["sp. j.", "sp. k.", "S.A."])
def test_organization_suffix_variants(suffix: str) -> None:
    merged = merge_chunk_outputs(
        [chunk(entities=Entities(organizations=["Beta", f"Beta {suffix}"], people=[]))]
    )
    assert merged.organizations == [f"Beta {suffix}"]


def test_amounts_and_dates_dedupe() -> None:
    a = chunk(
        amounts=[Amount(value=10.0, currency="PLN", context="Opłata  roczna")],
        dates=[DateMention(date="2026-03-12", precision="day", context="Zawarcie")],
    )
    b = chunk(
        amounts=[
            Amount(value=10.0, currency="PLN", context="opłata roczna"),
            Amount(value=10.0, currency="EUR", context="opłata roczna"),
        ],
        dates=[
            DateMention(date="2026-03-12", precision="day", context="zawarcie"),
            DateMention(date="2026-03-13", precision="day", context="zawarcie"),
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
    assert merged.summaries == ["Jeden.", "Dwa."]
    assert merged.key_points == ["a", "b"]


def test_empty_input() -> None:
    with pytest.raises(ValueError):
        merge_chunk_outputs([])


def test_amounts_near_identical_context_deduped() -> None:
    merged = merge_chunk_outputs(
        [
            chunk(
                amounts=[Amount(value=5.0, currency="PLN", context="Opłata miesięczna za hosting")]
            ),
            chunk(
                amounts=[Amount(value=5.0, currency="PLN", context="Opłata miesięczna za hostingu")]
            ),
            chunk(amounts=[Amount(value=5.0, currency="PLN", context="Kara umowna")]),
        ]
    )
    assert [a.context for a in merged.amounts] == [
        "Opłata miesięczna za hosting",
        "Kara umowna",
    ]


def test_amounts_and_dates_capped_in_document_order() -> None:
    amounts = [Amount(value=float(i), currency="PLN", context=f"pozycja {i}") for i in range(30)]
    dates = [
        DateMention(date=f"2026-01-{i:02d}", precision="day", context=f"termin {i}")
        for i in range(1, 29)
    ]
    merged = merge_chunk_outputs(
        [
            chunk(amounts=amounts[:15], dates=dates[:14]),
            chunk(amounts=amounts[15:], dates=dates[14:]),
        ]
    )
    assert [a.value for a in merged.amounts] == [float(i) for i in range(20)]
    assert [d.date for d in merged.dates] == [f"2026-01-{i:02d}" for i in range(1, 21)]
