"""
Проверка доступных моделей ProxyAPI.
Запуск: python check_proxyapi_models.py
Показывает, какой base URL и ключ работают и какие модели доступны.
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("В .env не задан OPENAI_API_KEY")
    exit(1)

bases = [
    ("Универсальный API", "https://openai.api.proxyapi.ru"),
    ("Прямой OpenAI API", "https://api.proxyapi.ru/openai"),
]

for name, base in bases:
    url = f"{base.rstrip('/')}/v1/models"
    print(f"\n--- {name}: GET {url} ---")
    try:
        r = requests.get(url, headers={"Authorization": f"Bearer {api_key}"}, timeout=15)
        print(f"Статус: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            models = data.get("data", [])
            ids = [m.get("id") for m in models[:20] if m.get("id")]
            print(f"Модели (первые 20): {ids}")
            if len(models) > 20:
                print(f"Всего: {len(models)}")
        else:
            print(r.text[:500])
    except Exception as e:
        print(f"Ошибка: {e}")

# Проверка chat/completions (какой endpoint реально принимает запросы)
print("\n--- Проверка POST /v1/chat/completions ---")
for name, base in bases:
    url = f"{base.rstrip('/')}/v1/chat/completions"
    print(f"\n{name}: {url}")
    try:
        r = requests.post(
            url,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": "openai/gpt-4o-mini" if "openai.api." in base else "gpt-3.5-turbo",
                "messages": [{"role": "user", "content": "Скажи ок"}],
                "max_tokens": 10,
            },
            timeout=30,
        )
        print(f"  Статус: {r.status_code}")
        if r.status_code == 200:
            text = r.json().get("choices", [{}])[0].get("message", {}).get("content", "")
            print(f"  Ответ: {text[:80]}")
        else:
            print(f"  Тело: {r.text[:200]}")
    except Exception as e:
        print(f"  Ошибка: {e}")
