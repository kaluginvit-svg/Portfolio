"""
Работа с файлом кэша курсов (currency_rate.json).
"""
import json
import os
import time

CACHE_MAX_AGE_SEC = 24 * 3600
DEFAULT_PATH = "currency_rate.json"


def save_to_file(data: dict, path: str = DEFAULT_PATH) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def read_from_file(path: str = DEFAULT_PATH) -> dict | None:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def cache_fresh(path: str = DEFAULT_PATH) -> bool:
    try:
        mtime = os.path.getmtime(path)
        return (time.time() - mtime) < CACHE_MAX_AGE_SEC
    except OSError:
        return False


def get_rates_for_base(raw: dict | None, base: str) -> dict | None:
    """
    Возвращает данные одной базы (с полями base_code, rates) из сырого кэша.
    Поддерживает формат: одна база в корне или несколько баз по ключам (USD, EUR, ...).
    """
    if not raw:
        return None
    if raw.get("base_code") and "rates" in raw:
        return raw if raw.get("base_code") == base else None
    if base in raw and isinstance(raw[base], dict):
        return raw[base]
    return None
