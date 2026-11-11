import tomllib
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.llm import LLMError, LLMTimeout
from app.main import create_app

ORIGIN = "https://pwnaxe.github.io"
PYPROJECT = Path(__file__).parents[1] / "pyproject.toml"


class FailingProvider:
    name = "failing"

    def __init__(self, exc: Exception) -> None:
        self.exc = exc

    async def complete_json(self, *args: object, **kwargs: object) -> str:
        raise self.exc


def make_client(**overrides: object) -> TestClient:
    settings = Settings(llm_provider="mock", **overrides)
    return TestClient(create_app(settings))


def post(
    client: TestClient,
    data: bytes,
    name: str = "a.pdf",
    type_: str = "application/pdf",
    form: dict[str, str] | None = None,
    **kw,
):
    return client.post("/api/analyze", files={"file": (name, data, type_)}, data=form, **kw)


def error_code(response) -> str:
    return response.json()["error"]["code"]


def test_health() -> None:
    assert make_client().get("/health").json() == {"status": "ok"}


def test_not_pdf() -> None:
    response = post(make_client(), b"hello world", "a.txt", "text/plain")
    assert response.status_code == 415
    assert error_code(response) == "UNSUPPORTED_MEDIA_TYPE"


def test_wrong_magic_with_pdf_name() -> None:
    assert post(make_client(), b"hello world").status_code == 415


def test_missing_file_is_validation_error() -> None:
    response = make_client().post("/api/analyze")
    assert response.status_code == 422
    assert error_code(response) == "VALIDATION_ERROR"


def test_too_big(contract_bytes: bytes) -> None:
    client = make_client(max_file_mb=0)
    response = post(client, contract_bytes)
    assert response.status_code == 413
    assert error_code(response) == "FILE_TOO_LARGE"


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        ({}, "OCR nie jest obsługiwany"),
        ({"lang": "pl"}, "OCR nie jest obsługiwany"),
        ({"lang": "en"}, "OCR is not supported"),
        ({"lang": "de"}, "OCR nie jest obsługiwany"),
    ],
)
def test_blank_pdf(blank_pdf_bytes: bytes, data: dict[str, str], expected: str) -> None:
    response = post(make_client(), blank_pdf_bytes, form=data)
    assert response.status_code == 422
    assert error_code(response) == "NO_TEXT"
    assert expected in response.json()["error"]["message"]


@pytest.mark.parametrize(
    ("lang", "expected"),
    [("pl", "Plik jest za duży. Maksymalny rozmiar to 0 MB."), ("en", "maximum size is 0 MB")],
)
def test_error_messages_follow_lang(contract_bytes: bytes, lang: str, expected: str) -> None:
    response = post(make_client(max_file_mb=0), contract_bytes, form={"lang": lang})
    assert expected in response.json()["error"]["message"]


def test_page_limit_message_in_both_languages(contract_bytes: bytes) -> None:
    client = make_client(max_pages=5)
    pl = post(client, contract_bytes).json()["error"]["message"]
    en = post(client, contract_bytes, form={"lang": "en"}).json()["error"]["message"]
    assert pl == "Dokument ma zbyt wiele stron (limit: 5)."
    assert en == "The document has too many pages (limit: 5)."


def test_rate_limit_message_follows_lang() -> None:
    client = make_client(rate_limit_per_10min=1)
    post(client, b"x", "a.txt", "text/plain")
    response = post(client, b"x", "a.txt", "text/plain", form={"lang": "en"})
    assert response.json()["error"]["message"] == "Too many requests. Try again in a few minutes."


def test_encrypted_pdf(encrypted_pdf_bytes: bytes) -> None:
    assert error_code(post(make_client(), encrypted_pdf_bytes)) == "PDF_ENCRYPTED"


def test_too_many_pages(contract_bytes: bytes) -> None:
    response = post(make_client(max_pages=5), contract_bytes)
    assert response.status_code == 413
    assert error_code(response) == "TOO_MANY_PAGES"


def test_foreign_origin_is_rejected(contract_bytes: bytes) -> None:
    response = post(make_client(), contract_bytes, headers={"Origin": "https://evil.example"})
    assert response.status_code == 403
    assert error_code(response) == "FORBIDDEN_ORIGIN"


def test_cors_preflight_for_allowed_origin() -> None:
    response = make_client().options(
        "/api/analyze",
        headers={"Origin": ORIGIN, "Access-Control-Request-Method": "POST"},
    )
    assert response.headers["access-control-allow-origin"] == ORIGIN


def test_dev_origin_only_in_dev() -> None:
    assert "http://localhost:5173" not in Settings().origins
    assert "http://localhost:5173" in Settings(env="dev").origins


def test_rate_limit(contract_bytes: bytes) -> None:
    client = make_client(rate_limit_per_10min=2)
    assert post(client, b"x", "a.txt", "text/plain").status_code == 415
    assert post(client, b"x", "a.txt", "text/plain").status_code == 415
    response = post(client, b"x", "a.txt", "text/plain")
    assert response.status_code == 429
    assert error_code(response) == "RATE_LIMITED"
    assert int(response.headers["retry-after"]) > 0


