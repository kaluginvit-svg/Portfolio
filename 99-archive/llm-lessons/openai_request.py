#!/usr/bin/env python3
"""
Скрипт: обычный запрос к OpenAI.
Запуск из терминала. Параметры: запрос, температура, max_tokens, system_message (опционально).
Модель: gpt-3.5-turbo.
Ключ: OPENAI_API_KEY в .env или в переменных окружения.
"""

import argparse

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


def main():
    parser = argparse.ArgumentParser(description="Запрос к OpenAI gpt-3.5-turbo")
    parser.add_argument("--prompt", "-p", required=True, help="Текст запроса для модели")
    parser.add_argument("--temperature", "-t", type=float, default=0.7, help="Температура (0–2)")
    parser.add_argument("--max_tokens", "-m", type=int, default=1000, help="Максимум токенов в ответе")
    parser.add_argument("--system", "-s", default=None, help="System message (опционально)")
    args = parser.parse_args()

    client = OpenAI()

    messages = []
    if args.system:
        messages.append({"role": "system", "content": args.system})
    messages.append({"role": "user", "content": args.prompt})

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
    )

    content = response.choices[0].message.content
    print(content)


if __name__ == "__main__":
    main()
