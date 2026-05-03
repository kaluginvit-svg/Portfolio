#!/usr/bin/env python3
"""
Пример отправки логов в Loki через HTTP API.
Запуск: python main.py — в цикле раз в ~15 сек отправляет случайный лог в Loki (Ctrl+C — выход).
Переменная LOKI_URL (по умолчанию http://155.212.174.153:3100) — адрес Loki.
"""
import os
import random
import sys
import time

try:
    import requests
except ImportError:
    print("Установите requests: pip install requests", file=sys.stderr)
    sys.exit(1)

LOKI_URL = os.environ.get("LOKI_URL", "http://155.212.174.153:3100")
PUSH_PATH = "/loki/api/v1/push"


def send_log(message: str, level: str = "info", app: str = "main.py") -> bool:
    """Отправить одну строку лога в Loki."""
    # Наносекунды, как требует Loki
    ns = str(int(time.time() * 1e9))
    payload = {
        "streams": [
            {
                "stream": {
                    "job": "python-script",
                    "level": level,
                    "app": app,
                },
                "values": [[ns, message]],
            }
        ]
    }
    url = f"{LOKI_URL.rstrip('/')}{PUSH_PATH}"
    try:
        r = requests.post(
            url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10,
        )
        r.raise_for_status()
        return True
    except requests.RequestException as e:
        print(f"Ошибка отправки в Loki: {e}", file=sys.stderr)
        if hasattr(e, "response") and e.response is not None:
            print(f"Ответ: {e.response.text[:500]}", file=sys.stderr)
        return False


def send_log_to_loki(message: str, category: str, level: str) -> bool:
    """Отправить лог в Loki с указанием категории и уровня."""
    return send_log(message, level=level.lower(), app=category)


# Варианты логов для случайной отправки: (сообщение, категория, уровень)
LOG_SAMPLES = [
    ("Приложение запущено", "app", "INFO"),
    ("Пользователь авторизован", "auth", "INFO"),
    ("Ошибка валидации данных", "validation", "ERROR"),
    ("Запрос к API выполнен", "api", "DEBUG"),
    ("Критическая ошибка системы", "system", "CRITICAL"),
    ("Сессия истекла", "auth", "WARNING"),
    ("Загрузка конфигурации", "app", "INFO"),
    ("Таймаут соединения с БД", "system", "ERROR"),
    ("Отправка метрик", "api", "DEBUG"),
    ("Неверный пароль", "auth", "WARNING"),
    ("Кэш очищен", "app", "INFO"),
    ("Сервис недоступен", "system", "CRITICAL"),
]


def main():
    print("Отправка логов в Loki (раз в ~15 сек). Остановка: Ctrl+C")
    print("Grafana: http://155.212.174.153:3000 (admin / admin)\n")

    while True:
        message, category, level = random.choice(LOG_SAMPLES)
        if send_log_to_loki(message, category, level):
            print(f"  [{level}] [{category}] {message}")
        else:
            print("  Ошибка отправки, повтор через 15 сек...")
        delay = random.uniform(12, 18)
        time.sleep(delay)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nОстановлено.")
        sys.exit(0)