def test_rate_limit_uses_forwarded_ip_when_trusted() -> None:
    client = make_client(rate_limit_per_10min=1, trust_proxy=True)
    first = post(client, b"x", "a.txt", "text/plain", headers={"X-Forwarded-For": "1.1.1.1"})
    other = post(client, b"x", "a.txt", "text/plain", headers={"X-Forwarded-For": "2.2.2.2"})
    again = post(client, b"x", "a.txt", "text/plain", headers={"X-Forwarded-For": "1.1.1.1"})
    assert (first.status_code, other.status_code, again.status_code) == (415, 415, 429)


WARNINGS = {
    "pl": ("Strony bez warstwy tekstowej (pominięte): 11.", "polecenia systemowi AI (strona 4)"),
    "en": (
        "Pages without a text layer (skipped): 11.",
        "give instructions to an AI system (page 4)",
    ),
}


@pytest.mark.parametrize("origin", [None, ORIGIN])
@pytest.mark.parametrize("lang", [None, "pl", "en"])
def test_full_flow_with_mock_provider(
    contract_bytes: bytes, origin: str | None, lang: str | None
) -> None:
    headers = {"Origin": origin} if origin else {}
    response = post(
        make_client(),
        contract_bytes,
        "Test_PDF_Insight_umowa_14-2026.pdf",
        headers=headers,
        form={"lang": lang} if lang else {},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["document"]["pages"] == 12
    assert body["document"]["fileName"] == "Test_PDF_Insight_umowa_14-2026.pdf"
    assert body["document"]["type"] == "umowa"
    assert body["document"]["language"] == "pl"
    assert body["suspectedInjection"] is True
    no_text, injection = WARNINGS[lang or "pl"]
    assert any(no_text in w for w in body["warnings"])
    assert any(injection in w for w in body["warnings"])
    amounts = {(a["value"], a["currency"]) for a in body["amounts"]}
    assert {(184500.0, "PLN"), (226935.0, "PLN"), (2150.0, "EUR"), (890.0, "USD")} <= amounts
    assert len(body["amounts"]) <= 20
    assert len(body["dates"]) <= 20
    assert 3 <= len(body["keyPoints"]) <= 7


def test_root() -> None:
    body = make_client().get("/").json()
    assert body["name"] == "pdf-insight-api"
    assert (
        body["version"]
        == tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))["project"]["version"]
    )
    assert body["endpoints"] == ["GET /health", "POST /api/analyze"]
    assert body["repo"] == "https://github.com/pwnaxe/pdf-insight"


def test_unknown_path_is_not_found() -> None:
    response = make_client().get("/nope")
    assert response.status_code == 404
    assert response.json() == {"error": {"code": "NOT_FOUND", "message": "Not found."}}


def test_wrong_method_has_allow_header() -> None:
    response = make_client().get("/api/analyze")
    assert response.status_code == 405
    assert error_code(response) == "METHOD_NOT_ALLOWED"
    assert "POST" in response.headers["allow"]


@pytest.mark.parametrize("path", ["/docs", "/redoc", "/openapi.json"])
def test_docs_disabled_in_prod(path: str) -> None:
    response = make_client(env="prod").get(path)
    assert response.status_code == 404
    assert error_code(response) == "NOT_FOUND"


@pytest.mark.parametrize("path", ["/docs", "/redoc", "/openapi.json"])
def test_docs_enabled_in_dev(path: str) -> None:
    assert make_client(env="dev").get(path).status_code == 200


def test_rate_limited_has_retry_after(contract_bytes: bytes) -> None:
    client = make_client(rate_limit_per_10min=1)
    assert post(client, contract_bytes).status_code == 200
    response = post(client, contract_bytes)
    assert response.status_code == 429
    assert error_code(response) == "RATE_LIMITED"
    assert int(response.headers["retry-after"]) > 0


def test_corrupt_pdf_is_invalid() -> None:
    response = post(make_client(), b"%PDF-1.4 garbage")
    assert response.status_code == 415
    assert error_code(response) == "INVALID_PDF"


def test_ai_failures_map_to_upstream_codes(contract_bytes: bytes) -> None:
    for exc, status, code in [(LLMTimeout(), 504, "AI_TIMEOUT"), (LLMError(), 502, "AI_ERROR")]:
        client = TestClient(create_app(Settings(llm_provider="mock"), FailingProvider(exc)))
        response = post(client, contract_bytes)
        assert (response.status_code, error_code(response)) == (status, code)


def test_internal_error_hides_details(contract_bytes: bytes) -> None:
    client = TestClient(
        create_app(Settings(llm_provider="mock"), FailingProvider(ValueError("secret detail"))),
        raise_server_exceptions=False,
    )
    response = post(client, contract_bytes)
    assert response.status_code == 500
    assert error_code(response) == "INTERNAL_ERROR"
    assert "secret detail" not in response.text
    assert "Traceback" not in response.text
