import re

from app.messages import Lang
from app.schemas import SUBTYPE_MAX, Amount, DatedItem, DateMention, date_precision

CONTEXT_MAX = 80

_META = re.compile(
    r"pomini[ęe]t\w*|skipped|not a date|nie jest dat\w*|brak daty|uncertain|niepewn\w*",
    re.IGNORECASE,
)
# a remark that the value is no date means the item itself is wrong, even inside brackets
_NOT_A_DATE = re.compile(r"not a date|nie jest dat\w*|brak daty", re.IGNORECASE)
_BRACKETED = re.compile(r"[(\[][^()\[\]]*[)\]]")
_EDGE_PUNCTUATION = " \t\n,;:-–—.(["
_GENERIC_AMOUNT: dict[Lang, str] = {"pl": "kwota", "en": "amount"}


def clean_context(text: str) -> str | None:
    def drop_meta(match: re.Match[str]) -> str:
        return " " if _META.search(match.group()) else match.group()

    text = _BRACKETED.sub(drop_meta, text)
    if _META.search(text):
        return None
    text = " ".join(text.split()).strip(_EDGE_PUNCTUATION)
    if len(text) > CONTEXT_MAX:
        cut = text[:CONTEXT_MAX]
        # cut at a word boundary unless the text starts with one very long word
        if text[CONTEXT_MAX] != " " and " " in cut:
            cut = cut.rsplit(" ", 1)[0]
        text = cut.strip(_EDGE_PUNCTUATION)
    return text or None


def normalise_dates(mentions: list[DateMention]) -> list[DatedItem]:
    items: list[DatedItem] = []
    seen: set[tuple[str, str]] = set()
    for mention in mentions:
        value = mention.date.strip()
        precision = date_precision(value)
        context = None if _NOT_A_DATE.search(mention.context) else clean_context(mention.context)
        if precision is None or context is None or (value, context.casefold()) in seen:
            continue
        seen.add((value, context.casefold()))
        items.append(DatedItem(date=value, precision=precision, context=context))
    return items


def normalise_document_date(value: str | None) -> str | None:
    value = (value or "").strip()
    return value if date_precision(value) == "day" else None


def normalise_amounts(amounts: list[Amount], lang: Lang) -> list[Amount]:
    return [
        amount.model_copy(
            update={"context": clean_context(amount.context) or _GENERIC_AMOUNT[lang]}
        )
        for amount in amounts
    ]


def normalise_subtype(value: str | None) -> str | None:
    value = " ".join((value or "").split()).lower()
    return value if value and len(value) <= SUBTYPE_MAX else None
