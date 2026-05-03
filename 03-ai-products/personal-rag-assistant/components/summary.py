"""Одно предложение резюме по тексту документа (после Docling)."""

from __future__ import annotations

import os

from openai import OpenAI


def summarize_one_sentence(*, client: OpenAI, text: str, model: str | None = None) -> str:
    used = model or os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini").strip() or "gpt-4o-mini"
    sample = (text or "").strip()
    if not sample:
        return "Файл обработан, но текста для краткого описания не найдено."
    if len(sample) > 14000:
        sample = sample[:14000] + "\n…"

    resp = client.chat.completions.create(
        model=used,
        messages=[
            {
                "role": "user",
                "content": (
                    "Сформулируй ровно одно короткое предложение на русском языке — "
                    "суть содержимого документа. Без вступлений и пояснений.\n\n" + sample
                ),
            }
        ],
        max_tokens=180,
        temperature=0.3,
    )
    out = (resp.choices[0].message.content or "").strip()
    return out or "Документ успешно проиндексирован."
