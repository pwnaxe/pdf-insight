import io
from pathlib import Path

import pytest
from pypdf import PdfWriter

from app.config import Settings

FIXTURES = Path(__file__).parent / "fixtures"


def _write(writer: PdfWriter) -> bytes:
    buffer = io.BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


@pytest.fixture(scope="session")
def contract_bytes() -> bytes:
    return (FIXTURES / "Test_PDF_Insight_umowa_14-2026.pdf").read_bytes()


@pytest.fixture(scope="session")
def blank_pdf_bytes() -> bytes:
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    return _write(writer)


@pytest.fixture(scope="session")
def encrypted_pdf_bytes() -> bytes:
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    writer.encrypt("secret")
    return _write(writer)


@pytest.fixture(autouse=True)
def isolated_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in Settings.model_fields:
        monkeypatch.delenv(name.upper(), raising=False)
    monkeypatch.setitem(Settings.model_config, "env_file", None)


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"
