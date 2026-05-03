import json
import re
from typing import AsyncGenerator

import httpx
from openai import AsyncOpenAI

from app.config import settings
from app.services.openai_service import chat_completion, get_client, parse_plan_json


PLAN_SYSTEM = """Ты — эксперт по SEO. Твоя задача: составить пошаговый план анализа сайта по ссылке и генерации SEO-ядра.
Верни ответ ТОЛЬКО в формате JSON, без пояснений до и после.
Структура: массив шагов, каждый шаг — объект с полями:
- "step": номер шага (число)
- "title": краткое название шага
- "prompt": текст промпта для анализа (в промпте будет подставлена либо ссылка, либо текст страницы; используй плейсхолдер {{CONTENT}} там, где нужно подставить контент/ссылку).

Пример формата:
[
  {"step": 1, "title": "Сбор структуры", "prompt": "Проанализируй контент: {{CONTENT}}. Выпиши заголовки и структуру страницы."},
  {"step": 2, "title": "Ключевые слова", "prompt": "По контенту {{CONTENT}} выдели потенциальные ключевые слова."}
]
Сделай 5-6 шагов, покрывающих: структуру, ключевые слова, мета-теги, семантику, рекомендации. Ответ — только валидный JSON."""

FINAL_SYSTEM = """Ты — эксперт по SEO. На основе промежуточных результатов анализа сайта собери итоговое SEO-ядро.
SEO-ядро должно включать:
- список основных и дополнительных ключевых слов с частотностью/приоритетом;
- рекомендации по title, description, h1;
- рекомендации по структуре и контенту;
- краткий отчёт по текущему состоянию и приоритетным действиям.
Формат вывода: структурированный текст (можно с подзаголовками и списками), готовый к использованию."""

FINAL_SYSTEM_BATCH = """Ты — эксперт по SEO. Тебе даны результаты анализа нескольких сайтов-конкурентов.
Твоя задача: составить ЕДИНОЕ совокупное SEO-ядро для нового сайта (или доработки текущего), которое ГАРАНТИРОВАННО позволит опередить ВСЕ перечисленные сайты по поисковой выдаче.

Требования к итогу:
- Объединённый список ключевых слов: взять сильные стороны всех конкурентов, добавить недостающие у них ключевые запросы, расставить приоритеты так, чтобы покрыть и превзойти каждый сайт.
- Рекомендации по title, description, h1: лучшие практики с учётом слабых мест конкурентов (что у них не доделано — сделать сильнее).
- Структура и контент: как обойти всех по полноте, релевантности и удобству.
- Конкретные приоритетные действия: что внедрить в первую очередь, чтобы опередить каждый URL из списка.

Формат: структурированный текст с подзаголовками и списками, готовый к использованию. Цель — одно итоговое SEO-ядро, а не отдельные отчёты по сайтам."""


async def fetch_page_html(url: str) -> str:
    async with httpx.AsyncClient(follow_redirects=True, timeout=15.0) as client:
        try:
            r = await client.get(url)
            r.raise_for_status()
            return r.text
        except Exception as e:
            return f"[Ошибка загрузки страницы: {e}]"


def substitute_content(prompt_template: str, content: str) -> str:
    return prompt_template.replace("{{CONTENT}}", content).replace("{{URL}}", content)


