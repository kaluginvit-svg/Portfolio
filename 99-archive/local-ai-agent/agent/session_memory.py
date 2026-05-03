"""
Общая логика памяти диалога (CLI и Telegram).
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MAX_STORED_TURNS = 80
_log = logging.getLogger("local_agent.memory")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_memory_file(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {"messages": [], "turn_summaries": []}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        _log.warning("Не прочитан %s (%s), пустая память.", path, e)
        return {"messages": [], "turn_summaries": []}
    data.setdefault("messages", [])
    data.setdefault("turn_summaries", [])
    return data


def save_memory_file(path: Path, data: dict[str, Any]) -> None:
    msgs = data.get("messages", [])
    if len(msgs) > MAX_STORED_TURNS * 2:
        data["messages"] = msgs[-MAX_STORED_TURNS * 2 :]
    summ = data.get("turn_summaries", [])
    if len(summ) > MAX_STORED_TURNS:
        data["turn_summaries"] = summ[-MAX_STORED_TURNS:]
    try:
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError as e:
        _log.error("Не удалось записать %s: %s", path, e)
        raise


def pairs_from_memory(messages: list) -> list[dict[str, str]]:
    """messages: [{role, content}, ...] → [{user, assistant}, ...]"""
    pairs: list[dict[str, str]] = []
    pending_user: str | None = None
    for m in messages:
        role = m.get("role")
        content = (m.get("content") or "").strip()
        if role == "user":
            pending_user = content
        elif role == "assistant" and pending_user is not None:
            pairs.append({"user": pending_user, "assistant": content})
            pending_user = None
    return pairs


def append_turn(
    memory: dict[str, Any],
    user_text: str,
    assistant_text: str,
    summary_line: str,
) -> None:
    memory.setdefault("messages", [])
    memory.setdefault("turn_summaries", [])
    memory["messages"].extend(
        [
            {"role": "user", "content": user_text, "ts": now_iso()},
            {"role": "assistant", "content": assistant_text, "ts": now_iso()},
        ]
    )
    memory["turn_summaries"].append(
        {"ts": now_iso(), "summary": summary_line[:500]}
    )


def load_telegram_store(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {"chats": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        _log.warning("Не прочитан %s (%s).", path, e)
        return {"chats": {}}
    data.setdefault("chats", {})
    return data


def save_telegram_store(path: Path, store: dict[str, Any]) -> None:
    store.setdefault("chats", {})
    for _cid, mem in list(store["chats"].items()):
        msgs = mem.get("messages", [])
        if len(msgs) > MAX_STORED_TURNS * 2:
            mem["messages"] = msgs[-MAX_STORED_TURNS * 2 :]
        summ = mem.get("turn_summaries", [])
        if len(summ) > MAX_STORED_TURNS:
            mem["turn_summaries"] = summ[-MAX_STORED_TURNS:]
    try:
        path.write_text(json.dumps(store, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError as e:
        _log.error("Не удалось записать %s: %s", path, e)
        raise


def get_chat_bucket(store: dict[str, Any], chat_id: int) -> dict[str, Any]:
    key = str(chat_id)
    store.setdefault("chats", {})
    if key not in store["chats"]:
        store["chats"][key] = {"messages": [], "turn_summaries": []}
    return store["chats"][key]
