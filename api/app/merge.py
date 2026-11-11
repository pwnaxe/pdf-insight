import re
from collections import Counter
from dataclasses import dataclass
from difflib import SequenceMatcher

from app.schemas import Amount, ChunkOutput, DateMention, DocumentType, date_precision

MAX_KEYWORDS = 12
MAX_AMOUNTS = 20
MAX_DATES = 20
SIMILAR_CONTEXT = 0.85


@dataclass(frozen=True)
class MergedExtraction:
    language: str
    type: DocumentType
    subtype: str | None
    title: str | None
    date: str | None
    organizations: list[str]
    people: list[str]
    amounts: list[Amount]
    dates: list[DateMention]
    keywords: list[str]
    summaries: list[str]
    key_points: list[str]
    injection_detected: bool


def _norm(text: str) -> str:
    return " ".join(text.split()).casefold()


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        key = _norm(item)
        if key and key not in seen:
            seen.add(key)
            result.append(" ".join(item.split()))
    return result


_LEGAL_SUFFIX = re.compile(r"\s(sp z o o|sp j|sp k|s a|sa|gmbh|ltd|inc)$")


def _org_key(name: str) -> str:
    plain = " ".join(re.sub(r"[.,]", " ", name.casefold()).split())
    stripped = _LEGAL_SUFFIX.sub("", plain)
    return stripped or plain


def _dedupe_organizations(items: list[str]) -> list[str]:
    # same entity with and without a legal form: keep the longer name at the first position
    names: dict[str, str] = {}
    for item in items:
        key = _org_key(item)
        if not key:
            continue
        clean = " ".join(item.split())
        if key not in names or len(clean) > len(names[key]):
            names[key] = clean
    return list(names.values())


def _most_common[T](values: list[T]) -> T:
    return Counter(values).most_common(1)[0][0]


def _merge_amounts(items: list[Amount]) -> list[Amount]:
    kept: list[Amount] = []
    for amount in items:
        context = _norm(amount.context)
        duplicate = any(
            k.value == amount.value
            and k.currency == amount.currency
            and SequenceMatcher(None, _norm(k.context), context).ratio() >= SIMILAR_CONTEXT
            for k in kept
        )
        if not duplicate:
            kept.append(amount)
    return kept


def merge_chunk_outputs(outputs: list[ChunkOutput]) -> MergedExtraction:
    if not outputs:
        raise ValueError("nothing to merge")

    amounts: list[Amount] = []
    dates: dict[tuple[str, str], DateMention] = {}
    for out in outputs:
        amounts.extend(out.amounts)
        for item in out.dates:
            dates.setdefault((item.date, _norm(item.context)), item)

    kind = _most_common([o.type for o in outputs])
    return MergedExtraction(
        language=_most_common([o.language for o in outputs]),
        type=kind,
        subtype=next((o.subtype for o in outputs if o.subtype and o.type == kind), None),
        title=next((o.title for o in outputs if o.title), None),
        date=next((o.date for o in outputs if o.date and date_precision(o.date) == "day"), None),
        organizations=_dedupe_organizations([n for o in outputs for n in o.entities.organizations]),
        people=_dedupe([n for o in outputs for n in o.entities.people]),
        amounts=_merge_amounts(amounts)[:MAX_AMOUNTS],
        dates=list(dates.values())[:MAX_DATES],
        keywords=_dedupe([k for o in outputs for k in o.keywords])[:MAX_KEYWORDS],
        summaries=[o.summary for o in outputs],
        key_points=[p for o in outputs for p in o.key_points],
        injection_detected=any(o.injection_detected for o in outputs),
    )
