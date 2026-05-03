"""
Управление контекстом диалога пользователей (в оперативной памяти).
"""

import logging
from typing import Any

from config import MAX_CONTEXT_MESSAGES

logger = logging.getLogger(__name__)

# user_id -> list of {"role": "user"|"assistant"|"system", "content": str}
_context: dict[int, list[dict[str, Any]]] = {}


def get_context(user_id: int) -> list[dict[str, Any]]:
    """Возвращает список сообщений контекста для пользователя."""
    return _context.get(user_id, []).copy()


def add_message(user_id: int, role: str, content: str) -> None:
    """Добавляет сообщение в контекст и обрезает старые, если превышен лимит."""
    if user_id not in _context:
        _context[user_id] = []
    _context[user_id].append({"role": role, "content": content})
    # Оставляем только последние MAX_CONTEXT_MESSAGES сообщений
    if len(_context[user_id]) > MAX_CONTEXT_MESSAGES:
        _context[user_id] = _context[user_id][-MAX_CONTEXT_MESSAGES:]
    logger.debug("Контекст user_id=%s: добавлено [%s], всего сообщений: %s", user_id, role, len(_context[user_id]))


def clear_context(user_id: int) -> None:
    """Очищает контекст диалога для пользователя."""
    if user_id in _context:
        del _context[user_id]
        logger.info("Контекст очищен для user_id=%s", user_id)
