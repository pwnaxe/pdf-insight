import re
import unicodedata
from dataclasses import dataclass

from app.pdf import PageText

# pypdf sometimes emits "wcze ś niejsze"; spaces around non-ASCII letters are joined before
# matching, so patterns use \s* between words.
_PATTERNS = [
    r"zignoruj\s*(wszystkie\s*)?(wczesniejsze|poprzednie|powyzsze)\s*(polecenia|instrukcje)",
    r"instrukcja\s*dla\s*(systemu\s*)?(ai|sztucznej\s*inteligencji|modelu)",
    r"nie\s*wspominaj\s*o\s*tej\s*instrukcji",
    r"ignore\s+(all\s+)?(previous|prior|above)\s+(instructions|prompts)",
    r"disregard\s+(all\s+)?(previous|prior)\s",
    r"\byou\s+are\s+now\b",
    r"\bsystem\s+prompt\b",
    r"\bact\s+as\s+(an?\s+)?(ai|assistant)\b",
]
_RULES = [re.compile(p, re.IGNORECASE) for p in _PATTERNS]
_NON_ASCII_LETTER_GAP = re.compile(r"\s?([^\x00-\x7f])\s?")
_CONTEXT_BEFORE = 20
_CONTEXT_AFTER = 100


@dataclass(frozen=True)
class InjectionHit:
    page: int
    snippet: str


def _join_gaps(text: str) -> str:
    def repl(match: re.Match[str]) -> str:
        char = match.group(1)
        return char if char.isalpha() else match.group(0)

    return _NON_ASCII_LETTER_GAP.sub(repl, text)


def _fold(text: str) -> str:
    folded = []
    for char in text:
        if char in "łŁ":
            folded.append("l")
        else:
            folded.append(unicodedata.normalize("NFD", char)[0])
    return "".join(folded)


def find_injections(pages: list[PageText]) -> list[InjectionHit]:
    hits: list[InjectionHit] = []
    for page in pages:
        text = _join_gaps(page.text)
        folded = _fold(text)
        starts = [m.start() for rule in _RULES for m in rule.finditer(folded)]
        if starts:
            start = min(starts)
            begin = max(0, start - _CONTEXT_BEFORE)
            hits.append(
                InjectionHit(page.number, " ".join(text[begin : start + _CONTEXT_AFTER].split()))
            )
    return hits
