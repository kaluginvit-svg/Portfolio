#!/usr/bin/env python3
"""
Скрипт: тот же функционал, но через ProxyAPI (OpenAI-совместимый API).
Параметры из терминала; API-ключ из .env.
Использует HTTP-запросы (requests).

Все эндпойнты ProxyAPI заданы здесь — их импортируют config.py и proxyapi_client.
"""

import os
import sys

import requests
from dotenv import load_dotenv

load_dotenv()

# --- Эндпойнты ProxyAPI (единый источник для проекта) ---
PROXYAPI_BASE = "https://api.proxyapi.ru/openai/v1"
PROXYAPI_CHAT_COMPLETIONS = f"{PROXYAPI_BASE}/chat/completions"
MODEL = "gpt-4.1-2025-04-14"


def main():
    # Получаем параметры от пользователя
    try:
        question = input("💬 Введите ваш вопрос: ").strip()
        if not question:
            print("❌ Вопрос не может быть пустым")
            return

        temperature = float(input("🌡 Введите temperature (0.0-2.0, по умолчанию 0.7): ") or "0.7")
        if not 0.0 <= temperature <= 1.0:
            print("❌ Temperature должен быть от 0.0 до 1.0")
            return

        max_tokens = int(input("🔢 Введите max_tokens (по умолчанию 1000): ") or "1000")
        if max_tokens <= 0:
            print("❌ max_tokens должен быть больше 0")
            return

        system_message = input("⚙️ Введите system message (опционально): ").strip()

        print("\n⏳ Отправляем запрос к OpenAI...")
    except ValueError as e:
        print(f"❌ Неверный формат: {e}")
        return

    api_key = os.getenv("PROXYAPI_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Ошибка: задайте PROXYAPI_API_KEY или OPENAI_API_KEY в файле .env", file=sys.stderr)
        sys.exit(1)

    messages = []
    if system_message:
        messages.append({"role": "system", "content": system_message})
    messages.append({"role": "user", "content": question})

    url = PROXYAPI_CHAT_COMPLETIONS
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    payload = {
        "model": MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    resp = requests.post(url, json=payload, headers=headers, timeout=60)

    if not resp.ok:
        print(f"Ошибка API: {resp.status_code}\n{resp.text}", file=sys.stderr)
        sys.exit(1)

    data = resp.json()
    content = data["choices"][0]["message"]["content"]
    usage = data.get("usage", {})
    model_name = data.get("model", MODEL)
    total_tokens = usage.get("total_tokens", 0)

    sep = "=" * 40
    print(sep)
    print("✅ Ответ от OpenAI:")
    print(sep)
    print(content)
    print(sep)
    print("ℹ️ Информация о запросе:")
    print(f"   Модель: {model_name}")
    print(f"   Использовано токенов: {total_tokens}")
    print(f"   Temperature: {temperature}")
    print(f"   Max tokens: {max_tokens}")
    print(sep)


if __name__ == "__main__":
    main()