def _format_openai_error(exc: Exception) -> str:
    """Читаемое сообщение об ошибке OpenAI/ProxyAPI."""
    msg = str(exc).strip()
    cause = getattr(exc, "__cause__", None)
    detail = str(cause).strip() if cause else msg
    combined = (msg + " " + detail).lower()

    if "401" in msg or "api_key" in combined or "invalid api key" in combined or "invalid_api_key" in combined or "authentication" in combined:
        return "Ошибка 401: неверный или не принятый API-ключ. Проверьте OPENAI_API_KEY в .env: ключ из личного кабинета ProxyAPI, без кавычек и пробелов, перезапустите контейнер."
    if "balance" in combined or "баланс" in combined or "quota" in combined or "insufficient" in combined or "payment" in combined or "402" in msg or "credits" in combined or "funds" in combined:
        return "Баланс ProxyAPI пуст или недостаточен. Пополните счёт в личном кабинете ProxyAPI."
    if "rate_limit" in combined or "rate limit" in combined:
        return "Превышен лимит запросов к API. Подождите и повторите."
    if "timeout" in combined:
        return "Таймаут при обращении к API. Проверьте сеть и повторите."
    if "connection" in msg.lower() or "connect" in msg.lower():
        hint = " Возможные причины: пустой баланс ProxyAPI (проверьте ЛК), неверный OPENAI_BASE_URL, недоступность API из контейнера, SSL (попробуйте OPENAI_SSL_VERIFY=false)."
        return f"Ошибка соединения: {detail[:200]}.{hint}"
    return f"Ошибка API: {msg[:300]}"


async def run_seo_analysis(
    url: str,
) -> AsyncGenerator[tuple[str, str], None]:
    """
    Генерирует события для лога: ("log", "сообщение") и в конце ("result", "финальный SEO текст").
    """
    try:
        client = get_client()
        if not settings.openai_api_key:
            yield "log", "Ошибка: OPENAI_API_KEY не задан."
            yield "result", ""
            return

        yield "log", f"Получена ссылка: {url}"

        # 1. Запрашиваем план у ChatGPT
        yield "log", "Запрос плана анализа у ChatGPT..."
        plan_raw = await chat_completion(
            client,
            PLAN_SYSTEM,
            "Составь пошаговый план (5-6 шагов) для анализа сайта по ссылке и генерации SEO-ядра. Верни результат в JSON, каждый шаг — отдельный промпт.",
        )
        try:
            steps = parse_plan_json(plan_raw)
        except json.JSONDecodeError as e:
            yield "log", f"Ошибка разбора плана: {e}"
            yield "result", ""
            return

        yield "log", f"Получен план из {len(steps)} шагов."

        # Решаем: передаём URL или HTML (по умолчанию всегда качаем HTML, т.к. у API нет доступа в интернет)
        content_for_prompts = url
        if not settings.use_url_directly:
            yield "log", "Загрузка HTML страницы..."
            html = await fetch_page_html(url)
            # Ограничиваем размер для промптов (оставляем в основном текст)
            text = re.sub(r"<script[^>]*>[\s\S]*?</script>", "", html, flags=re.I)
            text = re.sub(r"<style[^>]*>[\s\S]*?</style>", "", text, flags=re.I)
            text = re.sub(r"<[^>]+>", " ", text)
            text = " ".join(text.split())[:30000]
            content_for_prompts = text or html[:15000]
            yield "log", "HTML загружен и подготовлен для анализа."

        results = []
        for i, step_obj in enumerate(steps):
            step_num = step_obj.get("step", i + 1)
            title = step_obj.get("title", f"Шаг {step_num}")
            prompt_tpl = step_obj.get("prompt", step_obj.get("prompt_text", ""))
            if not prompt_tpl:
                continue
            prompt = substitute_content(prompt_tpl, content_for_prompts)
            yield "log", f"Шаг {step_num}: {title}..."
            answer = await chat_completion(client, "Ты — SEO-аналитик. Отвечай по существу.", prompt)
            results.append({"step": step_num, "title": title, "result": answer})
            yield "log", f"Шаг {step_num} выполнен."

        yield "log", "Формирование итогового SEO-ядра..."

        # Финальный запрос
        summary = "\n\n---\n\n".join(
            f"## Шаг {r['step']}: {r['title']}\n{r['result']}" for r in results
        )
        final_user = f"""Промежуточные результаты анализа сайта {url}:\n\n{summary}\n\nСобери из этого итоговое SEO-ядро (ключевые слова, рекомендации по title/description/h1, структура, приоритетные действия)."""
        final_seo = await chat_completion(client, FINAL_SYSTEM, final_user)
        yield "log", "Готово."
        yield "result", final_seo

    except Exception as e:
        yield "log", _format_openai_error(e)
        yield "result", ""


