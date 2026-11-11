import re
import unicodedata
from dataclasses import dataclass

from app.pdf import PageText

_PATTERNS = [
    r"zignoruj\s+(wszystkie\s+)?(wczesniejsze|poprzednie|powyzsze)\s+(polecenia|instrukcje)",
    r"instrukcja\s+dla\s+(systemu\s+)?(ai|sztucznej\s+inteligencji|modelu)",
    r"nie\s+wspominaj\s+o\s+tej\s+instrukcji",
    r"ignore\s+(all\s+)?(previous|prior|above)\s+(instructions|prompts)",
    r"disregard\s+(all\s+)?(previous|prior)\s",
    r"\byou\s+are\s+now\b",
    r"\bsystem\s+prompt\b",
    r"\bact\s+as\s+(an?\s+)?(ai|assistant)\b",
]
_RULES = [re.compile(p, re.IGNORECASE) for p in _PATTERNS]
_SNIPPET_MAX = 200
_SENTENCE_END = re.compile(r"[.!?](?:\s|$)|\n")


@dataclass(frozen=True)
class InjectionHit:
    page: int
    snippet: str


def _fold(text: str) -> str:
    folded = []
    for char in text:
        if char in "łŁ":
            folded.append("l")
        else:
            folded.append(unicodedata.normalize("NFD", char)[0])
    return "".join(folded)


def _snippet(text: str, start: int) -> str:
    end = _SENTENCE_END.search(text, start)
    stop = end.end() if end else len(text)
    return " ".join(text[start : min(stop, start + _SNIPPET_MAX)].split())


def injection_starts(text: str) -> list[int]:
    # _fold keeps one character per character, so offsets match the original text
    folded = _fold(text)
    return [m.start() for rule in _RULES for m in rule.finditer(folded)]


def find_injections(pages: list[PageText]) -> list[InjectionHit]:
    hits: list[InjectionHit] = []
    for page in pages:
        starts = injection_starts(page.text)
        if starts:
            hits.append(InjectionHit(page.number, _snippet(page.text, min(starts))))
    return hits
