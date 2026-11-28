
from io import BytesIO

from pypdf import PdfReader
from pypdf.errors import PyPdfError


# Extract readable text from an uploaded PDF file.
def extract_pdf_text(uploaded_file) -> str:
    try:
        pdf = PdfReader(BytesIO(uploaded_file.getvalue()))
    except PyPdfError as error:
        raise ValueError("This file could not be read as a PDF.") from error

    # Reject password-protected PDFs.
    if pdf.is_encrypted:
        raise ValueError("Password-protected PDFs are not supported.")

    # Limit PDF uploads to 15 pages.
    if len(pdf.pages) > 15:
        raise ValueError("PDF exceeds the 15-page limit.")

    # Extract text from each page of the PDF.
    text = "\n".join(
        page.extract_text() or "" for page in pdf.pages
    )

    # Reject scanned PDFs without extractable text.
    if not text.strip():
        raise ValueError(
            "No readable text found. Scanned PDFs are not supported."
        )

    return text.strip()
