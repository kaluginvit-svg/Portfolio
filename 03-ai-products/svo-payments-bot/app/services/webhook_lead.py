"""Отправка завершённой заявки на внешний HTTP-вебхук (POST JSON)."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

import aiohttp

log = logging.getLogger(__name__)


def _json_safe(payload: dict[str, Any]) -> dict[str, Any]:
    """Только типы, пригодные для json.dumps."""
    out: dict[str, Any] = {}
    for k, v in payload.items():
        if v is None or isinstance(v, (str, int, float, bool)):
            out[k] = v
        elif isinstance(v, list):
            out[k] = v
        elif isinstance(v, dict):
            out[k] = v
        else:
            out[k] = str(v)
    return out


async def post_json_envelope(
    url: str,
    secret: str | None,
    envelope: dict[str, Any],
    *,
    timeout_sec: float = 15.0,
) -> None:
    if not url:
        return
    body = _json_safe(envelope)
    headers = {"Content-Type": "application/json"}
    if secret:
        headers["X-Webhook-Secret"] = secret
    timeout = aiohttp.ClientTimeout(total=timeout_sec)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(url, json=body, headers=headers) as resp:
                txt = await resp.text()
                if resp.status >= 400:
                    log.warning(
                        "LEAD_WEBHOOK_URL ответ %s: %s",
                        resp.status,
                        (txt[:500] + "…") if len(txt) > 500 else txt,
                    )
    except TimeoutError:
        log.warning("LEAD_WEBHOOK_URL: таймаут (%ss)", timeout_sec)
    except aiohttp.ClientError as e:
        log.warning("LEAD_WEBHOOK_URL: ошибка клиента %s", e)
    except Exception:
        log.exception("LEAD_WEBHOOK_URL: неожиданная ошибка")


async def post_lead_completed(
    url: str,
    secret: str | None,
    payload: dict[str, Any],
    *,
    timeout_sec: float = 15.0,
) -> None:
    await post_json_envelope(
        url,
        secret,
        {
            "event": "lead_completed",
            "sent_at": datetime.now(timezone.utc).isoformat(),
            "lead": _json_safe(payload),
        },
        timeout_sec=timeout_sec,
    )


async def post_quiz_webhook(
    url: str,
    secret: str | None,
    payload: dict[str, Any],
    *,
    timeout_sec: float = 15.0,
) -> None:
    """Отправка квиза: event + sent_at + плоские поля payload (ТЗ)."""
    sent_at = datetime.now(timezone.utc).isoformat()
    envelope: dict[str, Any] = {"event": "quiz_submitted", "sent_at": sent_at, **_json_safe(payload)}
    await post_json_envelope(url, secret, envelope, timeout_sec=timeout_sec)
