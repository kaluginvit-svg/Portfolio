#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт запрашивает выбор CSV-файла из папки со скриптом и подставляет его в ноутбук WB EDA.

Запуск:
  python set_csv_for_analysis.py              # интерактивный выбор из списка .csv
  python set_csv_for_analysis.py отчет.csv   # сразу подставить указанный файл

Скрипт и ноутбук должны лежать в одной папке; .csv файлы ищутся в этой же папке.
По умолчанию обновляется wb_weekly_report_eda.ipynb.
"""

import json
import re
import sys
from pathlib import Path

# Папка скрипта = корень проекта
SCRIPT_DIR = Path(__file__).resolve().parent
# Ноутбук с FILE_PATH и read_csv для отчёта WB
NOTEBOOK_NAME = "wb_weekly_report_eda.ipynb"
NOTEBOOK_PATH = SCRIPT_DIR / NOTEBOOK_NAME
# Файл с текущим путём к CSV — ноутбук читает его при запуске первой ячейки
CONFIG_CSV = "wb_current_csv.txt"


def list_csv_files() -> list[Path]:
    """Список .csv файлов в корне проекта."""
    return sorted(SCRIPT_DIR.glob("*.csv"), key=lambda p: p.name.lower())


def get_user_choice(files: list[Path], cli_arg: str | None = None) -> Path | None:
    """Запрос выбора файла у пользователя или из аргумента командной строки."""
    if cli_arg:
        p = (SCRIPT_DIR / cli_arg).resolve()
        if not p.exists():
            print(f"Файл не найден: {p}")
            return None
        return p

    if not files:
        print("В этой папке нет .csv файлов.")
        return None

    print("\nНайдены .csv файлы в папке:\n")
    for i, f in enumerate(files, 1):
        print(f"  {i}. {f.name}")
    print("  0. Ввести имя файла вручную")
    print()

    while True:
        try:
            raw = input("Выберите номер (или 0 для ввода имени): ").strip()
            n = int(raw)
            if n == 0:
                name = input("Введите имя файла (например report.csv): ").strip()
                if not name:
                    continue
                p = SCRIPT_DIR / name
                if not p.exists():
                    print(f"Файл не найден: {p}")
                    continue
                return p
            if 1 <= n <= len(files):
                return files[n - 1]
        except (ValueError, EOFError):
            pass
        print("Введите номер из списка или 0.")


def update_notebook_file_path(notebook_path: Path, new_file_path: str) -> bool:
    """
    Подставляет в ноутбук строку FILE_PATH = "new_file_path".
    Ищет ячейку с FILE_PATH и заменяет значение.
    """
    with open(notebook_path, "r", encoding="utf-8") as f:
        nb = json.load(f)

    file_name = Path(new_file_path).name
    pattern = re.compile(r'(FILE_PATH\s*=\s*")[^"]*(")')

    updated = False
    for cell in nb.get("cells", []):
        if cell.get("cell_type") != "code":
            continue
        source = cell.get("source", [])
        if not isinstance(source, list):
            source = [source]
        text = "".join(source)
        if "FILE_PATH" not in text or "read_csv" not in text:
            continue
        new_source = []
        for line in source:
            if pattern.search(line):
                line = pattern.sub(lambda m: m.group(1) + file_name + m.group(2), line)
                updated = True
            new_source.append(line)
        if updated:
            cell["source"] = new_source
            break

    if not updated:
        return False

    with open(notebook_path, "w", encoding="utf-8") as f:
        json.dump(nb, f, ensure_ascii=False, indent=1)

    return True


def main():
    cli_arg = sys.argv[1].strip() if len(sys.argv) > 1 else None

    if not NOTEBOOK_PATH.exists():
        print(f"Ноутбук не найден: {NOTEBOOK_PATH}")
        sys.exit(1)

    files = list_csv_files()
    chosen = get_user_choice(files, cli_arg)
    if chosen is None:
        sys.exit(0)

    # Записываем выбранный файл в конфиг — первая ячейка ноутбука читает путь оттуда
    config_path = SCRIPT_DIR / CONFIG_CSV
    config_path.write_text(chosen.name, encoding="utf-8")

    # Опционально обновляем и ноутбук на диске (для тех, кто перезагружает файл)
    if update_notebook_file_path(NOTEBOOK_PATH, chosen.name):
        print(f"\nГотово. Установлен файл: {chosen.name}")
    else:
        print(f"\nФайл записан в {CONFIG_CSV}. (Ячейка в ноутбуке не обновлена.)")

    print("Запустите первую ячейку в ноутбуке — путь подставится из конфига автоматически.")


if __name__ == "__main__":
    main()
