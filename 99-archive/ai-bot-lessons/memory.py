"""
Память диалога: режим и последние N сообщений на чат (async-безопасно).
"""

from __future__ import annotations

import asyncio


class ChatMemoryStore:
    """
    Хранит для каждого chat_id:
    - выбранный ключ режима (как в prompts.json);
    - историю сообщений в формате OpenAI: user / assistant по очереди.
    """

    def __init__(self, default_mode: str, max_messages: int) -> None:
        self._default_mode = default_mode
        self._max = max(1, max_messages)
        # chat_id -> {"mode": str, "messages": list[dict]}
        self._chats: dict[int, dict] = {}
        self._lock = asyncio.Lock()

    async def ensure_chat(self, chat_id: int) -> None:
        async with self._lock:
            if chat_id not in self._chats:
                self._chats[chat_id] = {
                    "mode": self._default_mode,
                    "messages": [],
                }

    async def get_mode(self, chat_id: int) -> str:
        async with self._lock:
            st = self._chats.get(chat_id)
            if not st:
                return self._default_mode
            return st["mode"]

    async def set_mode(self, chat_id: int, mode_key: str) -> None:
        async with self._lock:
            if chat_id not in self._chats:
                self._chats[chat_id] = {"mode": mode_key, "messages": []}
            else:
                self._chats[chat_id]["mode"] = mode_key

    async def reset(self, chat_id: int) -> None:
        async with self._lock:
            if chat_id in self._chats:
                self._chats[chat_id]["messages"] = []

    async def get_messages_for_api(self, chat_id: int) -> list[dict[str, str]]:
        """Последние max_messages записей для передачи в OpenAI (без system)."""
        async with self._lock:
            st = self._chats.get(chat_id)
            if not st:
                return []
            msgs = st["messages"]
            return list(msgs[-self._max :])

    async def append_user(self, chat_id: int, text: str) -> None:
        async with self._lock:
            st = self._chats.setdefault(
                chat_id,
                {"mode": self._default_mode, "messages": []},
            )
            st["messages"].append({"role": "user", "content": text})
            self._trim_locked(st)

    async def append_assistant(self, chat_id: int, text: str) -> None:
        async with self._lock:
            st = self._chats.setdefault(
                chat_id,
                {"mode": self._default_mode, "messages": []},
            )
            st["messages"].append({"role": "assistant", "content": text})
            self._trim_locked(st)

    def _trim_locked(self, st: dict) -> None:
        msgs: list = st["messages"]
        while len(msgs) > self._max:
            msgs.pop(0)
