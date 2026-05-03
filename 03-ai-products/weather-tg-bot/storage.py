"""Хранение данных пользователей в User_Data.json. Формат: {"<user_id>": {"city", "lat", "lon", "notifications"}}."""
import json
import os

USER_DATA_FILE = "User_Data.json"


def _read_data() -> dict:
    try:
        if os.path.isfile(USER_DATA_FILE):
            with open(USER_DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        pass
    return {}


def _write_data(data: dict) -> None:
    try:
        with open(USER_DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except OSError:
        pass


def load_user(user_id: int) -> dict:
    data = _read_data()
    return data.get(str(user_id), {})


def save_user(user_id: int, data: dict) -> None:
    all_data = _read_data()
    all_data[str(user_id)] = dict(data)
    _write_data(all_data)
