import argparse
import asyncio
import json
import os
from typing import List, Dict, Any

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
    "Сделай анализ канала и предложи рубрики. "
    "Опиши темы, тон, форматы, частотность рубрик, "
    "и дай 5 рекомендаций по улучшению."
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


def flatten_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        parts = []
        for item in value:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                text_part = item.get("text")
                if text_part is None:
                    continue
                parts.append(str(text_part))
            else:
                parts.append(str(item))
        return "".join(parts)
    if isinstance(value, dict):
        return str(value.get("text", ""))
    return str(value)


def find_json_path(input_path: str) -> str:
    if os.path.isdir(input_path):
        candidate = os.path.join(input_path, "result.json")
        if os.path.isfile(candidate):
            return candidate
    return input_path


def load_messages(json_path: str) -> Dict[str, Any]:
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict) and "messages" in data:
        return data
    raise ValueError("JSON не содержит ожидаемую структуру Telegram export.")


def truncate_text(value: str, limit: int) -> str:
    text = " ".join(str(value).split())
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 1)] + "…"


def format_message(message: Dict[str, Any]) -> str:
    msg_id = message.get("id")
    parts = [f"id={msg_id}"]
    if message.get("date"):
        parts.append(f"date={message['date']}")
    if message.get("type"):
        parts.append(f"type={message['type']}")
    text = truncate_text(flatten_text(message.get("text")), 280)
    return f"- {'; '.join(parts)} | {text}"


def build_prompt(
    json_path: str,
    channel_name: str,
    total: int,
    messages: List[Dict[str, Any]],
    question: str,
    max_chars: int,
) -> str:
    header = (
        "Ты аналитик Telegram-канала. Ниже сводка JSON и примеры сообщений.\n"
        "Сделай анализ на русском.\n\n"
    )
    summary = [
        f"Файл: {os.path.basename(json_path)}",
        f"Канал: {channel_name}",
        f"Сообщений в JSON: {total}",
        "",
        f"Запрос: {question}",
        "",
        "Примеры сообщений (последние):",
    ]
    prompt = header + "\n".join(summary)

    for message in messages:
        line = format_message(message)
        if len(prompt) + len(line) + 1 > max_chars:
            break
        prompt += "\n" + line

    return prompt


async def main() -> int:
    parser = argparse.ArgumentParser(
        description="Анализ и рубрикация Telegram JSON через OpenRouter."
    )
    parser.add_argument(
        "--json",
        default="result.json",
        help="Путь к файлу JSON или папке экспорта",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=80,
        help="Сколько сообщений отправлять",
    )
    parser.add_argument("--question", help="Вопрос/задача для анализа")
    parser.add_argument(
        "--max-chars",
        type=int,
        default=12000,
        help="Максимальная длина промпта",
    )
    args = parser.parse_args()

    json_path = find_json_path(args.json)
    if not os.path.isfile(json_path):
        print(f"❌ JSON файл не найден: {json_path}")
        return 1

    try:
        data = load_messages(json_path)
    except Exception as exc:
        print(f"❌ Ошибка чтения JSON: {exc}")
        return 1

    all_messages = data.get("messages") or []
    channel_name = data.get("name") or data.get("title") or "unknown"
    total = len(all_messages)
    sample = list(reversed(all_messages))[: args.limit]

    question = args.question or prompt_question()

    prompt = build_prompt(
        json_path=json_path,
        channel_name=channel_name,
        total=total,
        messages=sample,
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
