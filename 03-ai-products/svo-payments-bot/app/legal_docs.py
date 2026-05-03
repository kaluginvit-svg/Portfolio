"""Документы ПДн в корне репозитория и публичные ссылки."""

from __future__ import annotations

from pathlib import Path
from urllib.parse import quote

from app.paths import PROJECT_ROOT

CONSENT_DOC_FILENAME = "Согласие на обработку ПДн.docx"
POLICY_DOC_FILENAME = "Политика конфиденциальности.docx"


def consent_doc_path() -> Path:
    return PROJECT_ROOT / CONSENT_DOC_FILENAME


def policy_doc_path() -> Path:
    return PROJECT_ROOT / POLICY_DOC_FILENAME


def build_public_doc_url(base_url: str, filename: str) -> str:
    b = base_url.rstrip("/")
    return f"{b}/{quote(filename)}"


def resolve_legal_urls(
    *,
    public_base_url: str | None,
    consent_url_override: str | None,
    policy_url_override: str | None,
) -> tuple[str, str]:
    """Возвращает (consent_url, policy_url) для текста и webhook."""
    if consent_url_override and policy_url_override:
        return consent_url_override.strip(), policy_url_override.strip()
    if public_base_url:
        base = public_base_url.strip().rstrip("/")
        return (
            build_public_doc_url(base, CONSENT_DOC_FILENAME),
            build_public_doc_url(base, POLICY_DOC_FILENAME),
        )
    return ("", "")
