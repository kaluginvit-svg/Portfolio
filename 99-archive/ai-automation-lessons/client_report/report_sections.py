"""
Флаги секций PDF для режимов: анализ / только ПО / только шаги / полный отчёт.
"""

from __future__ import annotations

from typing import Any

# Ключи совпадают с именами в report_template.html (sections.*)
FULL: dict[str, bool] = {
    "client": True,
    "topic": True,
    "main": True,
    "timeline": True,
    "product": True,
    "software": True,
    "steps": True,
    "letter": True,
}

ANALYSIS: dict[str, bool] = {
    **{k: False for k in FULL},
    "client": True,
    "topic": True,
    "main": True,
    "timeline": True,
    "product": True,
}

SOFTWARE_ONLY: dict[str, bool] = {
    **{k: False for k in FULL},
    "client": True,
    "software": True,
}

STEPS_ONLY: dict[str, bool] = {
    **{k: False for k in FULL},
    "client": True,
    "steps": True,
}

MODE_MAP = {
    "full": FULL,
    "analysis": ANALYSIS,
    "software": SOFTWARE_ONLY,
    "steps": STEPS_ONLY,
}


def merge_sections_into_payload(payload: dict[str, Any], mode: str) -> dict[str, Any]:
    m = (mode or "full").strip().lower()
    sec = MODE_MAP.get(m, FULL).copy()
    out = dict(payload)
    out["sections"] = sec
    if m == "software":
        out["report_title"] = out.get("report_title") or "Варианты ПО и смета внедрения"
    elif m == "steps":
        out["report_title"] = out.get("report_title") or "Рекомендуемые шаги"
    elif m == "analysis":
        out["report_title"] = out.get("report_title") or "Анализ входящего запроса"
    elif m == "full":
        out["report_title"] = out.get("report_title") or "Отчёт по диалогу с клиентом"
    else:
        out["report_title"] = out.get("report_title") or "Отчёт по диалогу с клиентом"
    return out
