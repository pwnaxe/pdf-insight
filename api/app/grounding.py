import re
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from app.injection import injection_starts
from app.pdf import PageText
from app.schemas import Amount, DatedItem

_CENT = Decimal("0.01")

_SEPARATORS = "    .,'’"
_NUMBER = re.compile(
    rf"(?<![\w.,'’])(?P<int>\d{{1,3}}(?:[{_SEPARATORS}]\d{{3}})+|\d+)"
    r"(?:[.,](?P<frac>\d{1,2}))?(?!\d|[./-]\d)"
)
_PERCENT = re.compile(r"\s*%")
_CURRENCY_WORDS = r"zł|zl|pln|eur|usd|gbp|chf|czk|€|\$|£"
_CURRENCY_AFTER = re.compile(rf"\s*(?:{_CURRENCY_WORDS})(?![^\W\d_])", re.IGNORECASE)
_CURRENCY_BEFORE = re.compile(rf"(?:{_CURRENCY_WORDS})\s*$", re.IGNORECASE)
# a bare small integer (a list number, a count) is not money unless a currency is next to it
_BARE_MONEY_MIN = 1000

_DATE_SEP = r"[./-]"
_NUMERIC_DATE = re.compile(
    rf"(?<![\d./-])(\d{{1,2}}){_DATE_SEP}(\d{{1,2}}){_DATE_SEP}(\d{{4}}|\d{{2}})(?!\d|[./-]\d)"
)
_ISO_DATE = re.compile(r"(?<![\d./-])(\d{4})[./-](\d{1,2})[./-](\d{1,2})(?!\d|[./-]\d)")
_NUMERIC_MONTH = re.compile(r"(?<![\d./-])(\d{1,2})[./-](\d{4})(?!\d)")
_ISO_MONTH = re.compile(r"(?<![\d./-])(\d{4})-(\d{1,2})(?![\d-])")
_YEAR = re.compile(r"(?<!\d)(\d{4})(?!\d)")

_MONTH_FORMS: dict[int, str] = {
    1: r"stycz(?:eń|en|nia|niu|niem)|january|jan",
    2: r"lut(?:y|ego|emu|ym)|february|feb",
    3: r"mar(?:zec|ca|cu|cem)|march|mar",
    4: r"kwie(?:cień|cien|tnia|tniu|tniem)|april|apr",
    5: r"maj(?:a|u|em)?|may",
    6: r"czerw(?:iec|ca|cu|cem)|june|jun",
    7: r"lip(?:iec|ca|cu|cem)|july|jul",
    8: r"sierp(?:ień|ien|nia|niu|niem)|august|aug",
    9: r"wrze(?:sień|sien|śnia|snia|śniu|sniu|śniem|sniem)|september|sept|sep",
    10: r"paźdz(?:iernik\w*)|pazdz(?:iernik\w*)|october|oct",
    11: r"listopad(?:a|zie|em)?|november|nov",
    12: r"grud(?:zień|zien|nia|niu|niem)|december|dec",
}
_MONTH_WORDS = "|".join(_MONTH_FORMS.values())
_MONTH_BY_WORD = [
    (month, re.compile(forms, re.IGNORECASE)) for month, forms in _MONTH_FORMS.items()
]
_MONTH = rf"(?P<month>{_MONTH_WORDS})\b"
_ORDINAL = r"(?:st|nd|rd|th)?"
_DAY_MONTH_YEAR = re.compile(
    rf"(?<![\d./-])(\d{{1,2}}){_ORDINAL}\.?\s+{_MONTH}\.?,?\s+(\d{{4}})(?!\d)", re.IGNORECASE
)
_MONTH_DAY_YEAR = re.compile(
    rf"\b{_MONTH}\.?\s+(\d{{1,2}}){_ORDINAL},?\s+(\d{{4}})(?!\d)", re.IGNORECASE
)
_MONTH_YEAR = re.compile(rf"\b{_MONTH}\.?,?\s+(\d{{4}})(?!\d)", re.IGNORECASE)

