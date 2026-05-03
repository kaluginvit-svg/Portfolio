"""
Конфигурация бота: токены и настройки из .env.
Эндпойнты ProxyAPI импортируются из proxyapi_request.py (единый источник).
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Загружаем .env из корня проекта
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(env_path)

# Telegram
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# ProxyAPI: базовый URL и путь — из proxyapi_request.py
from proxyapi_request import PROXYAPI_BASE

PROXYAPI_API_KEY = os.getenv("PROXYAPI_API_KEY", "")
AI_MODEL = "gpt-5-mini-2025-08-07"

# Лимиты контекста (сколько последних пар сообщений хранить)
MAX_CONTEXT_MESSAGES = 20
