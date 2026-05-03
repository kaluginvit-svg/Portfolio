"""Загрузка настроек из переменных окружения и .env."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# .env рядом с этим файлом или в корне репозитория (родитель telegram_bot)
_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent

load_dotenv(_HERE / ".env")
load_dotenv(_ROOT / ".env")


@dataclass(frozen=True)
class Config:
    telegram_api_token: str
    openai_api_key: str
    openai_model: str
    """Полный URL эндпоинта MCP Streamable HTTP, например http://127.0.0.1:8765/mcp"""
    mcp_base_url: str
    openai_base_url: str | None


def load_config() -> Config:
    token = os.environ.get("TELEGRAM_API_TOKEN", "").strip()
    key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not token:
        raise RuntimeError(
            "Задайте TELEGRAM_API_TOKEN в .env (корень проекта или папка telegram_bot)."
        )
    if not key:
        raise RuntimeError("Задайте OPENAI_API_KEY в .env.")

    model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini").strip()
    mcp_url = os.environ.get("MCP_BASE_URL", "http://127.0.0.1:8765/mcp").strip()
    base = os.environ.get("OPENAI_BASE_URL", "").strip() or None

    return Config(
        telegram_api_token=token,
        openai_api_key=key,
        openai_model=model,
        mcp_base_url=mcp_url.rstrip("/"),
        openai_base_url=base,
    )
