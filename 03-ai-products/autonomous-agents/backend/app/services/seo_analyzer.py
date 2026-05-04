import json
import re
from typing import AsyncGenerator

import httpx
from openai import AsyncOpenAI

from app.config import settings
from app.services.openai_service import chat_completion, get_client, parse_plan_json


PLAN_SYSTEM = """Ты — эксперт по SEO. Составь пошаговый план анализа сайта по ссылке и генерации SEO-ядра.
Верни ответ ТОЛЬКО в формате JSON: массив шагов. Каждый шаг — объект с полями:
- "step": номер (число)
- "title": название шага
- "prompt": текст промпта (используй плейсхолдер {{CONTENT}} для контента/ссылки).
Пример: [{"step": 1, "title": "Структура", "prompt": "Проанализируй: {{CONTENT}}. Выпиши заголовки."}]
Сделай 5-6 шагов. Только валидный JSON."""

FINAL_SYSTEM = """Ты — эксперт по SEO. По результатам анализа собери итоговое SEO-ядро: ключевые слова, рекомендации по title/description/h1, структуре, приоритетные действия. Формат — структурированный текст."""

FINAL_SYSTEM_BATCH = """Ты — эксперт по SEO. По результатам анализа нескольких сайтов составь ЕДИНОЕ SEO-ядро: объединённые ключевые слова, рекомендации по title/description/h1, приоритетные действия. Один структурированный текст."""


async def fetch_page_html(url: str) -> str:
    async with httpx.AsyncClient(follow_redirects=True, timeout=15.0) as client:
        try:
            r = await client.get(url)
            r.raise_for_status()
            return r.text
        except Exception as e:
            return f"[Ошибка загрузки: {e}]"


def substitute_content(prompt_template: str, content: str) -> str:
    return prompt_template.replace("{{CONTENT}}", content).replace("{{URL}}", content)


def _format_error(exc: Exception) -> str:
    msg = str(exc).strip()
    if "401" in msg or "api_key" in msg.lower():
        return "Ошибка 401: проверьте OPENAI_API_KEY в .env"
    if "balance" in msg.lower() or "quota" in msg.lower():
        return "Недостаточно средств на балансе API. Пополните счёт."
    if "connection" in msg.lower() or "connect" in msg.lower():
        return f"Ошибка соединения: {msg[:200]}. Проверьте OPENAI_BASE_URL и доступ в интернет."
    return f"Ошибка API: {msg[:300]}"


async def run_seo_analysis(url: str) -> AsyncGenerator[tuple[str, str], None]:
    try:
        client = get_client()
        if not (settings.openai_base_url or settings.openai_api_key):
            yield "log", "Ошибка: задайте OPENAI_BASE_URL и OPENAI_API_KEY в .env"
            yield "result", ""
            return

        yield "log", f"Получена ссылка: {url}"
        yield "log", "Запрос плана анализа..."
        plan_raw = await chat_completion(
            client,
            PLAN_SYSTEM,
            "Составь план (5-6 шагов) для анализа сайта по ссылке и генерации SEO-ядра. Ответ — только JSON.",
        )
        try:
            steps = parse_plan_json(plan_raw)
        except json.JSONDecodeError as e:
            yield "log", f"Ошибка разбора плана: {e}"
            yield "result", ""
            return

        yield "log", f"План: {len(steps)} шагов."

        content_for_prompts = url
        if not settings.use_url_directly:
            yield "log", "Загрузка страницы..."
            html = await fetch_page_html(url)
            text = re.sub(r"<script[^>]*>[\s\S]*?</script>", "", html, flags=re.I)
            text = re.sub(r"<style[^>]*>[\s\S]*?</style>", "", text, flags=re.I)
            text = re.sub(r"<[^>]+>", " ", text)
            text = re.sub(r"\s+", " ", text).strip()[:50000]
            content_for_prompts = text or url

        results = []
        for i, step in enumerate(steps):
            if not isinstance(step, dict):
                continue
            title = step.get("title") or step.get("name") or f"Шаг {i+1}"
            prompt_tpl = step.get("prompt") or ""
            if not prompt_tpl:
                continue
            yield "log", f"Шаг {i+1}: {title}"
            try:
                prompt = substitute_content(prompt_tpl, content_for_prompts)
                answer = await chat_completion(client, "Ты — SEO-аналитик. Отвечай по существу.", prompt)
                results.append(f"### {title}\n{answer}")
            except Exception as e:
                results.append(f"### {title}\nОшибка: {_format_error(e)}")

        yield "log", "Формирование SEO-ядра..."
        final_user = "\n\n".join(results)
        try:
            final_seo = await chat_completion(client, FINAL_SYSTEM, final_user)
            yield "result", final_seo
        except Exception as e:
            yield "log", _format_error(e)
            yield "result", final_user

    except Exception as e:
        yield "log", _format_error(e)
        yield "result", ""


async def run_seo_analysis_batch(urls: list[str]) -> AsyncGenerator[tuple[str, str], None]:
    try:
        client = get_client()
        if not (settings.openai_base_url or settings.openai_api_key):
            yield "log", "Ошибка: задайте OPENAI_BASE_URL и OPENAI_API_KEY в .env"
            yield "result", ""
            return

        yield "log", f"URL: {len(urls)} шт."
        yield "log", "Запрос плана анализа..."
        plan_raw = await chat_completion(
            client,
            PLAN_SYSTEM,
            "Составь план (5-6 шагов) для анализа сайта по ссылке и генерации SEO-ядра. Ответ — только JSON.",
        )
        try:
            steps = parse_plan_json(plan_raw)
        except json.JSONDecodeError as e:
            yield "log", f"Ошибка разбора плана: {e}"
            yield "result", ""
            return

        yield "log", f"План: {len(steps)} шагов."
        all_results = []

        for url in urls:
            yield "log", f"Анализ: {url}"
            content_for_prompts = url
            if not settings.use_url_directly:
                html = await fetch_page_html(url)
                text = re.sub(r"<script[^>]*>[\s\S]*?</script>", "", html, flags=re.I)
                text = re.sub(r"<style[^>]*>[\s\S]*?</style>", "", text, flags=re.I)
                text = re.sub(r"<[^>]+>", " ", text)
                text = re.sub(r"\s+", " ", text).strip()[:50000]
                content_for_prompts = text or url

            for i, step in enumerate(steps):
                if not isinstance(step, dict):
                    continue
                title = step.get("title") or step.get("name") or f"Шаг {i+1}"
                prompt_tpl = step.get("prompt") or ""
                if not prompt_tpl:
                    continue
                try:
                    prompt = substitute_content(prompt_tpl, content_for_prompts)
                    answer = await chat_completion(client, "Ты — SEO-аналитик.", prompt)
                    all_results.append(f"## {url}\n### {title}\n{answer}")
                except Exception as e:
                    all_results.append(f"## {url}\n### {title}\nОшибка: {_format_error(e)}")

        yield "log", "Формирование итогового SEO-ядра..."
        final_user = "\n\n".join(all_results)
        try:
            final_seo = await chat_completion(client, FINAL_SYSTEM_BATCH, final_user)
            yield "result", final_seo
        except Exception as e:
            yield "log", _format_error(e)
            yield "result", final_user

    except Exception as e:
        yield "log", _format_error(e)
        yield "result", ""