_QUOTES_DASHES = str.maketrans(
    {
        "„": '"',
        "“": '"',
        "”": '"',
        "«": '"',
        "»": '"',
        "‘": "'",
        "’": "'",
        "–": "-",
        "—": "-",
        "−": "-",
    }
)
_NON_WORD = re.compile(r"[\W_]+")
_LEGAL_FORMS = [
    "sp z o o sp k",
    "sp z o o",
    "spółka z ograniczoną odpowiedzialnością",
    "spolka z ograniczona odpowiedzialnoscia",
    "spółka akcyjna",
    "spolka akcyjna",
    "sp k",
    "sp j",
    "sp p",
    "s a",
    "sa",
    "ltd",
    "limited",
    "gmbh",
    "inc",
    "incorporated",
    "llc",
    "corp",
    "corporation",
    "plc",
    "ag",
    "bv",
    "srl",
]
_LEGAL_FORM = re.compile(rf"\b(?:{'|'.join(_LEGAL_FORMS)})\b")
_TITLES = {"dr", "mgr", "inz", "inż", "prof", "hab", "pan", "pani", "mr", "mrs", "ms"}
_SURNAME_MIN = 3
_PERSON_WINDOW = 3


@dataclass(frozen=True)
class GroundedFields:
    amounts: list[Amount]
    dates: list[DatedItem]
    document_date: str | None
    organizations: list[str]
    people: list[str]
    dropped: int


def _clean_corpus(pages: list[PageText]) -> str:
    # lines of an embedded instruction are untrusted, so values stated only there are not evidence
    kept: list[str] = []
    for page in pages:
        lines = page.text.split("\n")
        skip: set[int] = set()
        offset = 0
        starts = injection_starts(page.text)
        for index, line in enumerate(lines):
            end = offset + len(line)
            if any(offset <= start <= end for start in starts):
                last = index
                skip.add(last)
                while last + 1 < len(lines) and not lines[last].rstrip().endswith((".", "!", "?")):
                    last += 1
                    skip.add(last)
            offset = end + 1
        kept += [line for i, line in enumerate(lines) if i not in skip]
    return "\n".join(kept)


def _money(value: Decimal) -> Decimal:
    return value.quantize(_CENT)


def amount_index(text: str) -> set[Decimal]:
    index: set[Decimal] = set()
    for match in _NUMBER.finditer(text):
        if _PERCENT.match(text, match.end()):
            continue
        digits = re.sub(rf"[{_SEPARATORS}]", "", match["int"])
        value = Decimal(f"{digits}.{match['frac'] or '0'}")
        bare = match["int"] == digits and match["frac"] is None
        has_currency = bool(
            _CURRENCY_AFTER.match(text, match.end())
            or _CURRENCY_BEFORE.search(text[max(0, match.start() - 4) : match.start()])
        )
        if bare and value < _BARE_MONEY_MIN and not has_currency:
            continue
        index.add(_money(value))
    return index


def _month_of(word: str) -> int:
    for month, pattern in _MONTH_BY_WORD:
        if pattern.fullmatch(word):
            return month
    raise ValueError(word)


@dataclass
class DateIndex:
    days: set[tuple[int, int, int]]
    months: set[tuple[int, int]]
    years: set[int]

    def add_day(self, year: int, month: int, day: int) -> None:
        try:
            date(year, month, day)
        except ValueError:
            return
        self.days.add((year, month, day))
        self.months.add((year, month))
        self.years.add(year)

    def add_month(self, year: int, month: int) -> None:
        if 1 <= month <= 12:
            self.months.add((year, month))
            self.years.add(year)


def _full_year(raw: str) -> int:
    year = int(raw)
    if len(raw) == 4:
        return year
    return 2000 + year if year < 70 else 1900 + year


