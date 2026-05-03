# -*- coding: utf-8 -*-
"""
Скрипт: Отрисовка BPMN процесса «Возврат / претензия» (Retail / Интернет‑магазин)
и экспорт на доску Miro.

Пул: Retail / Интернет‑магазин.
Циклы: корректировка заявки (Шлюз 1), переговоры по решению (Шлюз 3), повтор платежа (Шлюз 5).

Использование:
  1. Токен: .env с MIRO_ACCESS_TOKEN=... или переменная окружения.
  2. Запуск: python service_desk_to_miro.py
  3. Опционально: в .env задать MIRO_BOARD_URL=... или ввести URL доски при запросе.

Требования: pip install requests
"""

import os
import re
import sys

# Загрузка переменных из .env (если файл есть) — чтобы подставить MIRO_ACCESS_TOKEN
def _load_dotenv(path=".env"):
    if not os.path.isfile(path):
        return
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value

_load_dotenv()

try:
    import requests
except ImportError:
    print("Установите requests: pip install requests")
    sys.exit(1)

# Базовый URL Miro REST API v2
MIRO_API_BASE = "https://api.miro.com/v2"

# Шаг сетки для размещения элементов (в пикселях)
STEP_X = 360
STEP_Y = 200

# Размеры элементов (ширина x высота)
TASK_WIDTH = 200
TASK_HEIGHT = 80
GATEWAY_SIZE = 100
EVENT_SIZE = 60
STICKY_WIDTH = 220
STICKY_HEIGHT = 160


def get_board_id_from_url(url):
    """
    Извлекает ID доски из ссылки Miro.
    Поддерживает форматы:
      https://miro.com/app/board/xxxxxxxxxx=/
      https://miro.com/app/board/uXjVKxxxxxxxxx=/
    """
    if not url or not isinstance(url, str):
        return None
    url = url.strip()
    # Паттерн: /app/board/ {id} / или конец строки. ID может содержать буквы, цифры, подчёркивание, =.
    match = re.search(r"miro\.com/app/board/([a-zA-Z0-9_=-]+)", url)
    if match:
        return match.group(1).rstrip("/")
    return None


def resolve_board_id():
    """
    Возвращает ID доски из переменных окружения.
    MIRO_BOARD_ID — либо готовый id, либо URL (тогда id извлекается из ссылки).
    MIRO_BOARD_URL — ссылка на доску, из неё берётся id.
    """
    raw_id = os.environ.get("MIRO_BOARD_ID")
    if raw_id:
        raw_id = raw_id.strip()
        if "miro.com" in raw_id:
            return get_board_id_from_url(raw_id)
        return raw_id
    url = os.environ.get("MIRO_BOARD_URL")
    if url:
        return get_board_id_from_url(url)
    return None


def get_headers():
    token = os.environ.get("MIRO_ACCESS_TOKEN")
    if not token:
        if sys.stdin.isatty():
            try:
                token = input("Введите MIRO_ACCESS_TOKEN (OAuth access token, scope: boards:write, boards:read): ").strip()
            except (EOFError, KeyboardInterrupt):
                token = ""
        if not token:
            print("Задайте переменную окружения MIRO_ACCESS_TOKEN или введите токен в терминале.")
            sys.exit(1)
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def create_board(headers):
    """Создаёт новую доску Miro."""
    url = f"{MIRO_API_BASE}/boards"
    payload = {
        "name": "BPMN: Возврат / претензия (Retail)",
        "policy": {
            "sharingPolicy": {
                "access": "private",
                "teamAccess": "private",
                "organizationAccess": "private",
                "inviteToAccountAndBoardLinkAccess": "no_access",
            },
            "permissionsPolicy": {
                "collaborationToolsStartAccess": "all_editors",
                "copyAccess": "anyone",
                "sharingAccess": "team_members_with_editing_rights",
            },
        },
    }
    r = requests.post(url, json=payload, headers=headers, timeout=30)
    if r.status_code == 403:
        print("Ошибка 403 Forbidden при создании доски.")
        print("Ответ Miro:", r.text)
        print("\nВозможные причины:")
        print("  — На бесплатном тарифе Miro можно создать не более 3 досок в команде.")
        print("  — У токена нет прав на создание досок (нужен scope boards:write при авторизации).")
        print("  — Используйте существующую доску: при запросе URL вставьте ссылку на доску вместо Enter.")
        r.raise_for_status()
    r.raise_for_status()
    data = r.json()
    # viewLink может быть в data["viewLink"] или в data["links"]["view"]
    view = data.get("viewLink") or (data.get("links") or {}).get("view") or ""
    return data["id"], view


