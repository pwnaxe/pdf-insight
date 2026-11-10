from collections import Counter
from dataclasses import dataclass
from difflib import SequenceMatcher

from app.schemas import Amount, ChunkOutput, DatedItem, DocumentType

MAX_KEYWORDS = 12
MAX_AMOUNTS = 20
MAX_DATES = 20
SIMILAR_CONTEXT = 0.85


@dataclass(frozen=True)
class MergedExtraction:
    language: str
    type: DocumentType
    title: str | None
    date: str | None
    organizations: list[str]
    people: list[str]
    amounts: list[Amount]
    dates: list[DatedItem]
    keywords: list[str]
    summaries: list[str]
    key_points: list[str]
    injection_detected: bool
    injection_quotes: list[str]


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
    dates: dict[tuple[str, str], DatedItem] = {}
    for out in outputs:
        for amount in out.amounts:
            amounts.append(amount)
        for item in out.dates:
            dates.setdefault((item.date, _norm(item.context)), item)

    return MergedExtraction(
        language=_most_common([o.language for o in outputs]),
        type=_most_common([o.type for o in outputs]),
        title=next((o.title for o in outputs if o.title), None),
        date=next((o.date for o in outputs if o.date), None),
        organizations=_dedupe([n for o in outputs for n in o.entities.organizations]),
        people=_dedupe([n for o in outputs for n in o.entities.people]),
        amounts=_merge_amounts(amounts)[:MAX_AMOUNTS],
        dates=list(dates.values())[:MAX_DATES],
        keywords=_dedupe([k for o in outputs for k in o.keywords])[:MAX_KEYWORDS],
        summaries=[o.summary for o in outputs],
        key_points=[p for o in outputs for p in o.key_points],
        injection_detected=any(o.injection_detected for o in outputs),
        injection_quotes=_dedupe([q for o in outputs for q in o.injection_quotes]),
    )
