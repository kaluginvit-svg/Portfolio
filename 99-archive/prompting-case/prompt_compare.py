#!/usr/bin/env python3
"""
prompt_compare — подробное сравнение запросов из .md файлов для выбранного JSON-промпта.
"""

import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple


def find_json_files(root: Path) -> List[Path]:
    """Ищет все JSON-файлы в корневой папке."""
    return sorted(root.glob("*.json"))


def format_json_list(files: List[Path]) -> str:
    """Форматирует список JSON-файлов для выбора."""
    lines = ["\n  📂 Доступные JSON-промпты:", "  " + "-" * 50]
    for i, p in enumerate(files, 1):
        lines.append(f"  {i}. {p.name}")
    return "\n".join(lines)


def parse_md_request(md_path: Path) -> Dict[str, Any]:
    """
    Парсит .md файл, созданный prompt_chat.write_request_log.
    Возвращает model, temperature, preview (первая строка user), response, usage (tokens).
    """
    model = ""
    temperature = ""
    user_message_preview = ""
    model_response = ""
    prompt_tokens = 0
    completion_tokens = 0
    total_tokens = 0

    try:
        with open(md_path, encoding="utf-8") as f:
            lines = [line.rstrip("\n") for line in f]
    except Exception:
        return _result_dict(model, temperature, user_message_preview, model_response, prompt_tokens, completion_tokens, total_tokens)

    in_user = False
    in_model = False
    for line in lines:
        if line.startswith("# Запрос к модели"):
            parts = line.split("модели", 1)
            if len(parts) == 2:
                model = parts[1].strip()
        elif line.startswith("- Температура"):
            if "`" in line:
                temperature = line.split("`")[1]
            else:
                temperature = line.split(":", 1)[-1].strip()
        elif line.startswith("- prompt_tokens:"):
            try:
                prompt_tokens = int(line.split(":", 1)[1].strip())
            except ValueError:
                pass
        elif line.startswith("- completion_tokens:"):
            try:
                completion_tokens = int(line.split(":", 1)[1].strip())
            except ValueError:
                pass
        elif line.startswith("- total_tokens:"):
            try:
                total_tokens = int(line.split(":", 1)[1].strip())
            except ValueError:
                pass
        elif line.strip() == "## User message":
            in_user = True
            in_model = False
            continue
        elif line.strip() == "## Model response":
            in_model = True
            in_user = False
            continue
        elif line.startswith("## "):
            in_user = False
            in_model = False
        elif in_user:
            if not user_message_preview and line.strip():
                user_message_preview = line.strip()
        elif in_model:
            model_response = model_response + "\n" + line if model_response else line

    return _result_dict(model, temperature, user_message_preview, model_response, prompt_tokens, completion_tokens, total_tokens)


def _result_dict(
    model: str,
    temperature: str,
    preview: str,
    response: str,
    prompt_tokens: int,
    completion_tokens: int,
    total_tokens: int,
) -> Dict[str, Any]:
    return {
        "model": model,
        "temperature": temperature,
        "preview": preview,
        "response": response,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
    }


def word_count(text: str) -> int:
    """Приблизительное число слов (последовательности непробельных символов)."""
    return len(re.findall(r"\S+", text.strip()))


def response_preview(response: str, max_lines: int = 3, max_chars_per_line: int = 80) -> str:
    """Первые строки ответа для сравнения ясности."""
    lines = [s.strip() for s in response.strip().split("\n") if s.strip()][:max_lines]
    out = []
    for line in lines:
        if len(line) > max_chars_per_line:
            line = line[: max_chars_per_line - 3] + "..."
        out.append(line)
    return " | ".join(out) if out else "—"


