import base64
import io
import logging

from PyPDF2 import PdfReader
from docx import Document

logger = logging.getLogger(__name__)


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract text from a PDF file."""
    reader = PdfReader(io.BytesIO(file_bytes))
    pages = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            pages.append(text)
    return "\n\n".join(pages)


def extract_images_from_pdf(file_bytes: bytes) -> list[str]:
    """Extract embedded page images from a PDF as data URLs when available."""
    reader = PdfReader(io.BytesIO(file_bytes))
    image_urls: list[str] = []

    for page in reader.pages:
        try:
            images = getattr(page, "images", [])
        except Exception:
            images = []

        for image in images or []:
            data = getattr(image, "data", None)
            name = (getattr(image, "name", "") or "").lower()
            if not data:
                continue

            if name.endswith(".png"):
                mime_type = "image/png"
            elif name.endswith(".webp"):
                mime_type = "image/webp"
            else:
                mime_type = "image/jpeg"

            encoded = base64.b64encode(data).decode("ascii")
            image_urls.append(f"data:{mime_type};base64,{encoded}")

    return image_urls


def extract_text_from_docx(file_bytes: bytes) -> str:
    """Extract text from a DOCX file."""
    doc = Document(io.BytesIO(file_bytes))
    parts: list[str] = []

    parts.extend(p.text.strip() for p in doc.paragraphs if p.text.strip())

    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                cell_lines = [line.strip() for line in cell.text.splitlines() if line.strip()]
                parts.extend(cell_lines)

    return "\n\n".join(parts)


def extract_text(file_bytes: bytes, filename: str) -> str:
    """Extract text from an uploaded file based on extension."""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    logger.info(f"Extracting text from '{filename}' (type={ext})")

    if ext == "pdf":
        return extract_text_from_pdf(file_bytes)
    elif ext in ("docx", "doc"):
        return extract_text_from_docx(file_bytes)
    elif ext == "txt":
        return file_bytes.decode("utf-8", errors="replace")
    else:
        raise ValueError(f"Unsupported file type: .{ext}. Use PDF, DOCX, or TXT.")


def extract_template_source(file_bytes: bytes, filename: str) -> tuple[str, list[str]]:
    """
    Extract text and any embedded page images for template parsing.
    Image extraction is primarily useful for scanned PDFs that contain little
    or no selectable text.
    """
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext != "pdf":
        return extract_text(file_bytes, filename), []
    return extract_text_from_pdf(file_bytes), extract_images_from_pdf(file_bytes)
