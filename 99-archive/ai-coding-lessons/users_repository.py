"""Доступ к таблице пользователей в SQLite."""
import json
import sqlite3
from typing import Optional

from settings import DB_PATH


def insert_user(name: str, tags: Optional[list] = None) -> int:
    """
    Вставляет строку пользователя. Возвращает lastrowid.
    Не предназначено для прямого импорта извне пакета — используйте api.add_user.
    """
    if tags is None:
        tags = []
    row_tags = list(tags)
    row_tags.append("new")
    payload = json.dumps(row_tags, ensure_ascii=False)

    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO users (name, tags) VALUES (?, ?)",
            (name, payload),
        )
        conn.commit()
        last_id = cur.lastrowid

    if last_id is None:
        raise RuntimeError("Не удалось получить id после INSERT")
    return int(last_id)
