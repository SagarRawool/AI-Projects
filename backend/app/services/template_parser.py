import io
from typing import Optional
from fastapi import HTTPException, UploadFile
import pypdf


def extract_text_from_pdf_bytes(pdf_bytes: bytes) -> str:
    """Extracts all readable text from PDF bytes."""
    try:
        reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
        pages_text = []
        for idx, page in enumerate(reader.pages):
            text = page.extract_text()
            if text:
                pages_text.append(text.strip())
        return "\n\n".join(pages_text).strip()
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to parse PDF template: {str(e)}"
        )


async def parse_template_upload(file: UploadFile) -> str:
    """Parses uploaded template file (PDF, TXT, or MD) and returns extracted plain text."""
    filename = (file.filename or "").lower()
    content_bytes = await file.read()

    if not content_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    if filename.endswith(".pdf"):
        extracted = extract_text_from_pdf_bytes(content_bytes)
    elif filename.endswith(".txt") or filename.endswith(".md"):
        try:
            extracted = content_bytes.decode("utf-8").strip()
        except UnicodeDecodeError:
            try:
                extracted = content_bytes.decode("latin-1").strip()
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Failed to decode text file: {e}")
    else:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file format. Please upload a .pdf, .txt, or .md file."
        )

    if not extracted:
        raise HTTPException(
            status_code=400,
            detail="Could not extract any readable text from the uploaded template file."
        )

    return extracted

