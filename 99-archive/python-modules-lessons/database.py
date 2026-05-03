from __future__ import annotations

import json
import sys
from pathlib import Path

# Храним заметки рядом со скриптами приложения.
NOTES_FILE = Path(__file__).with_name("notes_data.json")


def load_notes() -> list[str]:
    """Загружает список заметок из файла или возвращает пустой список."""
    if not NOTES_FILE.exists():
        return []
    try:
        return json.loads(NOTES_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        print("Файл заметок поврежден. Создаю новый.", file=sys.stderr)
        return []


def save_notes(notes: list[str]) -> None:
    """Сохраняет список заметок в файл."""
    NOTES_FILE.write_text(json.dumps(notes, ensure_ascii=False, indent=2), encoding="utf-8")

