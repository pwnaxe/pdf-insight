import io
from pathlib import Path

import pytest
from pypdf import PdfWriter

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


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"