async def run_seo_analysis_batch(
    urls: list[str],
) -> AsyncGenerator[tuple[str, str], None]:
    """
    Анализирует список URL и формирует единое SEO-ядро, позволяющее опередить все сайты из списка.
    """
    if not urls:
        yield "log", "Список URL пуст."
        yield "result", ""
        return

    try:
        client = get_client()
        if not settings.openai_api_key:
            yield "log", "Ошибка: OPENAI_API_KEY не задан."
            yield "result", ""
            return

        yield "log", f"Получено URL: {len(urls)}"

        # План один раз
        yield "log", "Запрос плана анализа у ChatGPT..."
        plan_raw = await chat_completion(
            client,
            PLAN_SYSTEM,
            "Составь пошаговый план (5-6 шагов) для анализа сайта по ссылке и генерации SEO-ядра. Верни результат в JSON, каждый шаг — отдельный промпт.",
        )
        try:
            steps = parse_plan_json(plan_raw)
        except json.JSONDecodeError as e:
            yield "log", f"Ошибка разбора плана: {e}"
            yield "result", ""
            return

        yield "log", f"Получен план из {len(steps)} шагов."

        all_site_results: list[dict] = []  # [{"url": ..., "summary": "## Шаг 1...\n..."}, ...]

        for idx, url in enumerate(urls):
            yield "log", f"Анализ {idx + 1}/{len(urls)}: {url}"

            content_for_prompts = url
            if not settings.use_url_directly:
                yield "log", f"  Загрузка HTML..."
                html = await fetch_page_html(url)
                text = re.sub(r"<script[^>]*>[\s\S]*?</script>", "", html, flags=re.I)
                text = re.sub(r"<style[^>]*>[\s\S]*?</style>", "", text, flags=re.I)
                text = re.sub(r"<[^>]+>", " ", text)
                text = " ".join(text.split())[:30000]
                content_for_prompts = text or html[:15000]

            results = []
            for i, step_obj in enumerate(steps):
                step_num = step_obj.get("step", i + 1)
                title = step_obj.get("title", f"Шаг {step_num}")
                prompt_tpl = step_obj.get("prompt", step_obj.get("prompt_text", ""))
                if not prompt_tpl:
                    continue
                prompt = substitute_content(prompt_tpl, content_for_prompts)
                yield "log", f"  Шаг {step_num}: {title}..."
                answer = await chat_completion(client, "Ты — SEO-аналитик. Отвечай по существу.", prompt)
                results.append({"step": step_num, "title": title, "result": answer})
            summary = "\n\n---\n\n".join(
                f"## Шаг {r['step']}: {r['title']}\n{r['result']}" for r in results
            )
            all_site_results.append({"url": url, "summary": summary})
            yield "log", f"  Сайт {idx + 1}/{len(urls)} обработан."

        yield "log", "Формирование совокупного SEO-ядра (опережение всех сайтов)..."

        combined = "\n\n" + "=" * 60 + "\n\n".join(
            f"### Сайт: {r['url']}\n{r['summary']}" for r in all_site_results
        )
        sites_list = "\n".join(f"- {u}" for u in urls)
        final_user = f"""Ниже результаты анализа {len(urls)} сайтов-конкурентов. Составь единое SEO-ядро, которое позволит гарантированно опередить каждый из них по поисковой выдаче.

Список сайтов:
{sites_list}

Результаты по каждому:
{combined}

Итог: одно совокупное SEO-ядро (ключевые слова, title/description/h1, структура, приоритетные действия)."""
        final_seo = await chat_completion(client, FINAL_SYSTEM_BATCH, final_user)
        yield "log", "Готово."
        yield "result", final_seo

    except Exception as e:
        yield "log", _format_openai_error(e)
        yield "result", ""
