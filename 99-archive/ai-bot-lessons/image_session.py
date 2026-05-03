"""
Отдельная ветка: ожидание промпта для генерации изображения (Images API).
"""

from __future__ import annotations

import asyncio


class ImagePromptSession:
    def __init__(self) -> None:
        self._waiting: set[int] = set()
        self._lock = asyncio.Lock()

    async def set_waiting(self, chat_id: int, active: bool) -> None:
        async with self._lock:
            if active:
                self._waiting.add(chat_id)
            else:
                self._waiting.discard(chat_id)

    async def is_waiting(self, chat_id: int) -> bool:
        async with self._lock:
            return chat_id in self._waiting

    async def clear(self, chat_id: int) -> None:
        async with self._lock:
            self._waiting.discard(chat_id)
