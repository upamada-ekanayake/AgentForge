from pathlib import Path

from docx import Document as DocxDocument
from pypdf import PdfReader


class DocumentParsingError(ValueError):
    """Raised when text cannot be extracted from an uploaded document."""


def extract_text(file_path: Path) -> str:
    extension = file_path.suffix.lower()

    if extension == ".pdf":
        text = _extract_pdf_text(file_path)
    elif extension == ".docx":
        text = _extract_docx_text(file_path)
    elif extension == ".txt":
        text = _extract_txt_text(file_path)
    else:
        raise DocumentParsingError("Unsupported document type.")

    normalized_text = _normalize_text(text)
    if not normalized_text:
        raise DocumentParsingError("No readable text was found in the document.")

    return normalized_text


def _extract_pdf_text(file_path: Path) -> str:
    try:
        reader = PdfReader(str(file_path))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception as exc:
        raise DocumentParsingError("Could not extract text from PDF.") from exc


def _extract_docx_text(file_path: Path) -> str:
    try:
        document = DocxDocument(str(file_path))
        return "\n".join(paragraph.text for paragraph in document.paragraphs)
    except Exception as exc:
        raise DocumentParsingError("Could not extract text from DOCX.") from exc


def _extract_txt_text(file_path: Path) -> str:
    try:
        return file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        try:
            return file_path.read_text(encoding="utf-8-sig")
        except UnicodeDecodeError as exc:
            raise DocumentParsingError("TXT file must use UTF-8 encoding.") from exc
    except OSError as exc:
        raise DocumentParsingError("Could not read TXT file.") from exc


def _normalize_text(text: str) -> str:
    text = text.lstrip("\ufeff")
    lines = [line.strip() for line in text.splitlines()]
    compact_lines = [line for line in lines if line]
    return "\n".join(compact_lines).strip()
