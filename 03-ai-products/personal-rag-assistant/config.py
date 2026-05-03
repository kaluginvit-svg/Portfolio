"""
Валидация окружения при старте (VPg07).
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class BotConfig:
    telegram_token: str
    max_file_mb: int
    user_doc_chunk_size: int


REQUIRED_VARS = (
    "TELEGRAM_BOT_TOKEN",
    "PINECONE_API_KEY",
    "PINECONE_INDEX_NAME",
)


def load_config() -> BotConfig:
    load_dotenv()

    missing = [name for name in REQUIRED_VARS if not (os.getenv(name) or "").strip()]
    if missing:
        raise ValueError(
            f"Отсутствуют переменные окружения: {', '.join(missing)}. См. .env.example."
        )

    key_ok = (os.getenv("PROXYAPI_API_KEY") or "").strip() or (os.getenv("OPENAI_API_KEY") or "").strip()
    url_ok = (os.getenv("PROXYAPI_BASE_URL") or "").strip() or (os.getenv("OPENAI_BASE_URL") or "").strip()
    if not key_ok or not url_ok:
        raise ValueError(
            "Нужны PROXYAPI_API_KEY и PROXYAPI_BASE_URL "
            "(или OPENAI_API_KEY и OPENAI_BASE_URL). См. .env.example."
        )

    max_mb = int(os.getenv("HAY_V2_MAX_FILE_MB", "20"))
    chunk = int(os.getenv("HAY_V2_USER_DOC_CHUNK_SIZE", "1200"))

    return BotConfig(
        telegram_token=os.getenv("TELEGRAM_BOT_TOKEN", "").strip(),
        max_file_mb=max(1, min(max_mb, 100)),
        user_doc_chunk_size=max(256, min(chunk, 8192)),
    )
