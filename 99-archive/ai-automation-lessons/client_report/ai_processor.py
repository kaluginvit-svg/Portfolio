"""
Структурированный JSON по транскрипции диалога через ProxyAPI (OpenAI-совместимый API).
Документация: https://proxyapi.ru
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Any

from dotenv import load_dotenv

ReportDict = dict[str, Any]

load_dotenv()

# База по умолчанию — нативный OpenAI-эндпоинт ProxyAPI
DEFAULT_PROXYAPI_BASE_URL = "https://api.proxyapi.ru/openai/v1"

STRING_KEYS = (
    "client_name",
    "topic",
    "main_request",
    "mood",
    "timeline_and_cost",
    "product_must_haves",
    "next_steps",
    "response_letter",
)

SYSTEM_PROMPT = """Ты аналитик переговоров и пресейл-консультант. По транскрипции диалога с клиентом верни ТОЛЬКО валидный JSON без markdown и без текста вокруг.

Строковые поля:
- client_name: имя или компания клиента; если неясно — краткое обозначение (например «Клиент»).
- topic: тема разговора в одном предложении.
- main_request: главная просьба или потребность клиента (2–4 предложения).
- mood: эмоциональный тон / настроение (кратко).
- timeline_and_cost: желаемые сроки и ожидаемая стоимость/бюджет (если в диалоге не сказано — «Не озвучено» или краткий вывод из контекста).
- product_must_haves: что точно должно войти в финальный продукт / результат; основные пожелания и обязательные элементы (списком через «; » или абзац).
- next_steps: рекомендуемые следующие шаги для менеджера (маркированный текст через «; » или короткий абзац).
- response_letter: готовый текст «ответного письма» клиенту РОВНО из трёх абзацев. Между абзацами ставь двойной перевод строки \\n\\n. В каждом абзаце — конкретные цифры (суммы, сроки, объёмы) и понятные предложения по сотрудничеству. Тон деловой, дружелюбный.

Массив software_options: 3–5 наиболее подходящих вариантов ПО под задачу клиента. Каждый элемент — объект с полями:
- software_name: название продукта / стека
- license_estimate: предварительная оценка лицензий (кол-во мест, редакция, подписка/разово; сумма если уместно)
- implementation_cost_estimate: оценка стоимости внедрения (интеграция, настройка, обучение). Используй актуальные рыночные ориентиры под РФ/релевантный рынок; для суммы бери ВЕРХНЮЮ границу типичного диапазона — ближе к 8-му децилю (дорогой, но реалистичный сценарий «под ключ»), не минимальную цену. Укажи валюту (₽ или USD). Пометь что оценка ориентировочная.
- implementation_timeline: сроки внедрения (диапазон недель/месяцев)

Если задача не про ПО — всё равно заполни software_options осмысленными ближайшими аналогами или напиши в software_name «Уточнить у клиента» и кратко в остальных полях."""


def _normalize_software_options(raw: Any) -> list[dict[str, str]]:
    if not isinstance(raw, list):
        return []
    out: list[dict[str, str]] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        out.append(
            {
                "software_name": str(item.get("software_name", "") or "").strip(),
                "license_estimate": str(item.get("license_estimate", "") or "").strip(),
                "implementation_cost_estimate": str(
                    item.get("implementation_cost_estimate", "") or ""
                ).strip(),
                "implementation_timeline": str(item.get("implementation_timeline", "") or "").strip(),
            }
        )
    return out


def _normalize_report(data: Any) -> ReportDict:
    if not isinstance(data, dict):
        raise ValueError("Ответ ИИ не является объектом JSON")
    out: ReportDict = {}
    for key in STRING_KEYS:
        val = data.get(key, "")
        if val is None:
            val = ""
        if isinstance(val, (dict, list)):
            out[key] = json.dumps(val, ensure_ascii=False)
        else:
            out[key] = str(val).strip()

    out["software_options"] = _normalize_software_options(data.get("software_options"))
    return out


def _extract_json_from_text(text: str) -> dict[str, Any]:
    text = text.strip()
    if not text:
        raise ValueError("Пустой ответ модели")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    m = re.search(r"\{[\s\S]*\}", text)
    if m:
        return json.loads(m.group(0))
    raise ValueError("Не удалось разобрать JSON из ответа модели")


def _api_key() -> str | None:
    """Ключ из кабинета ProxyAPI; OPENAI_API_KEY — запасной вариант той же схемы именования."""
    return (os.getenv("PROXYAPI_API_KEY") or os.getenv("OPENAI_API_KEY") or "").strip() or None


def _base_url() -> str:
    return (os.getenv("OPENAI_BASE_URL") or "").strip() or DEFAULT_PROXYAPI_BASE_URL


@dataclass(frozen=True)
class ProcessingResult:
    """Ответ модели + usage для отчёта о токенах."""

    data: ReportDict
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


def _usage_from_response(response: Any) -> tuple[int, int, int]:
    usage = getattr(response, "usage", None)
    if usage is None:
        return 0, 0, 0
    pt = int(getattr(usage, "prompt_tokens", None) or 0)
    ct = int(getattr(usage, "completion_tokens", None) or 0)
    tt = int(getattr(usage, "total_tokens", None) or 0)
    if tt == 0 and (pt or ct):
        tt = pt + ct
    return pt, ct, tt


def process_dialog_with_ai(text: str) -> ProcessingResult:
    """
    Отправляет транскрипцию в модель через ProxyAPI и возвращает поля отчёта.

    Переменные окружения: PROXYAPI_API_KEY (или OPENAI_API_KEY), OPENAI_BASE_URL (необязательно),
    OPENAI_MODEL, OPENAI_TEMPERATURE (необязательно; без неё — дефолт API).

    Returns:
        ProcessingResult: поля отчёта + токены из ответа API.
    """
    from openai import OpenAI

    transcript = (text or "").strip()
    if not transcript:
        raise ValueError("Пустая транскрипция")

    api_key = _api_key()
    if not api_key:
        raise RuntimeError(
            "Задайте PROXYAPI_API_KEY в .env (ключ в личном кабинете https://proxyapi.ru)"
        )

    model = (os.getenv("OPENAI_MODEL") or "gpt-4o-mini").strip()
    client = OpenAI(api_key=api_key, base_url=_base_url())
    user_content = f"Транскрипция диалога:\n\n{transcript}"

    req: dict[str, Any] = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        "response_format": {"type": "json_object"},
    }
    # Часть моделей (например новые в каталоге ProxyAPI) не принимают temperature != 1 —
    # тогда параметр не передаём. Явно задать: OPENAI_TEMPERATURE=0.3 в .env
    t_env = (os.getenv("OPENAI_TEMPERATURE") or "").strip()
    if t_env:
        req["temperature"] = float(t_env)

    response = client.chat.completions.create(**req)
    raw = response.choices[0].message.content or ""
    data = _extract_json_from_text(raw)
    pt, ct, tt = _usage_from_response(response)
    return ProcessingResult(
        data=_normalize_report(data),
        model=model,
        prompt_tokens=pt,
        completion_tokens=ct,
        total_tokens=tt,
    )


KP_SYSTEM_PROMPT = """Ты готовишь коммерческое предложение (КП) для клиента. Верни ТОЛЬКО валидный JSON без markdown.

