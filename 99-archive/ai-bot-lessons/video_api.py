"""
Создание видео через POST /videos с телом application/json.

ProxyAPI (и часть прокси) не принимают application/x-www-form-urlencoded, который
может отправлять OpenAI SDK при пустом multipart — требуется JSON или multipart.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx
from openai import APIStatusError, AsyncOpenAI
from openai.types.video import Video

logger = logging.getLogger(__name__)


async def videos_create_json(client: AsyncOpenAI, *, model: str, prompt: str) -> Video:
    """
    Эквивалент openai.videos.create(model=..., prompt=...), но с Content-Type: application/json.
    """
    base = str(client.base_url).rstrip("/")
    url = f"{base}/videos"
    api_key = client.api_key or ""

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload: dict[str, Any] = {"model": model, "prompt": prompt}

    async with httpx.AsyncClient(timeout=httpx.Timeout(600.0, connect=60.0)) as hc:
        r = await hc.post(url, json=payload, headers=headers)

    if r.status_code >= 400:
        body: Any = None
        try:
            body = r.json()
        except Exception:
            body = None
        msg = r.text
        if isinstance(body, dict):
            err = body.get("error")
            if isinstance(err, dict) and err.get("message"):
                msg = str(err["message"])
            elif body.get("detail"):
                msg = str(body["detail"])
        logger.warning("videos POST failed %s: %s", r.status_code, msg)
        raise APIStatusError(message=msg, response=r, body=body)

    data = r.json()
    return Video.model_validate(data)
