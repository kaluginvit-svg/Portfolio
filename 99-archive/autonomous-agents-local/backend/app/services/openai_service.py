import json
from typing import AsyncGenerator

import httpx
from openai import AsyncOpenAI

from app.config import settings


def get_client() -> AsyncOpenAI:
    kwargs = {
        "api_key": settings.openai_api_key,
        "timeout": 120.0,
    }
    if settings.openai_base_url:
        kwargs["base_url"] = settings.openai_base_url.rstrip("/")
    if not settings.openai_ssl_verify:
        kwargs["http_client"] = httpx.AsyncClient(verify=False)
    return AsyncOpenAI(**kwargs)


async def chat_completion(
    client: AsyncOpenAI,
    system_prompt: str,
    user_prompt: str,
    model: str | None = None,
) -> str:
    model = model or settings.openai_model
    response = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,
    )
    return (response.choices[0].message.content or "").strip()


def parse_plan_json(raw: str) -> list[dict]:
    """Извлекает список шагов из ответа ChatGPT (может быть обёрнут в markdown)."""
    text = raw.strip()
    if text.startswith("```"):
        for marker in ("```json", "```"):
            if text.startswith(marker):
                text = text[len(marker) :].strip()
                break
        if text.endswith("```"):
            text = text[:-3].strip()
    data = json.loads(text)
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and "steps" in data:
        return data["steps"]
    if isinstance(data, dict) and "plan" in data:
        return data["plan"]
    return [data]
