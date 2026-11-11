import re
from collections import Counter
from datetime import date

from app.injection import find_injections
from app.pdf import PageText
from app.schemas import Amount, ChunkOutput, DateMention, Entities, FinalOutput, ModelOutput

_MONTHS = {
    "stycznia": 1,
    "lutego": 2,
    "marca": 3,
    "kwietnia": 4,
    "maja": 5,
    "czerwca": 6,
    "lipca": 7,
    "sierpnia": 8,
    "września": 9,
    "października": 10,
    "listopada": 11,
    "grudnia": 12,
}
_CURRENCIES = {"zł": "PLN", "pln": "PLN", "eur": "EUR", "€": "EUR", "usd": "USD", "$": "USD"}

_DOCUMENT = re.compile(r"<document>\n(.*)\n</document>", re.DOTALL)
_PAGE_MARKER = re.compile(r"^\[strona (\d+)\]$", re.MULTILINE)
_AMOUNT = re.compile(
    r"(?<![\d.,])(\d{1,3}(?:[  ]\d{3})+(?:[.,]\d{1,2})?|\d+(?:[.,]\d{1,2})?)\s*"
    r"(zł|PLN|EUR|€|USD|\$)",
    re.IGNORECASE,
)
_NUMERIC_DATE = re.compile(r"\b(\d{1,2})\.(\d{1,2})\.(\d{4})\b")
_OUTPUT_LANG = re.compile(r"^Output language: (pl|en)\b", re.MULTILINE)
_MONTH_NOMINATIVE = {
    "styczeń": 1,
    "luty": 2,
    "marzec": 3,
    "kwiecień": 4,
    "maj": 5,
    "czerwiec": 6,
    "lipiec": 7,
    "sierpień": 8,
    "wrzesień": 9,
    "październik": 10,
    "listopad": 11,
    "grudzień": 12,
}
_ISO_DATE = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b")
_TEXT_DATE = re.compile(rf"\b(\d{{1,2}})\s+({'|'.join(_MONTHS)})\s+(\d{{4}})\b", re.IGNORECASE)
_MONTH_YEAR = re.compile(
    rf"\b({'|'.join([*_MONTHS, *_MONTH_NOMINATIVE])})\s+(\d{{4}})\b", re.IGNORECASE
)
_YEAR_ONLY = re.compile(r"\broku\s+(\d{4})\b", re.IGNORECASE)
_ORGANIZATION = re.compile(r"((?:[A-ZĄĆĘŁŃÓŚŹŻ][\wąćęłńóśźż&-]*[ \t]+){1,4})(sp\. z o\.o\.|S\.A\.)")
_PERSON = re.compile(r"\b([A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż]+ [A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż]+)\s+—\s")
_WORD = re.compile(r"[^\W\d_]{6,}")
_POLISH_HINTS = re.compile(r"\b(i|w|nie|oraz|się|do|na|z|że|jest)\b", re.IGNORECASE)
_ENGLISH_HINTS = re.compile(r"\b(the|and|of|to|is|with|for|that)\b", re.IGNORECASE)
_TYPE_WORDS = [
    ("faktura", "faktura"),
    ("umowa", "umowa"),
    ("oferta", "oferta"),
    ("oferujemy", "oferta"),
    ("raport", "raport"),
    ("invoice", "faktura"),
    ("agreement", "umowa"),
    ("contract", "umowa"),
    ("offer", "oferta"),
    ("report", "raport"),
]
_SUBTYPES = [
    (re.compile(r"\b(?:cv|curriculum vitae|resume|życiorys)\b", re.IGNORECASE), "cv"),
    (re.compile(r"\bregulamin\b", re.IGNORECASE), "regulamin"),
    (re.compile(r"\bprotok[oó][lł]\b", re.IGNORECASE), "protokol"),
]
_SENTENCE_END = re.compile(r"[.!?;]\s+|\n")
_CONTEXT_NOISE = re.compile(
    r"\b\d{1,2}\.\d{1,2}\.\d{4}\b|\b\d+\s*%|\b[A-Z]\d\b|[\d  ]+[.,]\d{2}\s*(?:zł|PLN|EUR|€|USD|\$)"
)
_CONTEXT = 60
_LIMIT = 12
_NO_CONTEXT = "brak kontekstu"


def _pages(user: str) -> list[PageText]:
    match = _DOCUMENT.search(user)
    body = match.group(1) if match else user
    markers = list(_PAGE_MARKER.finditer(body))
    pages = []
    for i, marker in enumerate(markers):
        end = markers[i + 1].start() if i + 1 < len(markers) else len(body)
        pages.append(PageText(int(marker.group(1)), body[marker.end() : end].strip()))
    return pages