def create_shape(headers, board_id, shape_type, content, x, y, width=None, height=None, fill_color="#E6E6E6"):
    """Создаёт фигуру на доске. shape_type: rectangle, circle, rhombus и т.д."""
    url = f"{MIRO_API_BASE}/boards/{board_id}/shapes"
    w = width or (GATEWAY_SIZE if shape_type == "rhombus" else TASK_WIDTH)
    h = height or (GATEWAY_SIZE if shape_type == "rhombus" else TASK_HEIGHT)
    if shape_type == "circle":
        w = h = EVENT_SIZE
    payload = {
        "data": {"shape": shape_type, "content": content},
        "position": {"origin": "center", "x": x, "y": y},
        "geometry": {"width": w, "height": h},
        "style": {"fillColor": fill_color},
    }
    r = requests.post(url, json=payload, headers=headers, timeout=30)
    r.raise_for_status()
    return r.json()["id"]


def create_sticky_note(headers, board_id, content, x, y, fill_color="light_yellow"):
    """Создаёт стикер на доске."""
    url = f"{MIRO_API_BASE}/boards/{board_id}/sticky_notes"
    payload = {
        "data": {"content": content, "shape": "rectangle"},
        "position": {"origin": "center", "x": x, "y": y},
        "style": {"fillColor": fill_color},
    }
    r = requests.post(url, json=payload, headers=headers, timeout=30)
    r.raise_for_status()
    return r.json()["id"]


def create_connector(headers, board_id, start_id, end_id, caption=None):
    """Создаёт соединитель между двумя элементами."""
    url = f"{MIRO_API_BASE}/boards/{board_id}/connectors"
    # Miro REST API v2: startItem/endItem обязательны (ошибка 2.0703)
    payload = {
        "startItem": {"id": start_id, "snapTo": "auto"},
        "endItem": {"id": end_id, "snapTo": "auto"},
        "shape": "elbowed",
        "style": {"strokeColor": "#1a1a1a", "endStrokeCap": "arrow"},
    }
    if caption:
        # position — в процентах (0–100), тип Percentage в API
        payload["captions"] = [{"content": caption, "position": "50%"}]
    r = requests.post(url, json=payload, headers=headers, timeout=30)
    if not r.ok:
        print("Connector error:", r.status_code, r.text)
    r.raise_for_status()
    return r.json()["id"]


def create_text(headers, board_id, content, x, y):
    """Создаёт текстовый блок (для подписей пулов/веток)."""
    url = f"{MIRO_API_BASE}/boards/{board_id}/texts"
    payload = {
        "data": {"content": content},
        "position": {"origin": "center", "x": x, "y": y},
        "style": {"fontSize": "14"},
    }
    r = requests.post(url, json=payload, headers=headers, timeout=30)
    r.raise_for_status()
    return r.json()["id"]


