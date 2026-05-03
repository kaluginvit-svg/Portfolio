import json
import os
import sqlite3
import sys
from datetime import datetime

EXPORT_DIR_DEFAULT = r"C:\Users\Виталий\Downloads\Telegram Desktop\ИнфоПовод"


def prompt_path(prompt_text):
    try:
        return input(prompt_text).strip().strip('"')
    except EOFError:
        return ""


def flatten_text(value):
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        parts = []
        for item in value:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                text_part = item.get("text")
                if text_part is None:
                    continue
                parts.append(str(text_part))
            else:
                parts.append(str(item))
        return "".join(parts)
    if isinstance(value, dict):
        return str(value.get("text", ""))
    return str(value)


def find_export_json(export_dir):
    candidate = os.path.join(export_dir, "result.json")
    if os.path.isfile(candidate):
        return candidate

    for entry in os.listdir(export_dir):
        if not entry.lower().endswith(".json"):
            continue
        path = os.path.join(export_dir, entry)
        if os.path.isfile(path):
            return path
    return None


def load_export_json(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict) and "messages" in data:
        return data
    raise ValueError("JSON does not contain expected Telegram export structure.")

def sanitize_filename(value):
    name = []
    for ch in value:
        if ch.isalnum() or ch in ("_", "-", ".", " "):
            name.append(ch)
        else:
            name.append("_")
    cleaned = "".join(name).strip().strip(".")
    return cleaned or "tg_export"


def default_db_path(export_dir):
    base = os.path.basename(os.path.normpath(export_dir))
    base = sanitize_filename(base)
    filename = f"tg_catalog_{base}.db"
    return os.path.join(os.getcwd(), filename)


def sanitize_column_name(key):
    name = []
    for ch in key:
        if ch.isalnum() or ch == "_":
            name.append(ch)
        else:
            name.append("_")
    column = "".join(name).strip("_")
    if not column:
        column = "field"
    if column[0].isdigit():
        column = f"k_{column}"
    return column


def build_column_map(keys, reserved):
    column_map = {}
    used = set(reserved)
    for key in sorted(keys):
        if key == "id":
            continue
        col = sanitize_column_name(key)
        if col in used:
            col = f"{col}_raw"
        used.add(col)
        column_map[key] = col
    return column_map


def ensure_schema(conn, column_map):
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS posts (
            channel_id TEXT NOT NULL,
            channel_name TEXT,
            message_id INTEGER NOT NULL,
            tag TEXT,
            text_flat TEXT,
            text_json TEXT,
            media_json TEXT,
            raw_json TEXT,
            PRIMARY KEY (channel_id, message_id)
        )
        """
    )

    existing_columns = {
        row[1] for row in conn.execute("PRAGMA table_info(posts)").fetchall()
    }
    for column in column_map.values():
        if column not in existing_columns:
            conn.execute(f'ALTER TABLE posts ADD COLUMN "{column}" TEXT')


def normalize_value(value):
    if value is None:
        return None
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, float, str)):
        return value
    return json.dumps(value, ensure_ascii=False)


def is_null_value(value):
    return value is None


def normalize_message(message):
    text_raw = message.get("text")
    text_flat = flatten_text(text_raw)
    text_json = json.dumps(text_raw, ensure_ascii=False) if text_raw is not None else None

    media = message.get("media")
    media_json = json.dumps(media, ensure_ascii=False) if media is not None else None

    return {
        "message_id": message.get("id"),
        "text_flat": text_flat,
        "text_json": text_json,
        "media_json": media_json,
        "raw_json": json.dumps(message, ensure_ascii=False),
    }


def insert_messages(conn, channel_id, channel_name, messages, column_map):
    inserted = 0
    skipped = 0
    cursor = conn.cursor()
    base_columns = [
        "channel_id",
        "channel_name",
        "message_id",
        "tag",
        "text_flat",
        "text_json",
        "media_json",
        "raw_json",
    ]
    dynamic_columns = [column_map[key] for key in sorted(column_map)]
    all_columns = base_columns + dynamic_columns
    placeholders = ", ".join(["?"] * len(all_columns))
    column_list = ", ".join([f'"{c}"' for c in all_columns])
    for message in messages:
        msg_id = message.get("id")
        if msg_id is None:
            skipped += 1
            continue
        normalized = normalize_message(message)
        row = {
            "channel_id": channel_id,
            "channel_name": channel_name,
            "message_id": normalized["message_id"],
            "tag": None,
            "text_flat": normalized["text_flat"],
            "text_json": normalized["text_json"],
            "media_json": normalized["media_json"],
            "raw_json": normalized["raw_json"],
        }

        for key, column in column_map.items():
            row[column] = normalize_value(message.get(key))

        values = [row.get(col) for col in all_columns]
        cursor.execute(
            f'INSERT OR REPLACE INTO posts ({column_list}) VALUES ({placeholders})',
            values,
        )
        inserted += 1
    return inserted, skipped


def main():
    export_dir = prompt_path(
        "Введите путь к папке экспорта Telegram "
        f"(Enter = {EXPORT_DIR_DEFAULT}): "
    )
    if not export_dir:
        export_dir = EXPORT_DIR_DEFAULT
    if not export_dir or not os.path.isdir(export_dir):
        print("Папка не найдена. Проверьте путь и попробуйте снова.")
        sys.exit(1)

    default_db = default_db_path(export_dir)
    db_path = prompt_path(
        f"Путь к SQLite БД (Enter = {default_db}): "
    )
    if not db_path:
        db_path = default_db
    if os.path.isfile(db_path):
        os.remove(db_path)

    json_path = find_export_json(export_dir)
    if not json_path:
        print("Не найден JSON-файл экспорта (например, result.json).")
        sys.exit(1)

    try:
        export_data = load_export_json(json_path)
    except Exception as exc:
        print(f"Ошибка чтения JSON: {exc}")
        sys.exit(1)

    channel_id = str(export_data.get("id", "unknown"))
    channel_name = export_data.get("name") or export_data.get("title") or "unknown"
    messages = export_data.get("messages") or []

    message_keys = set()
    keys_with_values = set()
    for message in messages:
        if isinstance(message, dict):
            message_keys.update(message.keys())
            for key, value in message.items():
                if not is_null_value(value):
                    keys_with_values.add(key)

    reserved = {
        "channel_id",
        "channel_name",
        "message_id",
        "text_flat",
        "text_json",
        "media_json",
        "raw_json",
    }
    column_map = build_column_map(message_keys & keys_with_values, reserved)

    conn = sqlite3.connect(db_path)
    try:
        ensure_schema(conn, column_map)
        inserted, skipped = insert_messages(
            conn, channel_id, channel_name, messages, column_map
        )
        conn.commit()
    finally:
        conn.close()

    exported_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"Каталогизация завершена: {inserted} сообщений.")
    if skipped:
        print(f"Пропущено (без id): {skipped}.")
    print(f"Канал: {channel_name} (id={channel_id})")
    print(f"БД: {db_path}")
    print(f"Экспорт: {json_path}")
    print(f"Время: {exported_at}")


if __name__ == "__main__":
    main()
