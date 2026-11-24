
from io import BytesIO

from pypdf import PdfReader


# Extract readable text from an uploaded PDF file.
def extract_pdf_text(uploaded_file) -> str:
    pdf = PdfReader(BytesIO(uploaded_file.getvalue()))

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

