"""Настройки из переменных окружения."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

log = logging.getLogger(__name__)


def _env(key: str, default: str = "") -> str:
    return (os.getenv(key) or default).strip()


def _env_int(key: str) -> int | None:
    raw = os.getenv(key)
    if raw is None or not str(raw).strip():
        return None
    try:
        return int(str(raw).strip())
    except ValueError:
        return None


def sqlite_path_from_database_url(url: str) -> Path:
    """Парсит sqlite:///leads.db или sqlite:///C:/path/leads.db."""
    prefix = "sqlite:///"
    if not url.strip().lower().startswith("sqlite:///"):
        raise ValueError("DATABASE_URL должен начинаться с sqlite:///")
    rest = url.strip()[len(prefix) :].strip()
    if not rest:
        rest = "leads.db"
    return Path(rest)


def _optional_url(key: str) -> str | None:
    raw = os.getenv(key)
    if raw is None or not str(raw).strip():
        return None
    u = str(raw).strip()
    if not u.lower().startswith(("http://", "https://")):
        log.warning("%s должен начинаться с http:// или https:// — значение проигнорировано", key)
        return None
    return u


@dataclass(frozen=True)
class Settings:
    bot_token: str
    admin_chat_id: int | None
    contact_text: str
    database_path: Path
    log_level: str
    lead_webhook_url: str | None
    lead_webhook_secret: str | None
    legal_docs_public_base_url: str | None
    personal_data_consent_url: str | None
    personal_data_policy_url: str | None

    @classmethod
    def from_env(cls) -> Settings:
        db_url = _env("DATABASE_URL", "sqlite:///leads.db")
        return cls(
            bot_token=_env("BOT_TOKEN"),
            admin_chat_id=_env_int("ADMIN_CHAT_ID"),
            contact_text=_env(
                "CONTACT_TEXT",
                "Свяжитесь с нами удобным способом из описания бота.",
            ),
            database_path=sqlite_path_from_database_url(db_url),
            log_level=_env("LOG_LEVEL", "INFO").upper() or "INFO",
            lead_webhook_url=_optional_url("LEAD_WEBHOOK_URL"),
            lead_webhook_secret=_env("LEAD_WEBHOOK_SECRET") or None,
            legal_docs_public_base_url=_optional_url("LEGAL_DOCS_PUBLIC_BASE_URL"),
            personal_data_consent_url=_optional_url("PERSONAL_DATA_CONSENT_URL"),
            personal_data_policy_url=_optional_url("PERSONAL_DATA_POLICY_URL"),
        )


def get_settings() -> Settings:
    return Settings.from_env()
