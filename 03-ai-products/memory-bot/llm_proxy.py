# -*- coding: utf-8 -*-
"""Вызовы LLM через ProxyAPI (OpenAI-совместимый endpoint)."""
from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from openai import OpenAI

logger = logging.getLogger(__name__)


class StructuredReply(BaseModel):
    """Ответ модели: видимый текст + новые тезисы для БД."""

    theses: list[str] = Field(
        default_factory=list,
        description="Новые факты из этого хода диалога, короткие строки",
    )
    message: str = Field(..., description="Текст ответа пользователю в Telegram")


SYSTEM_BASE = """Ты дружелюбный AI-ассистент в Telegram.
Отвечай по делу, на языке пользователя.

В конце каждого внутреннего ответа ты должен вернуть СТРОГО JSON с двумя ключами:
- "theses": массив строк — только НОВЫЕ факты из ЭТОГО сообщения (имя, планы, предпочтения), которые стоит запомнить. Пустой массив, если нечего сохранять.
- "message": текст, который увидит пользователь (без служебных пометок).

Не дублируй факты, которые уже перечислены в блоке «Факты из базы данных»."""


def build_system_prompt(stored_theses: list[str]) -> str:
    if not stored_theses:
        return SYSTEM_BASE + "\n\n(Факты из базы данных пока пусты.)"
    lines = "\n".join(f"- {t}" for t in stored_theses)
    return (
        SYSTEM_BASE
        + "\n\nФакты из базы данных о пользователе:\n"
        + lines
    )


def _parse_json_content(raw: str) -> StructuredReply:
    raw = raw.strip()
    if raw.startswith("```"):
        parts = raw.split("```")
        for p in parts:
            p = p.strip()
            if p.startswith("json"):
                p = p[4:].strip()
            if p.startswith("{"):
                raw = p
                break
    data = json.loads(raw)
    return StructuredReply.model_validate(data)


def complete_structured(
    client: OpenAI,
    model: str,
    system_text: str,
    history_messages: list[dict],
    user_message: str,
    max_tokens: int = 2048,
) -> StructuredReply:
    """
    history_messages: [{"role":"user"|"assistant","content":"..."}, ...]
    """
    messages: list[dict] = [{"role": "system", "content": system_text}]
    messages.extend(history_messages)
    messages.append({"role": "user", "content": user_message})

    # 1) Пробуем structured output (как в уроке OpenAI)
    try:
        resp = client.beta.chat.completions.parse(
            model=model,
            messages=messages,
            response_format=StructuredReply,
            max_tokens=max_tokens,
            temperature=0.7,
        )
        parsed = resp.choices[0].message.parsed
        if parsed is not None:
            return parsed
    except Exception as e:
        logger.info("beta.chat.completions.parse недоступен (%s), fallback JSON", e)

    # 2) JSON mode + ручной разбор (совместимо с большинством прокси)
    messages[0]["content"] = (
        system_text
        + '\n\nОтветь одним JSON-объектом без markdown: {"theses": ["..."], "message": "..."}'
    )
    resp2 = client.chat.completions.create(
        model=model,
        messages=messages,
        response_format={"type": "json_object"},
        max_tokens=max_tokens,
        temperature=0.7,
    )
    raw = resp2.choices[0].message.content or "{}"
    try:
        return _parse_json_content(raw)
    except Exception as e:
        logger.exception("Не удалось разобрать JSON: %s", raw[:500])
        raise RuntimeError("Модель вернула невалидный JSON") from e
