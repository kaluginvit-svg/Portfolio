"""
Учебный скрипт: заполняет CRM через REST API случайными, но правдоподобными данными.

Запуск (API должен быть доступен):
  python fill_test_data.py

Переменные окружения:
  CRM_API_URL — по умолчанию http://127.0.0.1:8000
  CRM_SEED_ROWS — строк на таблицу (по умолчанию 250; в уроке упоминается ~1000)
"""

from __future__ import annotations

import os
import random
import sys
import time
from datetime import date, timedelta

import httpx

BASE = os.environ.get("CRM_API_URL", "http://127.0.0.1:8000").rstrip("/")
ROWS = int(os.environ.get("CRM_SEED_ROWS", "250"))

LAST_NAMES = [
    "Иванов",
    "Петрова",
    "Сидорова",
    "Козлов",
    "Смирнов",
    "Волкова",
    "Новикова",
    "Морозов",
]

FIRST_NAMES = ["Алексей", "Мария", "Иван", "Ольга", "Дмитрий", "Елена", "Сергей", "Анна"]
COMPANIES = ["ТехноЛогистик", "СеверСтрой", "АльфаТрейд", "Омега IT", "Вектор-М", "Спектр+", "Компас"]

DEAL_STAGE = ["lead", "qualified", "proposal", "won", "lost"]
CLIENT_STATUS = ["active", "archived"]
TASK_PRIOR = ["low", "medium", "high"]


def main() -> int:
    rng = random.Random(42 + int(time.time()) % 1000)
    with httpx.Client(base_url=BASE, timeout=60.0) as c:
        r = c.get("/health")
        r.raise_for_status()
        client_ids: list[int] = []
        deal_ids: list[int] = []

        status_weights = CLIENT_STATUS + ["active"] * 3
        print(f"Creating {ROWS} clients…")
        for i in range(ROWS):
            st = rng.choice(status_weights)
            fn, ln = rng.choice(FIRST_NAMES), rng.choice(LAST_NAMES)
            payload = {
                "name": f"{fn} {ln} #{i + 1}",
                "email": f"crm-seed-{i + 1}-{rng.randint(10000, 99999)}@example.com",
                "phone": f"+79{rng.randint(10**8, 10**9 - 1)}",
                "company": rng.choice(COMPANIES),
                "status": st,
            }
            res = c.post("/clients", json=payload)
            if res.status_code != 201:
                print(res.text)
                res.raise_for_status()
            client_ids.append(res.json()["id"])

        print(f"Creating {ROWS} deals…")
        for i in range(ROWS):
            stage = rng.choice(DEAL_STAGE)
            attach = rng.random() > 0.15
            payload = {
                "title": f"Поставка / услуга {rng.randint(100, 999)} — {rng.choice(COMPANIES)}",
                "amount": round(rng.uniform(5_000, 2_500_000), 2),
                "currency": "RUB",
                "stage": stage,
                "client_id": rng.choice(client_ids) if attach else None,
            }
            res = c.post("/deals", json=payload)
            if res.status_code != 201:
                print(res.text)
                res.raise_for_status()
            deal_ids.append(res.json()["id"])

        print(f"Creating {ROWS} tasks…")
        for _ in range(ROWS):
            cid = rng.choice(client_ids) if rng.random() > 0.2 else None
            did = rng.choice(deal_ids) if cid and rng.random() > 0.4 else (rng.choice(deal_ids) if rng.random() > 0.7 else None)
            due_roll = rng.random()
            due = None
            if due_roll > 0.2:
                due = date.today() + timedelta(days=rng.randint(-14, 30))
            payload = {
                "title": rng.choice(
                    [
                        "Позвонить клиенту",
                        "Отправить КП",
                        "Согласовать договор",
                        "Напоминание оплата",
                        "Встреча уточнение ТЗ",
                    ]
                )
                + f" #{rng.randint(1, 9999)}",
                "description": "Авто-генерация fill_test_data.py",
                "due_date": due.isoformat() if due else None,
                "priority": rng.choice(TASK_PRIOR),
                "done": rng.random() < 0.25,
                "client_id": cid,
                "deal_id": did,
            }
            res = c.post("/tasks", json=payload)
            if res.status_code != 201:
                print(res.text)
                res.raise_for_status()

        print(f"Done. API={BASE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
