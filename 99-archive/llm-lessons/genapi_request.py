#!/usr/bin/env python3
"""
Скрипт: тот же функционал, но через GenAPI (https://gen-api.ru/).
Параметры из терминала; API-ключ из .env.
Использует HTTP-запросы (requests).
После создания запроса опрашивает результат до готовности.
"""

import argparse
import os
import sys
import time

import requests
from dotenv import load_dotenv

load_dotenv()

GENAPI_BASE = "https://api.gen-api.ru/api/v1"
# Идентификатор модели для текстовой генерации (GPT-3.5-совместимая на платформе GenAPI)
DEFAULT_NETWORK_ID = "gpt-3.5-turbo"


def main():
    parser = argparse.ArgumentParser(description="Запрос к GenAPI")
    parser.add_argument("--prompt", "-p", required=True, help="Текст запроса для модели")
    parser.add_argument("--temperature", "-t", type=float, default=0.7, help="Температура (0–2)")
    parser.add_argument("--max_tokens", "-m", type=int, default=1000, help="Максимум токенов в ответе")
    parser.add_argument("--system", "-s", default=None, help="System message (опционально)")
    parser.add_argument("--model", "-M", default=DEFAULT_NETWORK_ID, help=f"ID модели (network_id), по умолчанию: {DEFAULT_NETWORK_ID}")
    args = parser.parse_args()

    api_key = os.getenv("GENAPI_API_KEY")
    if not api_key:
        print("Ошибка: задайте GENAPI_API_KEY в файле .env", file=sys.stderr)
        sys.exit(1)

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    # Тело запроса: prompt и опциональные параметры (формат может отличаться для разных моделей)
    body = {
        "prompt": args.prompt,
        "temperature": args.temperature,
        "max_tokens": args.max_tokens,
        "is_sync": True,
    }
    if args.system:
        body["system"] = args.system

    url = f"{GENAPI_BASE}/networks/{args.model}"
    resp = requests.post(url, json=body, headers=headers, timeout=120)

    if not resp.ok:
        print(f"Ошибка API: {resp.status_code}\n{resp.text}", file=sys.stderr)
        sys.exit(1)

    data = resp.json()
    status = data.get("status", "")

    if status == "success":
        result = data.get("result")
        if isinstance(result, list) and result:
            print(result[0] if isinstance(result[0], str) else str(result[0]))
        elif isinstance(result, str):
            print(result)
        else:
            print(data.get("full_response", result))
        return

    if status == "error":
        print("Ошибка генерации:", data.get("error", data), file=sys.stderr)
        sys.exit(1)

    # Асинхронный ответ — опрашиваем результат по request_id
    request_id = data.get("request_id") or data.get("id")
    if request_id is None:
        print("Ошибка: в ответе нет request_id/id и статус не success", file=sys.stderr)
        print(data, file=sys.stderr)
        sys.exit(1)

    get_url = f"{GENAPI_BASE}/request/get/{request_id}"
    for _ in range(120):
        time.sleep(1)
        r = requests.get(get_url, headers=headers, timeout=30)
        if not r.ok:
            print(f"Ошибка при получении результата: {r.status_code}\n{r.text}", file=sys.stderr)
            sys.exit(1)
        data = r.json()
        status = data.get("status", "")
        if status == "success":
            result = data.get("result")
            if isinstance(result, list) and result:
                print(result[0] if isinstance(result[0], str) else str(result[0]))
            elif isinstance(result, str):
                print(result)
            else:
                print(data.get("full_response", result))
            return
        if status == "error":
            print("Ошибка генерации:", data.get("error", data), file=sys.stderr)
            sys.exit(1)

    print("Таймаут ожидания результата", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()
