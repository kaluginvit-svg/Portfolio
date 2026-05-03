#!/usr/bin/env python3
"""
Скрипт для домашних заданий: промпты из homework_prompts.json, запрос к ProxyAPI.
Запрос температуры, опция тестового вопроса (Y). После выполнения — вывод ответа, температуры и модели.
"""

import json
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

from proxyapi_request import MODEL, PROXYAPI_CHAT_COMPLETIONS

PROMPTS_PATH = Path(__file__).resolve().parent / "homework_prompts.json"
MAX_TOKENS = 2000


def load_prompts():
    """Загружает список промптов из homework_prompts.json."""
    if not PROMPTS_PATH.exists():
        print(f"❌ Файл не найден: {PROMPTS_PATH}", file=sys.stderr)
        sys.exit(1)
    with open(PROMPTS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("prompts", [])


def main():
    prompts = load_prompts()
    if not prompts:
        print("❌ В homework_prompts.json нет промптов.", file=sys.stderr)
        sys.exit(1)

    print("\n📋 Домашние задания (промпты):\n")
    for i, p in enumerate(prompts, start=1):
        name = p.get("name", p.get("id", "Без названия"))
        print(f"  {i}. {name}")
    print()

    try:
        num = int(input("Введите порядковый номер промпта (1–{}): ".format(len(prompts))).strip())
        if num < 1 or num > len(prompts):
            print("❌ Неверный номер.")
            return
    except ValueError:
        print("❌ Введите число.")
        return

    prompt = prompts[num - 1]

    temperature = float(input("🌡 Введите temperature (0.0–2.0, по умолчанию 0.7): ").strip() or "0.7")
    if not 0.0 <= temperature <= 2.0:
        print("❌ Temperature должен быть от 0.0 до 2.0")
        return

    use_test = input("Использовать тестовый вопрос из промпта? (Y/n): ").strip().upper()
    if use_test in ("", "Y", "ДА"):
        user_text = prompt.get("test_input", "")
        if not user_text:
            print("❌ У выбранного промпта нет test_input.")
            return
        print("✅ Используется тестовый вопрос из промпта.\n")
    else:
        user_text = input("Введите свой текст запроса: ").strip()
        if not user_text:
            print("❌ Текст не может быть пустым.")
            return

    parts = [
        prompt.get("role", ""),
        prompt.get("context", ""),
        prompt.get("question", ""),
        prompt.get("format", ""),
    ]
    use_few_shot = False
    if prompt.get("few_shot_example"):
        few_shot_choice = input("Использовать few-shot пример в запросе? (Y/n): ").strip().upper()
        use_few_shot = few_shot_choice in ("", "Y", "ДА")
        if use_few_shot:
            parts.append("Few-shot пример (формат вывода):\n" + prompt["few_shot_example"])
            print("✅ Few-shot пример добавлен в системный промпт.\n")
    system_content = "\n\n".join(p for p in parts if p)

    api_key = os.getenv("PROXYAPI_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ Задайте PROXYAPI_API_KEY в .env", file=sys.stderr)
        sys.exit(1)

    messages = [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_text},
    ]

    print("⏳ Отправляем запрос к ProxyAPI...\n")
    resp = requests.post(
        PROXYAPI_CHAT_COMPLETIONS,
        json={
            "model": MODEL,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": MAX_TOKENS,
        },
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        timeout=120,
    )

    if not resp.ok:
        print(f"❌ Ошибка API: {resp.status_code}\n{resp.text}", file=sys.stderr)
        sys.exit(1)

    data = resp.json()
    content = data["choices"][0]["message"]["content"]
    usage = data.get("usage", {})
    total_tokens = usage.get("total_tokens", 0)
    model_name = data.get("model", MODEL)

    sep = "=" * 50
    print(sep)
    print("✅ Ответ (промпт: {})".format(prompt.get("name", prompt.get("id", ""))))
    print(sep)
    print(content)
    print(sep)
    print("ℹ️ Параметры запроса:")
    print("   Temperature: {}".format(temperature))
    print("   Модель: {}".format(model_name))
    print("   Использовано токенов: {}".format(total_tokens))
    print(sep)


if __name__ == "__main__":
    main()
