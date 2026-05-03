"""File reading: CSV, plain text, PDF (best-effort)."""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)


def read_text_file(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def read_pdf_text(path: Path) -> tuple[str, list[str]]:
    warnings: list[str] = []
    text_parts: list[str] = []

    try:
        import pdfplumber

        with pdfplumber.open(str(path)) as pdf:
            for page in pdf.pages:
                t = page.extract_text() or ""
                if t.strip():
                    text_parts.append(t)
        if text_parts:
            return "\n".join(text_parts), warnings
    except Exception as e:
        warnings.append(f"pdfplumber failed: {e}")
        logger.debug("pdfplumber extract failed", exc_info=True)

    try:
        from PyPDF2 import PdfReader

        reader = PdfReader(str(path))
        for page in reader.pages:
            t = page.extract_text() or ""
            if t.strip():
                text_parts.append(t)
        if text_parts:
            return "\n".join(text_parts), warnings
    except Exception as e:
        warnings.append(f"PyPDF2 failed: {e}")
        logger.debug("PyPDF2 extract failed", exc_info=True)

    return "", warnings + ["Could not extract text from PDF"]


def read_contract_document(path: Path) -> tuple[str, list[str]]:
    suffix = path.suffix.lower()
    if suffix in {".txt", ".md"}:
        return read_text_file(path), []
    if suffix == ".pdf":
        return read_pdf_text(path)
    try:
        return read_text_file(path), []
    except OSError as e:
        return "", [str(e)]


def read_csv_dataframe(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str, keep_default_na=False)
