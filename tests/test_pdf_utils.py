
from io import BytesIO

import pytest
from pypdf import PdfWriter

from src.pdf_utils import extract_pdf_text


# Stands in for a Streamlit uploaded file.
class FakeUpload:
    def __init__(self, data: bytes):
        self._data = data

    def getvalue(self) -> bytes:
        return self._data


def _blank_pdf(pages: int, password: str | None = None) -> FakeUpload:
    writer = PdfWriter()
    for _ in range(pages):
        writer.add_blank_page(width=612, height=792)
    if password:
        writer.encrypt(password)
    buffer = BytesIO()
    writer.write(buffer)
    return FakeUpload(buffer.getvalue())


def test_pdf_without_text_is_rejected():
    with pytest.raises(ValueError, match="No readable text"):
        extract_pdf_text(_blank_pdf(1))


def test_pdf_over_page_limit_is_rejected():
    with pytest.raises(ValueError, match="15-page limit"):
        extract_pdf_text(_blank_pdf(16))


def test_password_protected_pdf_is_rejected():
    with pytest.raises(ValueError, match="Password-protected"):
        extract_pdf_text(_blank_pdf(1, password="secret"))


def test_non_pdf_file_is_rejected():
    with pytest.raises(ValueError, match="could not be read"):
        extract_pdf_text(FakeUpload(b"this is not a pdf"))
