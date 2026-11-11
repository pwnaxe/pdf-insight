import pytest

from app.normalize import (
    CONTEXT_MAX,
    clean_context,
    normalise_amounts,
    normalise_dates,
    normalise_document_date,
    normalise_subtype,
)
from app.schemas import Amount, DateMention


def mention(date: str, context: str = "termin", precision: str = "day") -> DateMention:
    return DateMention(date=date, precision=precision, context=context)


def test_precision_is_derived_from_the_string_not_trusted() -> None:
    items = normalise_dates(
        [
            mention("2024", precision="day"),
            mention("2024-05", precision="year"),
            mention("2024-05-17", precision="month"),
        ]
    )
    assert [(i.date, i.precision) for i in items] == [
        ("2024", "year"),
        ("2024-05", "month"),
        ("2024-05-17", "day"),
    ]


@pytest.mark.parametrize("bad", ["2024-02-30", "2024-13", "12.03.2024", "24", "2024-5", "", "x"])
def test_invalid_dates_are_dropped(bad: str) -> None:
    assert normalise_dates([mention(bad), mention("2024-01-02", "ok")])[0].date == "2024-01-02"
    assert len(normalise_dates([mention(bad)])) == 0


def test_duplicate_dates_are_collapsed() -> None:
    items = normalise_dates([mention("2024-01-02", "Start"), mention("2024-01-02", " start ")])
    assert len(items) == 1


@pytest.mark.parametrize(
    "context",
    [
        "nie jest datą",
        "Not a date",
        "brak daty",
        "uncertain",
        "niepewne",
        "pominięto",
        "skipped",
        "numer faktury (nie jest datą)",
    ],
)
def test_dates_with_meta_context_are_dropped(context: str) -> None:
    assert normalise_dates([mention("2024-01-02", context)]) == []


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("termin płatności (pominięto dzień)", "termin płatności"),
        ("payment due [skipped] in March", "payment due in March"),
        ("zawarcie umowy (niepewne)", "zawarcie umowy"),
        ("termin płatności (14 dni)", "termin płatności (14 dni)"),
    ],
)
def test_parenthetical_meta_is_removed(raw: str, expected: str) -> None:
    assert clean_context(raw) == expected


def test_long_context_is_cut_at_a_word_boundary() -> None:
    text = " ".join(["słowo"] * 30)
    cleaned = clean_context(text)
    assert cleaned is not None
    assert len(cleaned) <= CONTEXT_MAX
    assert set(cleaned.split()) == {"słowo"}


def test_long_context_ending_exactly_on_a_word_keeps_it() -> None:
    text = "a" * 79 + " bbb"
    assert clean_context(text) == "a" * 79


def test_single_long_word_is_hard_cut() -> None:
    assert clean_context("x" * 200) == "x" * CONTEXT_MAX


def test_amount_with_meta_context_gets_a_generic_one() -> None:
    amounts = [
        Amount(value=1.0, currency="PLN", context="pominięto"),
        Amount(value=2.0, currency="PLN", context="opłata (niepewne)"),
    ]
    assert [a.context for a in normalise_amounts(amounts, "pl")] == ["kwota", "opłata"]
    assert normalise_amounts(amounts[:1], "en")[0].context == "amount"


def test_document_date_only_full_valid_day() -> None:
    assert normalise_document_date("2026-03-12") == "2026-03-12"
    for value in ("2026", "2026-03", "2026-02-30", "12.03.2026", "", None):
        assert normalise_document_date(value) is None


def test_subtype_is_lowercased_and_bounded() -> None:
    assert normalise_subtype(" CV ") == "cv"
    assert normalise_subtype("Protokół") == "protokół"
    assert normalise_subtype("") is None
    assert normalise_subtype(None) is None
    assert normalise_subtype("x" * 31) is None