def _context(text: str, start: int) -> str:
    begin = max(0, start - _CONTEXT)
    before = text[begin:start]
    ends = list(_SENTENCE_END.finditer(before))
    if ends:
        before = before[ends[-1].end() :]
    elif begin > 0 and text[begin - 1].isalnum():
        before = before.partition(" ")[2]
    before = _CONTEXT_NOISE.sub(" ", before)
    return " ".join(before.split()).strip(" :-—–,(") or _NO_CONTEXT


def _cap(amounts: list[Amount]) -> list[Amount]:
    # keep one amount per currency first so a long PLN list does not hide the rest
    seen: set[tuple[str, str]] = set()
    useful = []
    for amount in amounts:
        key = (amount.currency, amount.context)
        if amount.context != _NO_CONTEXT and key not in seen:
            seen.add(key)
            useful.append(amount)
    chosen = {id(a) for a in {a.currency: a for a in reversed(useful)}.values()}
    for amount in useful:
        if len(chosen) >= _LIMIT:
            break
        chosen.add(id(amount))
    return [a for a in useful if id(a) in chosen]


def _amounts(text: str) -> list[Amount]:
    found: dict[tuple[float, str], Amount] = {}
    for m in _AMOUNT.finditer(text):
        number = re.sub(r"[  ]", "", m.group(1)).replace(",", ".")
        key = (float(number), _CURRENCIES[m.group(2).lower()])
        found.setdefault(
            key, Amount(value=key[0], currency=key[1], context=_context(text, m.start()))
        )
    return _cap(list(found.values()))


def _dates(text: str) -> list[DateMention]:
    found: dict[str, DateMention] = {}

    def add(iso: str, precision: str, start: int) -> None:
        found.setdefault(
            iso, DateMention(date=iso, precision=precision, context=_context(text, start))
        )

    full: list[tuple[int, int, int, int, int]] = []
    for m in _NUMERIC_DATE.finditer(text):
        full.append((m.start(), m.end(), int(m.group(3)), int(m.group(2)), int(m.group(1))))
    for m in _ISO_DATE.finditer(text):
        full.append((m.start(), m.end(), int(m.group(1)), int(m.group(2)), int(m.group(3))))
    for m in _TEXT_DATE.finditer(text):
        month = _MONTHS[m.group(2).lower()]
        full.append((m.start(), m.end(), int(m.group(3)), month, int(m.group(1))))

    candidates: list[tuple[int, str, str]] = []
    for start, _, year, month, day in full:
        try:
            candidates.append((start, date(year, month, day).isoformat(), "day"))
        except ValueError:
            continue
    spans = [(start, end) for start, end, *_ in full]
    for m in _MONTH_YEAR.finditer(text):
        if any(
            start <= m.start() < end or m.start() < end and start < m.end() for start, end in spans
        ):
            continue
        name = m.group(1).lower()
        month = _MONTHS.get(name) or _MONTH_NOMINATIVE[name]
        candidates.append((m.start(), f"{int(m.group(2)):04d}-{month:02d}", "month"))
    for m in _YEAR_ONLY.finditer(text):
        candidates.append((m.start(), m.group(1), "year"))
    for start, iso, precision in sorted(candidates):
        add(iso, precision, start)
    return list(found.values())[:_LIMIT]


def _unique(items: list[str]) -> list[str]:
    seen: dict[str, str] = {}
    for item in items:
        seen.setdefault(" ".join(item.split()).casefold(), " ".join(item.split()))
    return list(seen.values())[:10]


def _language(text: str) -> str:
    polish = len(_POLISH_HINTS.findall(text)) + 3 * len(re.findall(r"[ąćęłńóśźż]", text))
    return "en" if len(_ENGLISH_HINTS.findall(text)) > polish else "pl"


def _type(first_page: str) -> str:
    lowered = first_page.lower()
    hits = [(lowered.find(word), kind) for word, kind in _TYPE_WORDS if word in lowered]
    return min(hits)[1] if hits else "inne"


def _subtype(first_page: str) -> str | None:
    return next((label for pattern, label in _SUBTYPES if pattern.search(first_page)), None)


def _title(text: str) -> str | None:
    for line in text.split("\n"):
        if len(line.strip()) >= 8 and re.search(r"[^\W\d_]{3}", line):
            return line.strip()[:120]
    return None


def _keywords(text: str) -> list[str]:
    words = Counter(w.lower() for w in _WORD.findall(text))
    return [word for word, _ in words.most_common(8)]


_TEXTS = {
    "pl": {
        "type": "Typ dokumentu: {}.",
        "language": "Język dokumentu: {}.",
        "title": "Tytuł: {}",
        "orgs": "Organizacje: {}",
        "amount": "Pierwsza kwota: {:.2f} {}",
        "date": "Pierwsza data: {}",
        "pages": "Liczba stron z tekstem: {}",
        "fragments": "Liczba przeanalizowanych fragmentów: {}",
        "combined": "Dokument obejmuje {} fragmentów przeanalizowanych osobno. {}",
        "no_data": "Brak danych.",
    },
    "en": {
        "type": "Document type: {}.",
        "language": "Document language: {}.",
        "title": "Title: {}",
        "orgs": "Organizations: {}",
        "amount": "First amount: {:.2f} {}",
        "date": "First date: {}",
        "pages": "Pages with text: {}",
        "fragments": "Fragments analysed: {}",
        "combined": "The document spans {} fragments analysed separately. {}",
        "no_data": "No data.",
    },
}


