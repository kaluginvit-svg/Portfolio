"""
Фильтр сообщений для записи в Pinecone (как в исходном bot.py).
"""

from __future__ import annotations

import re


def should_store_message(text: str) -> bool:
    """
    Сохраняем только осмысленный пользовательский текст.
    """
    if not text or not text.strip():
        return False

    normalized = text.strip().lower()
    if normalized.startswith("/"):
        return False

    if len(normalized) < 6:
        return False

    normalized = re.sub(r"\s+", " ", normalized).strip(" \t\n\r.!?,:;\"'()[]{}")

    technical = {"start", "help", "menu", "settings", "clear"}
    if normalized in technical:
        return False

    junk = {
        "ок",
        "ok",
        "okay",
        "понятно",
        "ясно",
        "спасибо",
        "спс",
        "thanks",
        "thx",
        "пж",
        "плиз",
        "pls",
        "привет",
        "здравствуйте",
        "добрый день",
        "доброе утро",
        "добрый вечер",
        "ага",
        "угу",
        "нет",
        "да",
        "хорошо",
        "ладно",
        "отлично",
        "хаха",
        "lol",
    }
    return normalized not in junk