def main():
    root = Path(__file__).resolve().parent
    json_files = find_json_files(root)

    if not json_files:
        print("В корне проекта не найдено JSON-файлов.")
        sys.exit(1)

    print(format_json_list(json_files))
    choice = input(f"  ✏️ Выберите JSON (1–{len(json_files)}): ").strip()
    try:
        idx = int(choice)
        if idx < 1 or idx > len(json_files):
            raise ValueError("Некорректный номер")
    except ValueError:
        print("Некорректный выбор.")
        sys.exit(1)

    selected_json = json_files[idx - 1]
    stem = selected_json.stem

    md_files = sorted(root.glob(f"{stem}_*.md"))
    if not md_files:
        print(f"Для {selected_json.name} не найдено .md-файлов с запросами.")
        sys.exit(0)

    # Собираем данные по каждому .md
    records: List[Dict[str, Any]] = []
    for i, md in enumerate(md_files, 1):
        info = parse_md_request(md)
        info["file"] = md.name
        info["index"] = i
        resp = info.get("response") or ""
        info["response_len"] = len(resp.strip())
        info["word_count"] = word_count(resp)
        info["response_preview"] = response_preview(resp)
        records.append(info)

    # Агрегаты для подробного анализа
    response_lens = [r["response_len"] for r in records if r["response_len"] > 0]
    word_counts = [r["word_count"] for r in records if r["word_count"] > 0]
    total_tokens_list = [r["total_tokens"] for r in records if r["total_tokens"] > 0]
    min_len = min(response_lens) if response_lens else 0
    max_len = max(response_lens) if response_lens else 0
    avg_len = sum(response_lens) // len(response_lens) if response_lens else 0
    avg_words = sum(word_counts) // len(word_counts) if word_counts else 0

    # Температура как число для группировки
    def temp_float(t: str) -> float:
        try:
            return float(str(t).replace(",", ".").strip())
        except (TypeError, ValueError):
            return -1.0

    # ---- 1. Сводная таблица ----
    print("\n" + "=" * 80)
    print("📊 1. Сводная таблица запросов")
    print("=" * 80)
    print()
    print("| # | Файл | Модель | Температура | Символов | Слов | prompt_tok | compl_tok | total_tok |")
    print("|---|------|--------|-------------|----------|------|------------|-----------|-----------|")
    for r in records:
        pt = r.get("prompt_tokens") or 0
        ct = r.get("completion_tokens") or 0
        tt = r.get("total_tokens") or 0
        print(f"| {r['index']} | `{r['file']}` | {r.get('model') or '—'} | {r.get('temperature') or '—'} | {r['response_len']} | {r['word_count']} | {pt} | {ct} | {tt} |")
    print()

    # ---- 2. Анализ полноты ответов ----
    print("=" * 80)
    print("📈 2. Анализ полноты ответов")
    print("=" * 80)
    print()
    if response_lens:
        by_len = sorted(records, key=lambda x: x["response_len"], reverse=True)
        print("- **Самый подробный по объёму:**", by_len[0]["file"], f"({by_len[0]['response_len']} симв., {by_len[0]['word_count']} слов)")
        print("- **Самый краткий:**", by_len[-1]["file"], f"({by_len[-1]['response_len']} симв., {by_len[-1]['word_count']} слов)")
        print(f"- **Средний объём:** {avg_len} симв., ~{avg_words} слов.")
        print()
        for r in records:
            rel = ""
            if r["response_len"] == max_len and max_len > 0:
                rel = " ← максимум"
            elif r["response_len"] == min_len and min_len > 0 and min_len != max_len:
                rel = " ← минимум"
            print(f"  {r['index']}. {r['file']}: {r['response_len']} симв., {r['word_count']} слов ({r.get('model')}, temp={r.get('temperature')}){rel}")
    print()

    # ---- 3. Влияние температуры ----
    print("=" * 80)
    print("🌡️ 3. Влияние температуры на полноту и ясность")
    print("=" * 80)
    print()
    by_temp: Dict[float, List[Dict[str, Any]]] = {}
    for r in records:
        t = temp_float(r.get("temperature") or "")
        if t < 0:
            t = -1.0
        by_temp.setdefault(t, []).append(r)
    for t in sorted(by_temp.keys()):
        if t < 0:
            label = "температура не указана"
        else:
            label = f"температура {t}"
        runs = by_temp[t]
        lens = [x["response_len"] for x in runs if x["response_len"] > 0]
        avg = sum(lens) // len(lens) if lens else 0
        print(f"- **{label}** ({len(runs)} запросов): средняя длина ответа {avg} симв.")
        for r in runs:
            print(f"    - {r['file']}: модель {r.get('model')}, {r['response_len']} симв.")
        if t >= 0:
            if t <= 0.5:
                print("    → низкая температура: ожидаемо более чёткие и предсказуемые формулировки.")
            elif t <= 1.0:
                print("    → средняя: баланс между полнотой и креативностью.")
            else:
                print("    → высокая: выше вариативность, возможна потеря ясности.")
        print()
    print()

    # ---- 4. Сравнение по моделям ----
    print("=" * 80)
    print("🤖 4. Сравнение по моделям")
    print("=" * 80)
    print()
    by_model: Dict[str, List[Dict[str, Any]]] = {}
    for r in records:
        m = r.get("model") or "—"
        by_model.setdefault(m, []).append(r)
    for m in sorted(by_model.keys()):
        runs = by_model[m]
        lens = [x["response_len"] for x in runs if x["response_len"] > 0]
        toks = [x["total_tokens"] for x in runs if x["total_tokens"] > 0]
        avg_len = sum(lens) // len(lens) if lens else 0
        avg_tok = sum(toks) // len(toks) if toks else 0
        print(f"- **Модель {m}** ({len(runs)} запусков): средняя длина ответа {avg_len} симв., в среднем {avg_tok} токенов на запрос.")
        for r in runs:
            print(f"    - temp={r.get('temperature')}: {r['response_len']} симв., {r.get('total_tokens', 0)} токенов — {r['file']}")
        print()
    print()

    # ---- 5. Превью ответов (ясность) ----
    print("=" * 80)
    print("💬 5. Превью ответов (сравнение ясности начала текста)")
    print("=" * 80)
    print()
    for r in records:
        prev = (r.get("response_preview") or "—").replace("\n", " ")
        print(f"**{r['index']}. {r['file']}** (модель: {r.get('model')}, temp: {r.get('temperature')})")
        print(f"  {prev}")
        print()
    print("=" * 80)


if __name__ == "__main__":
    main()

