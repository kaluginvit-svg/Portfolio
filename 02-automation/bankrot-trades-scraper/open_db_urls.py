"""
Открытие всех ссылок (поле URL) из выбранной БД в браузере Chrome.

Запуск: python open_db_urls.py [--new-window]
"""
import argparse
import os
import sys
import sqlite3
import webbrowser
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def _get_chrome_browser():
    """Возвращает webbrowser-объект для Chrome или стандартный браузер, если Chrome не найден."""
    chrome_paths = []
    if sys.platform == "win32":
        chrome_paths = [
            os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe"),
        ]
    elif sys.platform == "darwin":
        chrome_paths = ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"]
    else:
        chrome_paths = ["/usr/bin/google-chrome", "/usr/bin/google-chrome-stable", "/usr/bin/chromium"]
    for p in chrome_paths:
        if p and os.path.isfile(p):
            webbrowser.register("chrome", None, webbrowser.BackgroundBrowser(p))
            return webbrowser.get("chrome")
    return webbrowser.get()


def _get_url_column(cursor) -> str | None:
    """Возвращает имя колонки с URL в таблице announcements."""
    cursor.execute("PRAGMA table_info(announcements)")
    for row in cursor.fetchall():
        name = (row[1] or "").strip()
        if name.lower() == "url":
            return name
    return None


def _get_urls_from_db(path: Path) -> list[str]:
    """Извлекает уникальные непустые URL из таблицы announcements."""
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    url_col = _get_url_column(cur)
    if not url_col:
        conn.close()
        return []
    cur.execute(f'SELECT DISTINCT "{url_col}" FROM announcements')
    seen = set()
    urls = []
    for row in cur.fetchall():
        if not row[0]:
            continue
        u = str(row[0]).strip()
        if u and (u.startswith("http://") or u.startswith("https://")) and u not in seen:
            seen.add(u)
            urls.append(u)
    conn.close()
    return urls


def main(new_window: bool = False) -> None:
    db_files = sorted(BASE_DIR.glob("*.db"))
    db_files = [f for f in db_files if f.is_file()]
    if not db_files:
        print("В каталоге нет файлов .db")
        return

    print("Файлы .db в каталоге:")
    for i, f in enumerate(db_files, 1):
        print(f"  {i} — {f.name}")

    try:
        raw = input("\nВведите номер файла: ").strip()
    except EOFError:
        return
    if not raw:
        print("Не введён номер.")
        return
    try:
        n = int(raw)
    except ValueError:
        print("Введите число.")
        return
    if n < 1 or n > len(db_files):
        print("Нет такого номера.")
        return

    path = db_files[n - 1]
    urls = _get_urls_from_db(path)
    if not urls:
        print(f"В {path.name} нет записей с URL.")
        return

    browser = _get_chrome_browser()
    # new=1 — новое окно, new=0 — та же вкладка
    open_new = 1 if new_window else 0
    print(f"Открываю {len(urls)} ссылок из {path.name} в Chrome{' (новое окно)' if new_window else ''}...")
    for i, url in enumerate(urls, 1):
        browser.open(url, new=open_new)
        if i < len(urls):
            time.sleep(0.4)
    print("Готово.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Открытие URL из .db в Chrome")
    parser.add_argument("-n", "--new-window", action="store_true", help="Открывать каждую ссылку в новом окне")
    args = parser.parse_args()
    main(new_window=args.new_window)
