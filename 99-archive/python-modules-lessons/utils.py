from __future__ import annotations

from database import load_notes, save_notes


def add_note(text: str) -> None:
    notes = load_notes()
    notes.append(text)
    save_notes(notes)


def list_notes() -> list[str]:
    return load_notes()


def delete_note(number: int) -> str:
    notes = load_notes()
    index = number - 1
    if index < 0 or index >= len(notes):
        raise ValueError("Неверный номер заметки")
    removed = notes.pop(index)
    save_notes(notes)
    return removed