def date_index(text: str) -> DateIndex:
    index = DateIndex(set(), set(), set())
    for match in _NUMERIC_DATE.finditer(text):
        day, month, year = match.groups()
        index.add_day(_full_year(year), int(month), int(day))
    for match in _ISO_DATE.finditer(text):
        year, month, day = match.groups()
        index.add_day(int(year), int(month), int(day))
    for match in _DAY_MONTH_YEAR.finditer(text):
        index.add_day(int(match[3]), _month_of(match["month"]), int(match[1]))
    for match in _MONTH_DAY_YEAR.finditer(text):
        index.add_day(int(match[3]), _month_of(match["month"]), int(match[2]))
    for match in _MONTH_YEAR.finditer(text):
        index.add_month(int(match[2]), _month_of(match["month"]))
    for match in _NUMERIC_MONTH.finditer(text):
        index.add_month(int(match[2]), int(match[1]))
    for match in _ISO_MONTH.finditer(text):
        index.add_month(int(match[1]), int(match[2]))
    index.years.update(int(year) for year in _YEAR.findall(text))
    return index


def _date_grounded(value: str, index: DateIndex) -> bool:
    parts = [int(part) for part in value.split("-")]
    if len(parts) == 3:
        return (parts[0], parts[1], parts[2]) in index.days
    if len(parts) == 2:
        return (parts[0], parts[1]) in index.months
    return parts[0] in index.years


def _fold(text: str) -> str:
    return text.casefold().translate(_QUOTES_DASHES)


def _words(text: str) -> str:
    return " ".join(_NON_WORD.sub(" ", _fold(text)).split())


def _organization_core(name: str) -> str:
    return " ".join(_LEGAL_FORM.sub(" ", _words(name)).split())


def _organization_grounded(name: str, haystack: str) -> bool:
    core = _organization_core(name)
    return bool(core) and f" {core} " in haystack


def _person_grounded(name: str, tokens: list[str]) -> bool:
    words = [w for w in _words(name).split() if w not in _TITLES]
    if not words or len(words[-1]) < _SURNAME_MIN:
        return False
    surname = words[-1]
    if len(words) == 1:
        return any(token.startswith(surname) for token in tokens)
    # Polish inflection changes endings, so compare stems: drop up to two trailing letters
    surname_stem = surname[: max(4, len(surname) - 2)]
    first = words[0]
    first_stem = first[: max(3, len(first) - 2)]
    for position, token in enumerate(tokens):
        if not token.startswith(surname_stem):
            continue
        window = tokens[max(0, position - _PERSON_WINDOW) : position + _PERSON_WINDOW + 1]
        if any(other.startswith(first_stem) for other in window if other is not token):
            return True
    return False


def ground_fields(
    pages: list[PageText],
    amounts: list[Amount],
    dates: list[DatedItem],
    document_date: str | None,
    organizations: list[str],
    people: list[str],
) -> GroundedFields:
    corpus = _clean_corpus(pages)
    amounts_seen = amount_index(corpus)
    dates_seen = date_index(corpus)
    haystack = f" {_words(corpus)} "
    tokens = haystack.split()

    kept_amounts = [a for a in amounts if _money(Decimal(str(a.value))) in amounts_seen]
    kept_dates = [d for d in dates if _date_grounded(d.date, dates_seen)]
    kept_orgs = [o for o in organizations if _organization_grounded(o, haystack)]
    kept_people = [p for p in people if _person_grounded(p, tokens)]
    kept_document_date = (
        document_date if document_date and _date_grounded(document_date, dates_seen) else None
    )

    dropped = (
        len(amounts)
        - len(kept_amounts)
        + len(dates)
        - len(kept_dates)
        + len(organizations)
        - len(kept_orgs)
        + len(people)
        - len(kept_people)
        + (1 if document_date and kept_document_date is None else 0)
    )
    return GroundedFields(
        kept_amounts, kept_dates, kept_document_date, kept_orgs, kept_people, dropped
    )