def draw_process(headers, board_id):
    """Размещает BPMN процесса «Возврат / претензия» (Retail) на доске."""

    ids = {}
    ox, oy = 0, 0

    # --- Пул Retail / Интернет‑магазин ---
    # Start: Получена заявка на возврат / претензию
    ids["start"] = create_shape(
        headers, board_id, "circle",
        "Получена заявка\nна возврат / претензию",
        ox, oy, EVENT_SIZE, EVENT_SIZE, "#B5EAD7",
    )
    # Задача 1: Регистрация заявки
    ids["t1"] = create_shape(
        headers, board_id, "rectangle",
        "Зарегистрировать заявку\nна возврат",
        ox, oy + STEP_Y, TASK_WIDTH, TASK_HEIGHT, "#C7CEEA",
    )
    # Задача 2: Проверка корректности заявки
    ids["t2"] = create_shape(
        headers, board_id, "rectangle",
        "Проверить полноту и корректность\nданных заявки",
        ox, oy + 2 * STEP_Y, TASK_WIDTH, TASK_HEIGHT, "#FFDAC1",
    )
    # Шлюз 1: Данные корректны? (цикл по ошибкам ввода)
    ids["gw1"] = create_shape(
        headers, board_id, "rhombus",
        "Данные\nкорректны?",
        ox, oy + 3 * STEP_Y, GATEWAY_SIZE, GATEWAY_SIZE, "#E2F0CB",
    )
    ids["request_clarify"] = create_shape(
        headers, board_id, "rectangle",
        "Запросить уточнение\nу клиента",
        ox + STEP_X, oy + 3 * STEP_Y, TASK_WIDTH, TASK_HEIGHT, "#FFDAC1",
    )
    # Задача 3: Проверка статуса товара и условий возврата
    ids["t3"] = create_shape(
        headers, board_id, "rectangle",
        "Проверить статус товара,\nсрок и условия возврата",
        ox, oy + 4 * STEP_Y, TASK_WIDTH, TASK_HEIGHT, "#FFDAC1",
    )
    # Шлюз 2: Возврат допустим?
    ids["gw2"] = create_shape(
        headers, board_id, "rhombus",
        "Возврат\nдопустим?",
        ox, oy + 5 * STEP_Y, GATEWAY_SIZE, GATEWAY_SIZE, "#E2F0CB",
    )
    ids["send_refusal"] = create_shape(
        headers, board_id, "rectangle",
        "Сформировать и отправить\nмотивированный отказ",
        ox + STEP_X, oy + 5 * STEP_Y, TASK_WIDTH, TASK_HEIGHT, "#FF9AA2",
    )
    ids["end_rejected"] = create_shape(
        headers, board_id, "circle",
        "Возврат отклонен\n(по условиям)",
        ox + STEP_X, oy + 5 * STEP_Y + 120, EVENT_SIZE, EVENT_SIZE, "#FF9AA2",
    )
    # Задача 4: Согласование решения
    ids["t4"] = create_shape(
        headers, board_id, "rectangle",
        "Согласовать решение по претензии\n(эксперт/финансы)",
        ox, oy + 6 * STEP_Y, TASK_WIDTH, TASK_HEIGHT, "#FFDAC1",
    )
    # Задача 5: Отправить предложение клиенту
    ids["t5"] = create_shape(
        headers, board_id, "rectangle",
        "Отправить клиенту предложение\nпо возврату / обмену",
        ox, oy + 7 * STEP_Y, TASK_WIDTH, TASK_HEIGHT, "#FFDAC1",
    )
    # Шлюз 3: Клиент согласен? (цикл переговоров)
    ids["gw3"] = create_shape(
        headers, board_id, "rhombus",
        "Клиент\nсогласен?",
        ox, oy + 8 * STEP_Y, GATEWAY_SIZE, GATEWAY_SIZE, "#E2F0CB",
    )
    ids["clarify_conditions"] = create_shape(
        headers, board_id, "rectangle",
        "Уточнить условия /\nпредложить альтернативу",
        ox + STEP_X, oy + 8 * STEP_Y, TASK_WIDTH, TASK_HEIGHT, "#FFDAC1",
    )
    # Задача 6: Прием товара
    ids["t6"] = create_shape(
        headers, board_id, "rectangle",
        "Принять товар от клиента\n/ на складе",
        ox, oy + 9 * STEP_Y, TASK_WIDTH, TASK_HEIGHT, "#FFDAC1",
    )
    # Задача 7: Проверка состояния товара
    ids["t7"] = create_shape(
        headers, board_id, "rectangle",
        "Проверить состояние и соответствие\nтовара заявке",
        ox, oy + 10 * STEP_Y, TASK_WIDTH, TASK_HEIGHT, "#FFDAC1",
    )
    # Шлюз 4: Товар соответствует?
    ids["gw4"] = create_shape(
        headers, board_id, "rhombus",
        "Товар\nсоответствует?",
        ox, oy + 11 * STEP_Y, GATEWAY_SIZE, GATEWAY_SIZE, "#E2F0CB",
    )
    ids["notify_mismatch"] = create_shape(
        headers, board_id, "rectangle",
        "Сообщить о несоответствии и\nсогласовать действия",
        ox + STEP_X, oy + 11 * STEP_Y, TASK_WIDTH, TASK_HEIGHT, "#FF9AA2",
    )
    # Задача 8: Возврат средств
    ids["t8"] = create_shape(
        headers, board_id, "rectangle",
        "Инициировать возврат средств\n/ оформление обмена",
        ox, oy + 12 * STEP_Y, TASK_WIDTH, TASK_HEIGHT, "#C7CEEA",
    )
    # Шлюз 5: Платеж успешен? (цикл при ошибке)
    ids["gw5"] = create_shape(
        headers, board_id, "rhombus",
        "Платеж\nуспешен?",
        ox, oy + 13 * STEP_Y, GATEWAY_SIZE, GATEWAY_SIZE, "#E2F0CB",
    )
    ids["request_payment_retry"] = create_shape(
        headers, board_id, "rectangle",
        "Запросить реквизиты /\nповторить оплату",
        ox + STEP_X, oy + 13 * STEP_Y, TASK_WIDTH, TASK_HEIGHT, "#FFDAC1",
    )
    # Задача 9: Закрытие претензии
    ids["t9"] = create_shape(
        headers, board_id, "rectangle",
        "Закрыть претензию и обновить\nстатусы / отчеты",
        ox, oy + 14 * STEP_Y, TASK_WIDTH, TASK_HEIGHT, "#C7CEEA",
    )
    # End: Претензия обработана
    ids["end_ok"] = create_shape(
        headers, board_id, "circle",
        "Претензия обработана,\nвозврат завершен",
        ox, oy + 15 * STEP_Y, EVENT_SIZE, EVENT_SIZE, "#B5EAD7",
    )

    # --- Соединители ---
    def connect(a, b, caption=None):
        create_connector(headers, board_id, ids[a], ids[b], caption)

    connect("start", "t1")
    connect("t1", "t2")
    connect("t2", "gw1")
    connect("gw1", "t3", "Да")
    connect("gw1", "request_clarify", "Нет")
    create_connector(headers, board_id, ids["request_clarify"], ids["t2"])  # цикл: обратно к проверке данных
    connect("t3", "gw2")
    connect("gw2", "t4", "Да")
    connect("gw2", "send_refusal", "Нет")
    connect("send_refusal", "end_rejected")
    connect("t4", "t5")
    connect("t5", "gw3")
    connect("gw3", "t6", "Да")
    connect("gw3", "clarify_conditions", "Нет")
    create_connector(headers, board_id, ids["clarify_conditions"], ids["t4"])  # цикл: обратно к согласованию
    connect("t6", "t7")
    connect("t7", "gw4")
    connect("gw4", "t8", "Да")
    connect("gw4", "notify_mismatch", "Нет")
    create_connector(headers, board_id, ids["notify_mismatch"], ids["t7"])  # цикл: перепроверка товара
    connect("t8", "gw5")
    connect("gw5", "t9", "Да")
    connect("gw5", "request_payment_retry", "Нет")
    create_connector(headers, board_id, ids["request_payment_retry"], ids["t8"])  # цикл: повтор платежа
    connect("t9", "end_ok")

    return ids


