import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app

ORIGIN = "https://pwnaxe.github.io"


def make_client(**overrides: object) -> TestClient:
    settings = Settings(llm_provider="mock", **overrides)
    return TestClient(create_app(settings))


def post(
    client: TestClient, data: bytes, name: str = "a.pdf", type_: str = "application/pdf", **kw
):
    return client.post("/api/analyze", files={"file": (name, data, type_)}, **kw)


def error_code(response) -> str:
    return response.json()["error"]["code"]


def test_health() -> None:
    assert make_client().get("/health").json() == {"status": "ok"}


def test_not_pdf() -> None:
    response = post(make_client(), b"hello world", "a.txt", "text/plain")
    assert response.status_code == 415
    assert error_code(response) == "NOT_PDF"


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


def test_blank_pdf(blank_pdf_bytes: bytes) -> None:
    response = post(make_client(), blank_pdf_bytes)
    assert response.status_code == 422
    assert error_code(response) == "NO_TEXT"
    assert "OCR nie jest obsługiwany" in response.json()["error"]["message"]


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


@pytest.mark.parametrize("origin", [None, ORIGIN])
def test_full_flow_with_mock_provider(contract_bytes: bytes, origin: str | None) -> None:
    headers = {"Origin": origin} if origin else {}
    response = post(
        make_client(), contract_bytes, "Test_PDF_Insight_umowa_14-2026.pdf", headers=headers
    )
    assert response.status_code == 200
    body = response.json()
    assert body["document"]["pages"] == 12
    assert body["document"]["fileName"] == "Test_PDF_Insight_umowa_14-2026.pdf"
    assert body["document"]["type"] == "umowa"
    assert body["document"]["language"] == "pl"
    assert body["suspectedInjection"] is True
    assert any("Strony bez warstwy tekstowej (pominięte): 11." in w for w in body["warnings"])
    assert any("polecenia systemowi AI (strona 4)" in w for w in body["warnings"])
    amounts = {(a["value"], a["currency"]) for a in body["amounts"]}
    assert {(184500.0, "PLN"), (226935.0, "PLN"), (2150.0, "EUR"), (890.0, "USD")} <= amounts
    assert len(body["amounts"]) <= 20
    assert len(body["dates"]) <= 20
    assert 3 <= len(body["keyPoints"]) <= 7
