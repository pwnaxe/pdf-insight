from typing import Literal

Lang = Literal["pl", "en"]

DEFAULT_LANG: Lang = "pl"

_ERRORS: dict[Lang, dict[str, str]] = {
    "pl": {
        "FORBIDDEN_ORIGIN": "Pochodzenie żądania jest niedozwolone.",
        "RATE_LIMITED": "Zbyt wiele żądań. Spróbuj ponownie za kilka minut.",
        "FILE_TOO_LARGE": "Plik jest za duży. Maksymalny rozmiar to {max_mb} MB.",
        "UNSUPPORTED_MEDIA_TYPE": "To nie jest plik PDF.",
        "PDF_ENCRYPTED": "Ten plik PDF jest zaszyfrowany i nie można go odczytać.",
        "INVALID_PDF": "Nie udało się odczytać pliku PDF. Plik jest uszkodzony.",
        "TOO_MANY_PAGES": "Dokument ma zbyt wiele stron (limit: {max_pages}).",
        "NO_TEXT": (
            "Ten PDF nie ma warstwy tekstowej (prawdopodobnie to skan). OCR nie jest obsługiwany."
        ),
        "AI_TIMEOUT": "Model AI nie odpowiedział na czas. Spróbuj ponownie.",
        "AI_ERROR": "Usługa AI jest chwilowo niedostępna. Spróbuj ponownie później.",
        "AI_INVALID_OUTPUT": "Model AI zwrócił nieprawidłową odpowiedź.",
        "VALIDATION_ERROR": "Nieprawidłowe żądanie. Wyślij plik PDF w polu 'file'.",
        "NOT_FOUND": "Nie znaleziono.",
        "METHOD_NOT_ALLOWED": "Ta metoda HTTP nie jest dozwolona dla tego adresu.",
        "INTERNAL_ERROR": "Wystąpił nieoczekiwany błąd serwera.",
    },
    "en": {
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
    },
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
        "page_one": "page",
        "page_many": "pages",
    },
}


def parse_lang(value: object) -> Lang:
    return "en" if value == "en" else DEFAULT_LANG


def error_message(code: str, lang: Lang, **params: object) -> str:
    return _ERRORS[lang][code].format(**params)


def warning_message(key: str, lang: Lang, **params: object) -> str:
    return _WARNINGS[lang][key].format(**params)
