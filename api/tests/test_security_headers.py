import logging

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app

ORIGIN = "https://pwnaxe.github.io"
LEAK_MARKER = "internal-detail-9f3a"

EXPECTED = {
    "x-content-type-options": "nosniff",
    "referrer-policy": "no-referrer",
    "strict-transport-security": "max-age=31536000; includeSubDomains",
    "content-security-policy": "default-src 'none'; frame-ancestors 'none'",
    "x-frame-options": "DENY",
}


class ExplodingProvider:
    name = "exploding"

    async def complete_json(self, system, user, schema_name, json_schema) -> str:
        raise RuntimeError(LEAK_MARKER)


def make_client(**overrides: object) -> TestClient:
    return TestClient(create_app(Settings(llm_provider="mock", **overrides)))


def assert_headers(response, cache: bool) -> None:
    for name, value in EXPECTED.items():
        assert response.headers.get(name) == value, name
    assert (response.headers.get("cache-control") == "no-store") is cache


def test_health_has_headers_without_cache_control() -> None:
    response = make_client().get("/health")
    assert_headers(response, cache=False)


def test_not_found_has_headers() -> None:
    assert_headers(make_client().get("/nope"), cache=False)
    assert_headers(make_client().get("/api/nope"), cache=True)


def test_api_error_has_headers() -> None:
    response = make_client().post("/api/analyze")
    assert response.status_code == 422
    assert_headers(response, cache=True)


def test_rate_limited_has_headers(contract_bytes: bytes) -> None:
    client = make_client(rate_limit_per_10min=1)
    files = {"file": ("a.pdf", contract_bytes, "application/pdf")}
    client.post("/api/analyze", files=files)
    response = client.post("/api/analyze", files=files)
    assert response.status_code == 429
    assert_headers(response, cache=True)


def test_forbidden_origin_has_headers(contract_bytes: bytes) -> None:
    response = make_client().post(
        "/api/analyze",
        files={"file": ("a.pdf", contract_bytes, "application/pdf")},
        headers={"Origin": "https://evil.example"},
    )
    assert response.status_code == 403
    assert_headers(response, cache=True)


def test_preflight_has_headers_and_narrow_cors() -> None:
    response = make_client().options(
        "/api/analyze",
        headers={
            "Origin": ORIGIN,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == ORIGIN
    assert response.headers["access-control-allow-methods"] == "POST, GET"
    assert "*" not in response.headers.get("access-control-allow-headers", "")
    assert_headers(response, cache=True)


def test_preflight_rejects_unlisted_header() -> None:
    response = make_client().options(
        "/api/analyze",
        headers={
            "Origin": ORIGIN,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "x-custom",
        },
    )
    assert response.status_code == 400


def test_unexpected_error_is_generic_and_has_headers(
    contract_bytes: bytes, caplog: pytest.LogCaptureFixture
) -> None:
    app = create_app(Settings(llm_provider="mock"), provider=ExplodingProvider())
    client = TestClient(app, raise_server_exceptions=False)
    with caplog.at_level(logging.DEBUG):
        response = client.post(
            "/api/analyze", files={"file": ("a.pdf", contract_bytes, "application/pdf")}
        )
    assert response.status_code == 500
    body = response.json()
    assert body["error"]["code"] == "INTERNAL_ERROR"
    assert set(body) == {"error"}
    assert LEAK_MARKER not in response.text
    assert "Traceback" not in response.text
    assert "RuntimeError" not in response.text
    assert LEAK_MARKER not in caplog.text
    assert_headers(response, cache=True)
