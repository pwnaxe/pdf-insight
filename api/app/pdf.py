import io
import re
from dataclasses import dataclass

import pdfplumber
from pdfminer.pdfparser import PDFSyntaxError
from pypdf import PdfReader
from pypdf.errors import PyPdfError

from app.errors import ApiError
from app.messages import error_message

MIN_TEXT_CHARS = 10

_SPACES = re.compile(r"[^\S\n]+")
_BLANK_LINES = re.compile(r"\n\s*\n\s*(?:\n\s*)*")


class PdfError(ApiError):
    pass


@dataclass(frozen=True)
class PageText:
    number: int
    text: str


@dataclass(frozen=True)
class ExtractedPdf:
    page_count: int
    pages: list[PageText]
    pages_without_text: list[int]
    truncated: bool


def normalize_text(raw: str) -> str:
    lines = (_SPACES.sub(" ", line).strip() for line in raw.replace("\r", "\n").split("\n"))
    return _BLANK_LINES.sub("\n\n", "\n".join(lines)).strip()


def _has_text(text: str) -> bool:
    return len(re.sub(r"\s", "", text)) >= MIN_TEXT_CHARS


def _open(data: bytes) -> PdfReader:
    try:
        reader = PdfReader(io.BytesIO(data))
        if reader.is_encrypted:
            raise PdfError("PDF_ENCRYPTED", error_message("PDF_ENCRYPTED"), 422)
        reader.pages[0:0]
    except PdfError:
        raise
    except (PyPdfError, ValueError, KeyError, TypeError, OSError, RecursionError) as exc:
        raise PdfError("INVALID_PDF", error_message("INVALID_PDF"), 415) from exc
    return reader


def extract_pdf(data: bytes, max_pages: int, max_chars: int) -> ExtractedPdf:
    reader = _open(data)
    page_count = len(reader.pages)
    if page_count > max_pages:
        raise PdfError(
            "TOO_MANY_PAGES",
            error_message("TOO_MANY_PAGES", max_pages=max_pages),
            413,
        )

    pages: list[PageText] = []
    without_text: list[int] = []
    remaining = max_chars
    truncated = False
    try:
        with pdfplumber.open(io.BytesIO(data)) as plumber:
            for number, page in enumerate(plumber.pages, start=1):
                text = normalize_text(page.extract_text() or "")
                page.flush_cache()
                if not _has_text(text):
                    without_text.append(number)
                    continue
                if remaining <= 0:
                    truncated = True
                    continue
                if len(text) > remaining:
                    text = text[:remaining]
                    truncated = True
                remaining -= len(text)
                pages.append(PageText(number, text))
    except (
        PyPdfError,
        PDFSyntaxError,
        ValueError,
        KeyError,
        TypeError,
        OSError,
        RecursionError,
    ) as exc:
        raise PdfError("INVALID_PDF", error_message("INVALID_PDF"), 415) from exc

    if not pages and not truncated:
        raise PdfError("NO_TEXT", error_message("NO_TEXT"), 422)
    return ExtractedPdf(page_count, pages, without_text, truncated)
