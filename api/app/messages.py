from typing import Literal

Lang = Literal["pl", "en"]

_ERRORS = {
    "FORBIDDEN_ORIGIN": "Request origin not allowed.",
    "RATE_LIMITED": "Too many requests. Try again in a few minutes.",
    "FILE_TOO_LARGE": "The file is too large. The maximum size is {max_mb} MB.",
    "UNSUPPORTED_MEDIA_TYPE": "This is not a PDF file.",
    "PDF_ENCRYPTED": "This PDF is encrypted and cannot be read.",
    "INVALID_PDF": "Could not read the PDF file. The file is damaged.",
    "TOO_MANY_PAGES": "The document has too many pages (limit: {max_pages}).",
    "NO_TEXT": "This PDF has no text layer (probably a scan). OCR is not supported.",
    "AI_TIMEOUT": "The AI model did not respond in time. Try again.",
    "AI_ERROR": "The AI service is temporarily unavailable. Try again later.",
    "AI_INVALID_OUTPUT": "The AI model returned an invalid response.",
    "VALIDATION_ERROR": "Invalid request. Send a PDF file in the 'file' field.",
    "NOT_FOUND": "Not found.",
    "METHOD_NOT_ALLOWED": "This HTTP method is not allowed for this path.",
    "INTERNAL_ERROR": "An unexpected server error occurred.",
}

_WARNINGS: dict[Lang, dict[str, str]] = {
    "pl": {
        "injection_pages": (
            "Dokument zawiera tekst, który próbuje wydawać polecenia systemowi AI "
            "({label} {pages}). Został zignorowany podczas analizy."
        ),
        "injection": (
            "Dokument zawiera tekst, który próbuje wydawać polecenia systemowi AI. "
            "Został zignorowany podczas analizy."
        ),
        "no_text_pages": "Strony bez warstwy tekstowej (pominięte): {pages}.",
        "truncated": "Dokument jest bardzo długi, więc przeanalizowano tylko jego początek.",
        "dropped": "Pominięto {count} pozycji, których nie znaleziono w tekście dokumentu.",
        "page_one": "strona",
        "page_many": "strony",
    },
    "en": {
        "injection_pages": (
            "The document contains text that tries to give instructions to an AI system "
            "({label} {pages}). It was ignored during analysis."
        ),
        "injection": (
            "The document contains text that tries to give instructions to an AI system. "
            "It was ignored during analysis."
        ),
        "no_text_pages": "Pages without a text layer (skipped): {pages}.",
        "truncated": "The document is very long, so only its initial part was analysed.",
        "dropped": "Dropped {count} items not found in the document text.",
        "page_one": "page",
        "page_many": "pages",
    },
}


_GENERIC_AMOUNT: dict[Lang, str] = {"pl": "kwota", "en": "amount"}


def message_lang(document_language: str) -> Lang:
    return "pl" if document_language == "pl" else "en"


def generic_amount(lang: Lang) -> str:
    return _GENERIC_AMOUNT[lang]


def error_message(code: str, **params: object) -> str:
    return _ERRORS[code].format(**params)


def warning_message(key: str, lang: Lang, **params: object) -> str:
    return _WARNINGS[lang][key].format(**params)
