from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - dotenv is installed in normal runtime
    load_dotenv = None


def _load_dotenv() -> None:
    if load_dotenv is not None:
        load_dotenv()


def _get_required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ValueError(f"Missing required environment variable: {name}")
    return value


def _get_int(name: str, default: int) -> int:
    value = os.getenv(name, "").strip()
    if not value:
        return default
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer, got {value!r}") from exc


def _parse_allowed_chat_ids(raw: str) -> set[int]:
    if not raw.strip():
        return set()
    result: set[int] = set()
    for item in raw.split(","):
        item = item.strip()
        if item:
            result.add(int(item))
    return result


@dataclass(frozen=True)
class Settings:
    telegram_bot_token: str
    openai_api_key: str
    openai_base_url: str
    openai_model: str
    embedding_model: str
    pinecone_api_key: str
    pinecone_index_name: str
    pinecone_namespace: str
    pinecone_index_dimension: int
    pinecone_cloud: str
    pinecone_region: str
    log_level: str
    top_k: int
    allowed_chat_ids: set[int]
    state_db_path: Path
    max_telegram_message_length: int

    @classmethod
    def from_env(cls) -> "Settings":
        _load_dotenv()
        return cls(
            telegram_bot_token=_get_required("TELEGRAM_BOT_TOKEN"),
            openai_api_key=_get_required("OPENAI_API_KEY"),
            openai_base_url=_get_required("OPENAI_BASE_URL"),
            openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip(),
            embedding_model=os.getenv("EMBEDDING_MODEL", "text-embedding-3-large").strip(),
            pinecone_api_key=_get_required("PINECONE_API_KEY"),
            pinecone_index_name=_get_required("PINECONE_INDEX_NAME"),
            pinecone_namespace=os.getenv("PINECONE_NAMESPACE", "telegram-team-chat").strip(),
            pinecone_index_dimension=_get_int("PINECONE_INDEX_DIMENSION", 3072),
            pinecone_cloud=os.getenv("PINECONE_CLOUD", "aws").strip(),
            pinecone_region=os.getenv("PINECONE_REGION", "us-east-1").strip(),
            log_level=os.getenv("LOG_LEVEL", "INFO").strip().upper(),
            top_k=_get_int("TOP_K", 5),
            allowed_chat_ids=_parse_allowed_chat_ids(os.getenv("BOT_ALLOWED_CHAT_IDS", "")),
            state_db_path=Path(os.getenv("STATE_DB_PATH", "bot_state.sqlite3")),
            max_telegram_message_length=_get_int("MAX_TELEGRAM_MESSAGE_LENGTH", 3900),
        )

    def validate_embedding_dimension(self) -> None:
        if self.embedding_model == "text-embedding-3-large" and self.pinecone_index_dimension != 3072:
            raise ValueError(
                "text-embedding-3-large requires PINECONE_INDEX_DIMENSION=3072."
            )
