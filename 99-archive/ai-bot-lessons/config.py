"""
Конфигурация бота: переменные окружения и загрузка prompts.json.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

# Загружаем .env из каталога проекта
load_dotenv()


@dataclass(frozen=True)
class PromptEntry:
    """Один режим из prompts.json."""

    key: str
    name: str
    description: str
    system_prompt: str


@dataclass(frozen=True)
class PromptsConfig:
    """Распарсенный prompts.json."""

    default_prompt: str
    prompts: dict[str, PromptEntry]

    def get_system_prompt(self, mode_key: str) -> str:
        entry = self.prompts.get(mode_key)
        if entry is None:
            entry = self.prompts[self.default_prompt]
        return entry.system_prompt


def _parse_prompts(data: dict[str, Any]) -> PromptsConfig:
    default_key = data.get("default_prompt", "assistant")
    raw: dict[str, Any] = data.get("prompts") or {}
    prompts: dict[str, PromptEntry] = {}
    for key, item in raw.items():
        if not isinstance(item, dict):
            continue
        prompts[key] = PromptEntry(
            key=key,
            name=str(item.get("name", key)),
            description=str(item.get("description", "")),
            system_prompt=str(item.get("system_prompt", "")),
        )
    if default_key not in prompts and prompts:
        default_key = next(iter(prompts))
    elif not prompts:
        raise ValueError("prompts.json: секция prompts пуста")
    return PromptsConfig(default_prompt=default_key, prompts=prompts)


def load_prompts_file(path: str | Path | None = None) -> PromptsConfig:
    """Читает и валидирует prompts.json."""
    base = Path(path or os.getenv("PROMPTS_PATH", "prompts.json"))
    if not base.is_absolute():
        base = Path(__file__).resolve().parent / base
    with open(base, encoding="utf-8") as f:
        data = json.load(f)
    return _parse_prompts(data)


# --- Переменные окружения (токены и параметры модели) ---
# ProxyAPI: ключ из личного кабинета https://proxyapi.ru — в OPENAI_API_KEY или PROXYAPI_API_KEY
# База по умолчанию: нативный OpenAI-эндпоинт ProxyAPI (см. документацию «Генерация текста — OpenAI»)

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "") or os.getenv("PROXYAPI_API_KEY", "")
# Прямой OpenAI: https://api.openai.com/v1  |  ProxyAPI (OpenAI): https://api.proxyapi.ru/openai/v1
OPENAI_BASE_URL: str = os.getenv(
    "OPENAI_BASE_URL",
    "https://api.proxyapi.ru/openai/v1",
)
OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
MEMORY_MAX_MESSAGES: int = int(os.getenv("MEMORY_MAX_MESSAGES", "5"))

def _usd_env(key: str, default: str) -> Decimal:
    return Decimal(os.getenv(key, default))


# --- Sora: генерация видео (POST /videos) — только model/prompt, как в документации OpenAI ---
VIDEO_MODEL: str = os.getenv("VIDEO_MODEL", "sora-2")

# --- Изображения: POST /images/generations (ImageModel в OpenAI SDK: gpt-image-1.5, …) ---
# gpt-image-1.5 + quality=low — см. документацию GPT Image 1.5
IMAGE_MODEL: str = os.getenv("IMAGE_MODEL", "gpt-image-1.5")
IMAGE_QUALITY: str = os.getenv("IMAGE_QUALITY", "low")
IMAGE_SIZE: str = os.getenv("IMAGE_SIZE", "1024x1024")
# Оценка в USD за 1 картинку (low, 1024x1024; подстройте под ProxyAPI)
GPT_IMAGE_15_LOW_USD: Decimal = _usd_env("GPT_IMAGE_15_LOW_USD", "0.009")

# --- Цены для оценки в рублях (USD за 1M токенов; подставьте под вашу модель / тариф ProxyAPI) ---


PRICE_INPUT_PER_1M_USD: Decimal = _usd_env("PRICE_INPUT_PER_1M_USD", "0.15")
PRICE_OUTPUT_PER_1M_USD: Decimal = _usd_env("PRICE_OUTPUT_PER_1M_USD", "0.60")
# Оценка Sora-2 по секундам (подстройте под вашу сетку; в биллинге API может отличаться)
SORA2_USD_PER_SECOND: Decimal = _usd_env("SORA2_USD_PER_SECOND", "0.10")