def export_board(headers, board_id, format_type="pdf"):
    """
    Запускает экспорт доски (png/pdf). Экспорт асинхронный — возвращает job_id.
    Результат можно забрать по API экспорта (Enterprise) или открыть доску по viewLink и экспортировать вручную.
    """
    # Стандартный REST API v2 позволяет получить viewLink доски для открытия в браузере.
    url = f"{MIRO_API_BASE}/boards/{board_id}"
    r = requests.get(url, headers=headers, timeout=30)
    r.raise_for_status()
    data = r.json()
    return data.get("viewLink", ""), data.get("name", "")


def main():
    headers = get_headers()
    board_id = None

    # В терминале всегда запрашиваем URL доски
    if sys.stdin.isatty():
        prompt = "Введите URL доски Miro (или Enter — создать новую доску): "
        try:
            url_input = input(prompt).strip()
        except (EOFError, KeyboardInterrupt):
            url_input = ""
        if url_input:
            board_id = get_board_id_from_url(url_input)
            if not board_id:
                print("Не удалось извлечь ID из ссылки. Будет создана новая доска.")
                board_id = None
    else:
        # Не в терминале (pipe/CI) — берём из переменных окружения
        board_id = resolve_board_id()

    if board_id:
        print(f"Используется существующая доска (ID: {board_id})")
        view_link, name = export_board(headers, board_id)
    else:
        board_id, view_link = create_board(headers)
        name = "BPMN: Возврат / претензия (Retail)"
        print(f"Создана доска: {name} (ID: {board_id})")

    print("Размещение элементов процесса на доске...")
    draw_process(headers, board_id)

    if not view_link:
        view_link, _ = export_board(headers, board_id)
    if view_link:
        print(f"\nОткройте доску в Miro: {view_link}")
    print("\nГотово. Диаграмма процесса построена на доске Miro.")


if __name__ == "__main__":
    main()
