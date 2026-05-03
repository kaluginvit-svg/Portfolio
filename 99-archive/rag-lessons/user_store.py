"""Локальный профиль пользователя для персонализации (JSON). Pinecone не заменяет."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parent
_PATH = _ROOT / "data" / "user_profiles.json"


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


@dataclass
class UserProfileView:
    user_id: int
    telegram_name: str
    first_seen: str
    last_seen: str
    message_count: int
    important_notes: str


class UserStore:
    def __init__(self, path: Path = _PATH) -> None:
        self._path = path
        self._data: dict[str, dict[str, Any]] = {}
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._load()

    def _load(self) -> None:
        if not self._path.is_file():
            return
        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                self._data = {str(k): v for k, v in raw.items() if isinstance(v, dict)}
        except (json.JSONDecodeError, OSError):
            self._data = {}

    def _save(self) -> None:
        self._path.write_text(json.dumps(self._data, ensure_ascii=False, indent=2), encoding="utf-8")

    def _key(self, user_id: int) -> str:
        return str(user_id)

    def touch(
        self,
        user_id: int,
        *,
        telegram_name: str | None = None,
        increment: bool = True,
    ) -> UserProfileView:
        """Обновить активность; increment — +1 к счётчику сообщений."""
        k = self._key(user_id)
        now_d = _today()
        tnow = _now_iso()
        if k not in self._data:
            self._data[k] = {
                "user_id": user_id,
                "first_seen": now_d,
                "last_seen": tnow,
                "message_count": 0,
                "important_notes": "",
                "telegram_name": (telegram_name or "").strip(),
            }
        rec = self._data[k]
        rec["last_seen"] = tnow
        if telegram_name:
            rec["telegram_name"] = telegram_name.strip()
        if increment:
            rec["message_count"] = int(rec.get("message_count", 0)) + 1
        self._save()
        return self.view(user_id)

    def set_memory_note(self, user_id: int, text: str) -> None:
        """Текст для блока «важная информация» (напр. после /remember)."""
        k = self._key(user_id)
        if k not in self._data:
            self.touch(user_id, increment=False)
            k = self._key(user_id)
        self._data[k]["important_notes"] = text.strip()[:2000]
        self._save()

    def view(self, user_id: int) -> UserProfileView:
        k = self._key(user_id)
        if k not in self._data:
            self.touch(user_id, increment=False)
            k = self._key(user_id)
        r = self._data[k]
        return UserProfileView(
            user_id=int(r.get("user_id", user_id)),
            telegram_name=str(r.get("telegram_name", "") or ""),
            first_seen=str(r.get("first_seen", _today())),
            last_seen=str(r.get("last_seen", _now_iso())),
            message_count=int(r.get("message_count", 0)),
            important_notes=str(r.get("important_notes", "") or ""),
        )

    def forget(self, user_id: int) -> bool:
        k = self._key(user_id)
        if k in self._data:
            del self._data[k]
            self._save()
            return True
        return False


_store: UserStore | None = None


def get_store() -> UserStore:
    global _store
    if _store is None:
        _store = UserStore()
    return _store
