#!/usr/bin/env python3
"""
prompt_chat — выбор промпта из JSON-файлов и запрос к API с выбором модели и температуры.
"""

import json
import os
import sys
from pathlib import Path

# Загрузка переменных из .env
def load_dotenv():
    env_path = Path(__file__).resolve().parent / ".env"
    if not env_path.exists():
        return
    with open(env_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                os.environ[key.strip()] = value.strip().strip('"').strip("'")


def find_prompt_files(root: Path) -> list[Path]:
    """Ищет все JSON-файлы в корневой папке."""
    return sorted(root.glob("*.json"))


def load_prompt(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def build_system_message(data: dict) -> str:
    """Собирает системное сообщение из полей промпта."""
    parts = []
    if data.get("role"):
        parts.append(data["role"])
    if data.get("context"):
        parts.append("\n\nКонтекст:\n" + data["context"])
    if data.get("structure"):
        s = data["structure"]
        if isinstance(s, dict):
            fmt = s.get("output_format", "")
            comps = s.get("components", [])
            if fmt or comps:
                parts.append("\n\nСтруктура вывода: " + fmt)
                for c in comps:
                    if isinstance(c, dict):
                        parts.append(f"\n- {c.get('name', '')}: {c.get('description', '')}")
        else:
            parts.append("\n\nСтруктура: " + str(s))
    if data.get("format"):
        f = data["format"]
        if isinstance(f, dict):
            reqs = f.get("requirements", [])
            if reqs:
                parts.append("\n\nТребования:")
                for r in reqs:
                    parts.append("\n- " + r)
        else:
            parts.append("\n\nФормат: " + str(f))
    return "".join(parts) if parts else "Ты — полезный помощник."


def format_prompt_list(files: list[Path], prompts_data: list[dict]) -> str:
    """Форматирует список промптов для вывода."""
    lines = ["\n  📋 Доступные промпты (для ИИ-модели):", "  " + "-" * 50]
    for i, (path, data) in enumerate(zip(files, prompts_data), 1):
        name = data.get("name", path.name)
        category = data.get("category", "")
        desc = data.get("description", "")[:60]
        if len(data.get("description", "")) > 60:
            desc += "..."
        lines.append(f"  {i}. {name}")
        if category:
            lines.append(f"     Категория: {category}")
        lines.append(f"     {desc}")
        lines.append("")
    return "\n".join(lines)


def write_request_log(
    prompt_path: Path,
    model_id: str,
    temperature: float,
    system_message: str,
    user_message: str,
    model_response: str,
    usage: dict,
) -> None:
    """Сохраняет каждый запрос в .md файл: <имя json>_<модель>_<температура>.md."""
    stem = prompt_path.stem
    safe_model = model_id.replace(":", "-").replace("/", "-").replace(".", "-")
    temp_str = f"{temperature:.2f}".replace(".", "-")
    filename = f"{stem}_{safe_model}_{temp_str}.md"
    out_path = prompt_path.parent / filename

    content = [
        f"# Запрос к модели {model_id}",
        "",
        f"- Файл промпта: `{prompt_path.name}`",
        f"- Температура: `{temperature}`",
        "",
        "## System message",
        "",
        system_message,
        "",
        "## User message",
        "",
        user_message,
        "",
        "## Model response",
        "",
        model_response,
        "",
        "## Usage",
        "",
    ]

    if usage:
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        total_tokens = usage.get("total_tokens", prompt_tokens + completion_tokens)
        content.extend(
            [
                f"- prompt_tokens: {prompt_tokens}",
                f"- completion_tokens: {completion_tokens}",
                f"- total_tokens: {total_tokens}",
                "",
            ]
        )

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(content))


def print_usage_report(model_id: str, usage: dict) -> None:
    """Выводит итоговый отчёт по токенам и модели."""
    prompt_tokens = usage.get("prompt_tokens", 0)
    completion_tokens = usage.get("completion_tokens", 0)
    total_tokens = usage.get("total_tokens", prompt_tokens + completion_tokens)
    print("\n  " + "=" * 50)
    print("  📊 Итоговый отчёт")
    print("  " + "=" * 50)
    print(f"  🤖 Модель:        {model_id}")
    print(f"  📥 Вход (prompt): {prompt_tokens} токенов")
    print(f"  📤 Выход:        {completion_tokens} токенов")
    print(f"  📈 Всего:        {total_tokens} токенов")
    print("  " + "=" * 50)


def main():
    load_dotenv()
    root = Path(__file__).resolve().parent
    files = find_prompt_files(root)

    if not files:
        print("В корне проекта не найдено JSON-файлов.")
        sys.exit(1)

    prompts_data = []
    for p in files:
        try:
            prompts_data.append(load_prompt(p))
        except Exception as e:
            print(f"Ошибка чтения {p}: {e}", file=sys.stderr)
            sys.exit(1)

    print(format_prompt_list(files, prompts_data))
    choice = input("  ✏️ Введите номер промпта (1–{}): ".format(len(files))).strip()
    try:
        idx = int(choice)
        if idx < 1 or idx > len(files):
            raise ValueError("Некорректный номер")
    except ValueError:
        print("Некорректный выбор.")
        sys.exit(1)

    selected_path = files[idx - 1]
    selected_data = prompts_data[idx - 1]
    system_message = build_system_message(selected_data)

    models = [
        ("o4-mini", "o4-mini"),
        ("gpt-4.1", "gpt-4.1"),
        ("gpt-5-mini", "gpt-5-mini"),
        ("gpt-4o", "gpt-4o"),
    ]
    print("\n  🤖 Модель для запроса:")
    for i, (mid, label) in enumerate(models, 1):
        print(f"    {i}. {label}")
    model_choice = input("  🔢 Введите номер модели (1–4): ").strip()
    try:
        mi = int(model_choice)
        if mi < 1 or mi > 4:
            raise ValueError("Некорректный номер")
        model_id = models[mi - 1][0]
    except ValueError:
        print("Некорректный выбор модели.")
        sys.exit(1)

    temp_input = input("  🌡️ Температура (0.0–2.0, например 0.7): ").strip()
    try:
        temperature = float(temp_input) if temp_input else 0.7
        temperature = max(0.0, min(2.0, temperature))
    except ValueError:
        temperature = 0.7

    default_input = selected_data.get("test_input", "")
    user_msg = ""
    if default_input:
        print("\n  📎 В выбранном JSON есть test_input для примера запроса.")
        print("  ❓ Источник текста запроса:")
        print("     1 — использовать test_input из JSON")
        print("     2 — ввести свой текст")
        print("     3 — загрузить из файла в корне проекта")
        source = input("  Выбор (1–3): ").strip()
        if source == "1":
            user_msg = default_input
        elif source == "3":
            root = Path(__file__).resolve().parent
            files_in_root = sorted(p.name for p in root.iterdir() if p.is_file())
            if not files_in_root:
                print("  В корне проекта нет файлов.")
                sys.exit(1)
            print("  📂 Файлы в корне:", ", ".join(files_in_root[:20]) + (" ..." if len(files_in_root) > 20 else ""))
            fname = input("  Имя файла: ").strip()
            if not fname:
                print("  Имя файла не указано.")
                sys.exit(1)
            fpath = root / fname
            if not fpath.is_file():
                print(f"  Файл не найден: {fpath}")
                sys.exit(1)
            try:
                user_msg = fpath.read_text(encoding="utf-8")
            except Exception as e:
                print(f"  Ошибка чтения файла: {e}")
                sys.exit(1)
        else:
            user_msg = input("  💬 Введите свой текст запроса: ").strip()
    else:
        print("\n  ❓ Источник текста запроса:")
        print("     1 — ввести текст")
        print("     2 — загрузить из файла в корне проекта")
        source = input("  Выбор (1–2): ").strip()
        if source == "2":
            root = Path(__file__).resolve().parent
            files_in_root = sorted(p.name for p in root.iterdir() if p.is_file())
            if not files_in_root:
                print("  В корне проекта нет файлов.")
                sys.exit(1)
            print("  📂 Файлы в корне:", ", ".join(files_in_root[:20]) + (" ..." if len(files_in_root) > 20 else ""))
            fname = input("  Имя файла: ").strip()
            if not fname:
                print("  Имя файла не указано.")
                sys.exit(1)
            fpath = root / fname
            if not fpath.is_file():
                print(f"  Файл не найден: {fpath}")
                sys.exit(1)
            try:
                user_msg = fpath.read_text(encoding="utf-8")
            except Exception as e:
                print(f"  Ошибка чтения файла: {e}")
                sys.exit(1)
        else:
            user_msg = input("  💬 Введите текст запроса: ").strip()

    if not user_msg:
        print("Текст запроса не может быть пустым.")
        sys.exit(1)

    api_key = os.environ.get("PROXYAPI_API_KEY")
    if not api_key:
        print("Не задан PROXYAPI_API_KEY в .env")
        sys.exit(1)

    base_url = os.environ.get("PROXYAPI_BASE_URL", "https://api.proxyapi.ru/openai/v1").rstrip("/")
    url = f"{base_url}/chat/completions"
    payload = {
        "model": model_id,
        "temperature": temperature,
        "messages": [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_msg},
        ],
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    try:
        import urllib.request
        import urllib.error
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.load(resp)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        try:
            err_data = json.loads(body)
            detail = err_data.get("error", body)
            if isinstance(detail, dict):
                detail = detail.get("message", detail.get("code", str(detail)))
        except Exception:
            detail = body or str(e)
        print("Ошибка запроса к API:", e.code, e.reason)
        print("Ответ сервера:", detail)
        sys.exit(1)
    except Exception as e:
        print("Ошибка запроса к API:", e)
        sys.exit(1)

    content = ""
    for ch in result.get("choices", []):
        msg = ch.get("message", {})
        content += msg.get("content", "")
    if not content:
        print("Пустой ответ от API:", result)
        sys.exit(1)

    usage = result.get("usage", {})
    # Логируем каждый запрос в .md файл (после получения ответа)
    write_request_log(
        prompt_path=selected_path,
        model_id=model_id,
        temperature=temperature,
        system_message=system_message,
        user_message=user_msg,
        model_response=content,
        usage=usage,
    )
    print("\n" + "=" * 60 + "\n  💡 Ответ модели:\n" + "=" * 60)
    print(content)
    print("=" * 60)
    print_usage_report(model_id, usage)


if __name__ == "__main__":
    main()