Поля:
- document_title: заголовок документа (например «Коммерческое предложение на внедрение …»).
- client_ref: как обращаться к клиенту (кратко, из контекста).
- introduction: вводный абзац (3–5 предложений), тон деловой.
- kp_blocks: массив из 4–6 объектов { "title": "заголовок раздела", "body": "текст с конкретными цифрами, сроками, объёмами работ" } — предмет предложения, состав работ, сроки, стоимость (ориентир верхнего рынка при необходимости), гарантии.
- payment_and_terms: условия оплаты и этапность (один абзац).
- validity: срок действия оферты (например «30 календарных дней с даты направления»).
- signature_line: строка «С уважением, …» или «Готовы ответить на вопросы: …»

Цифры и сроки должны быть согласованы с входящим запросом и блоками КП."""


def _normalize_kp(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise ValueError("КП: ответ не JSON-объект")
    blocks_raw = data.get("kp_blocks")
    blocks: list[dict[str, str]] = []
    if isinstance(blocks_raw, list):
        for b in blocks_raw:
            if isinstance(b, dict):
                blocks.append(
                    {
                        "title": str(b.get("title", "") or "").strip(),
                        "body": str(b.get("body", "") or "").strip(),
                    }
                )
    return {
        "document_title": str(data.get("document_title", "") or "Коммерческое предложение").strip(),
        "client_ref": str(data.get("client_ref", "") or "").strip(),
        "introduction": str(data.get("introduction", "") or "").strip(),
        "kp_blocks": blocks,
        "payment_and_terms": str(data.get("payment_and_terms", "") or "").strip(),
        "validity": str(data.get("validity", "") or "").strip(),
        "signature_line": str(data.get("signature_line", "") or "").strip(),
    }


def generate_commercial_proposal(transcript: str, report_data: dict[str, Any]) -> dict[str, Any]:
    """
    Генерирует структуру КП для kp_template.html на основе запроса и полей отчёта.
    """
    from openai import OpenAI

    t = (transcript or "").strip()
    if not t:
        raise ValueError("Пустой текст запроса")

    api_key = _api_key()
    if not api_key:
        raise RuntimeError("Задайте PROXYAPI_API_KEY в .env")

    model = (os.getenv("OPENAI_MODEL") or "gpt-4o-mini").strip()
    client = OpenAI(api_key=api_key, base_url=_base_url())

    brief = {
        "client_name": report_data.get("client_name"),
        "topic": report_data.get("topic"),
        "main_request": report_data.get("main_request"),
        "timeline_and_cost": report_data.get("timeline_and_cost"),
        "product_must_haves": report_data.get("product_must_haves"),
        "software_options": report_data.get("software_options"),
    }
    user_content = (
        "Входящий запрос (исходный текст):\n\n"
        f"{t}\n\n"
        "Краткие данные анализа (для согласованности КП):\n"
        f"{json.dumps(brief, ensure_ascii=False, indent=2)}"
    )

    req: dict[str, Any] = {
        "model": model,
        "messages": [
            {"role": "system", "content": KP_SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        "response_format": {"type": "json_object"},
    }
    t_env = (os.getenv("OPENAI_TEMPERATURE") or "").strip()
    if t_env:
        req["temperature"] = float(t_env)

    response = client.chat.completions.create(**req)
    raw = response.choices[0].message.content or ""
    parsed = _extract_json_from_text(raw)
    return _normalize_kp(parsed)