def _summary(
    kind: str, title: str | None, orgs: list[str], amounts: list[Amount], n_dates: int, lang: str
) -> str:
    clean_title = re.sub(r"\.\s", " ", title or "")
    if lang == "en":
        parts = [f"The document is classified as {kind} and titled “{clean_title}”."]
        parts.append(
            f"The organizations named in it are {', '.join(orgs[:3])}, according to its text."
            if orgs
            else "No organizations were identified in the document."
        )
        parts.append(f"The text contains {len(amounts)} amounts and {n_dates} dates.")
        parts.append("This is a demo mode answer, produced by simple rules without an AI model.")
        return " ".join(parts)
    parts = [f"Dokument typu {kind} nosi tytuł „{clean_title}”."]
    parts.append(
        f"Podmioty wymienione w dokumencie to {', '.join(orgs[:3])}, zgodnie z jego treścią."
        if orgs
        else "W dokumencie nie wskazano żadnych organizacji."
    )
    parts.append(f"W treści znaleziono {len(amounts)} kwot oraz {n_dates} dat.")
    parts.append("To odpowiedź trybu demonstracyjnego, przygotowana regułami bez użycia modelu AI.")
    return " ".join(parts)


def _output_lang(system: str) -> str:
    match = _OUTPUT_LANG.search(system)
    return match.group(1) if match else "pl"


def _extract(user: str, out_lang: str) -> dict:
    texts = _TEXTS[out_lang]
    pages = _pages(user)
    text = "\n\n".join(p.text for p in pages)
    first = pages[0].text if pages else ""
    kind, lang, title = _type(first), _language(text), _title(first)
    subtype = _subtype(first) if kind == "inne" else None
    orgs = _unique([f"{m.group(1).strip()} {m.group(2)}" for m in _ORGANIZATION.finditer(text)])
    people = _unique([m.group(1) for m in _PERSON.finditer(text)])
    amounts, dates = _amounts(text), _dates(text)
    hits = find_injections(pages)

    points = [texts["type"].format(kind), texts["language"].format(lang)]
    if title:
        points.append(texts["title"].format(title))
    if orgs:
        points.append(texts["orgs"].format(", ".join(orgs[:3])))
    if amounts:
        points.append(texts["amount"].format(amounts[0].value, amounts[0].currency))
    if dates:
        points.append(texts["date"].format(dates[0].date))
    while len(points) < 3:
        points.append(texts["pages"].format(len(pages)))

    return {
        "language": lang,
        "type": kind,
        "subtype": subtype,
        "title": title,
        "date": next((d.date for d in dates if d.precision == "day"), None),
        "summary": _summary(kind, title, orgs, amounts, len(dates), out_lang),
        "key_points": points,
        "entities": Entities(organizations=orgs, people=people),
        "amounts": amounts,
        "dates": dates,
        "keywords": _keywords(text),
        "injection_detected": bool(hits),
        "injection_quotes": [hit.snippet for hit in hits],
    }


def _final(user: str, out_lang: str) -> FinalOutput:
    texts = _TEXTS[out_lang]
    body = _DOCUMENT.search(user)
    text = body.group(1) if body else user
    fragments = re.findall(r"\[fragment \d+\]\n(.*?)(?=\n\n\[)", text, re.DOTALL)
    points = [
        line[2:]
        for line in text.split("[kluczowe punkty]\n")[-1].split("\n")
        if line.startswith("- ")
    ]
    while len(points) < 3:
        points.append(texts["fragments"].format(len(fragments)))
    first = fragments[0] if fragments else texts["no_data"]
    summary = texts["combined"].format(len(fragments), first)
    return FinalOutput(summary=summary, key_points=points[:7])


class MockProvider:
    name = "mock"

    async def complete_json(
        self, system: str, user: str, schema_name: str, json_schema: dict
    ) -> str:
        out_lang = _output_lang(system)
        if schema_name == "final":
            return _final(user, out_lang).model_dump_json(by_alias=True)
        data = _extract(user, out_lang)
        if schema_name == "summary":
            return FinalOutput(
                summary=data["summary"], key_points=data["key_points"][:7]
            ).model_dump_json(by_alias=True)
        model = ChunkOutput if schema_name == "chunk" else ModelOutput
        if schema_name == "chunk":
            data["key_points"] = data["key_points"][:5]
        return model(**data).model_dump_json(by_alias=True)
