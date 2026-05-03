"""
Клиент для общения с AI через ProxyAPI (OpenAI-совместимый API).
"""

import logging
from typing import Any

from openai import OpenAI

from config import AI_MODEL, PROXYAPI_API_KEY, PROXYAPI_BASE

logger = logging.getLogger(__name__)

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    """Возвращает клиент OpenAI, настроенный на ProxyAPI."""
    global _client
    if _client is None:
        _client = OpenAI(
            base_url=PROXYAPI_BASE,
            api_key=PROXYAPI_API_KEY,
        )
    return _client


def get_ai_response(messages: list[dict[str, Any]]) -> str:
    """
    Отправляет сообщения в модель и возвращает текстовый ответ.
    messages: список вида [{"role": "user"|"assistant"|"system", "content": "..."}]
    """
    if not PROXYAPI_API_KEY:
        logger.error("PROXYAPI_API_KEY не задан")
        raise ValueError("PROXYAPI_API_KEY не задан в .env")

    client = _get_client()
    try:
        response = client.chat.completions.create(
            model=AI_MODEL,
            messages=messages,
        )
        content = response.choices[0].message.content or ""
        usage = getattr(response, "usage", None)
        if usage:
            logger.debug("Использовано токенов: %s", getattr(usage, "total_tokens", "?"))
        return content
    except Exception as e:
        logger.exception("Ошибка при запросе к ProxyAPI: %s", e)
        raise
