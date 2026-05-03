import argparse
import asyncio
import glob
import os
import sqlite3
from typing import List, Tuple

try:
    from app.services import call_openrouter_api
except ModuleNotFoundError as exc:
    missing = getattr(exc, "name", "")
    if missing == "aiohttp":
        print("❌ Не установлены зависимости. Установите их командой:")
        print("pip install -r requirements.txt")
        raise SystemExit(1) from exc
    raise


DEFAULT_QUESTION = (
    "Сделай краткий анализ канала по базе сообщений: "
    "темы, тон, частые форматы, что привлекает внимание, "
    "и 5 рекомендаций, что улучшить."
)


def prompt_question() -> str:
    try:
        print("Введите промпт для анализа. Пустая строка завершает ввод.")
        lines = []
        while True:
            line = input()
            if line == "":
                break
            lines.append(line)
        question = "\n".join(lines).strip()
    except EOFError:
        question = ""
    return question or DEFAULT_QUESTION


def find_db_files() -> List[str]:
    return sorted([f for f in os.listdir('.') if f.endswith('.db')])


def prompt_db_selection(files: List[str]) -> str:
    print("Найдены базы данных:")
    for i, f in enumerate(files, 1):
        print(f"{i}. {f}")
    
    while True:
        try:
            choice = input("Выберите номер (Enter - первая): ").strip()
            if not choice:
                return files[0]
            idx = int(choice) - 1
            if 0 <= idx < len(files):
                return files[idx]
            print("Неверный номер.")
        except ValueError:
            print("Введите число.")


def get_db_path(arg_db: str = None) -> str:
    if arg_db:
        return arg_db
    
    files = find_db_files()
    if not files:
        return ""
    
    if len(files) == 1:
        print(f"Используется единственная база: {files[0]}")
        return files[0]
        
    return prompt_db_selection(files)


def get_columns(conn: sqlite3.Connection) -> List[str]:
    return [row[1] for row in conn.execute("PRAGMA table_info(posts)").fetchall()]


def fetch_summary(conn: sqlite3.Connection, columns: List[str]) -> Tuple[int, str]:
    total = conn.execute("SELECT COUNT(*) FROM posts").fetchone()[0]
    channel = conn.execute(
        "SELECT channel_name FROM posts WHERE channel_name IS NOT NULL LIMIT 1"
    ).fetchone()
    channel_name = channel[0] if channel and channel[0] else "unknown"
    return total, channel_name


def build_sample_query(columns: List[str]) -> str:
    fields = ["message_id", "channel_name", "text_flat"]
    if "date" in columns:
        fields.append("date")
    if "tag" in columns:
        fields.append("tag")
    field_list = ", ".join(fields)
    return f"SELECT {field_list} FROM posts ORDER BY message_id DESC LIMIT ?"


def truncate_text(value: str, limit: int) -> str:
    if value is None:
        return ""
    text = " ".join(str(value).split())
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 1)] + "…"


def format_row(row: sqlite3.Row, columns: List[str]) -> str:
    parts = [f"id={row['message_id']}"]
    if "date" in row.keys() and row["date"]:
        parts.append(f"date={row['date']}")
    if "tag" in row.keys() and row["tag"]:
        parts.append(f"tag={row['tag']}")
    text_value = row["text_flat"] if "text_flat" in row.keys() else ""
    text = truncate_text(text_value, 280)
    return f"- {'; '.join(parts)} | {text}"


def build_prompt(
    db_path: str,
    columns: List[str],
    total: int,
    channel_name: str,
    rows: List[sqlite3.Row],
    question: str,
    max_chars: int,
) -> str:
    header = (
        "Ты аналитик Telegram-канала. Ниже сводка БД и примеры сообщений.\n"
        "Сделай анализ на русском.\n\n"
    )
    summary = [
        f"База: {os.path.basename(db_path)}",
        f"Канал: {channel_name}",
        f"Сообщений в базе: {total}",
        f"Колонки: {', '.join(columns)}",
        "",
        f"Запрос: {question}",
        "",
        "Примеры сообщений (последние):",
    ]
    prompt = header + "\n".join(summary)

    for row in rows:
        line = format_row(row, columns)
        if len(prompt) + len(line) + 1 > max_chars:
            break
        prompt += "\n" + line

    return prompt


async def main() -> int:
    parser = argparse.ArgumentParser(
        description="Отправка выборки из SQLite БД на анализ OpenRouter."
    )
    parser.add_argument("--db", default=None, help="Путь к SQLite БД")
    parser.add_argument("--limit", type=int, default=60, help="Сколько сообщений отправлять")
    parser.add_argument("--question", help="Вопрос/задача для анализа")
    parser.add_argument(
        "--max-chars",
        type=int,
        default=12000,
        help="Максимальная длина промпта",
    )
    args = parser.parse_args()

    db_path = get_db_path(args.db)
    if not db_path:
        print("❌ Не найден файл БД. Укажите --db путь_к_файлу.db")
        return 1
    if not os.path.isfile(db_path):
        print(f"❌ Файл БД не найден: {db_path}")
        return 1

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        columns = get_columns(conn)
        if not columns:
            print("❌ Таблица posts не найдена или пустая.")
            return 1
        total, channel_name = fetch_summary(conn, columns)
        query = build_sample_query(columns)
        rows = conn.execute(query, (args.limit,)).fetchall()
    finally:
        conn.close()

    question = args.question or prompt_question()

    prompt = build_prompt(
        db_path=db_path,
        columns=columns,
        total=total,
        channel_name=channel_name,
        rows=rows,
        question=question,
        max_chars=args.max_chars,
    )

    if len(prompt) > args.max_chars:
        print("❌ Промпт слишком длинный. Уменьшите --limit или --max-chars.")
        return 1

    print("📤 Отправляю запрос в OpenRouter...")
    response = await call_openrouter_api(prompt)
    if not response:
        print("❌ Не удалось получить ответ от OpenRouter.")
        return 1

    print("✅ Ответ OpenRouter:")
    print(response)
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
