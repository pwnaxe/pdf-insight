import pytest

from app.pdf import PdfError, extract_pdf, normalize_text


def test_normalize_text() -> None:
    assert normalize_text("a   b\t c \r\n\n\n\n d  \n") == "a b c\n\nd"


def test_contract_pages(contract_bytes: bytes) -> None:
    result = extract_pdf(contract_bytes, max_pages=100, max_chars=400_000)
    assert result.page_count == 12
    assert result.pages_without_text == [11]
    assert [p.number for p in result.pages] == [n for n in range(1, 13) if n != 11]
    assert "184 500,00" in result.pages[3].text
    assert not result.truncated


def test_truncation(contract_bytes: bytes) -> None:
    result = extract_pdf(contract_bytes, max_pages=100, max_chars=3000)
    assert result.truncated
    assert sum(len(p.text) for p in result.pages) == 3000
    assert [p.number for p in result.pages] == [1, 2]


def test_too_many_pages(contract_bytes: bytes) -> None:
    with pytest.raises(PdfError) as info:
        extract_pdf(contract_bytes, max_pages=5, max_chars=400_000)
    assert info.value.code == "TOO_MANY_PAGES"
    assert info.value.status == 413


def test_blank_pdf_has_no_text(blank_pdf_bytes: bytes) -> None:
    with pytest.raises(PdfError) as info:
        extract_pdf(blank_pdf_bytes, max_pages=100, max_chars=400_000)
    assert info.value.code == "NO_TEXT"
    assert info.value.status == 422


def test_encrypted(encrypted_pdf_bytes: bytes) -> None:
    with pytest.raises(PdfError) as info:
        extract_pdf(encrypted_pdf_bytes, max_pages=100, max_chars=400_000)
    assert info.value.code == "PDF_ENCRYPTED"


@pytest.mark.parametrize("data", [b"", b"%PDF-1.7\nnot really a pdf", b"%PDF-" + b"\x00" * 50])
def test_invalid(data: bytes) -> None:
    with pytest.raises(PdfError) as info:
        extract_pdf(data, max_pages=100, max_chars=400_000)
    assert info.value.code == "PDF_INVALID"
