"""
AI Client Report Generator — CLI: транскрипция → ProxyAPI → PDF.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv

# Загрузка .env из каталога проекта
_PROJECT = Path(__file__).resolve().parent
TXT_DIR = _PROJECT / "txt"
load_dotenv(_PROJECT / ".env")

from client_report import (
    compute_cost_usd,
    generate_report_pdf,
    print_token_cost_report,
    process_dialog_with_ai,
    resolve_usd_rub_rate,
)


def _ensure_txt_dir() -> Path:
    TXT_DIR.mkdir(parents=True, exist_ok=True)
    return TXT_DIR


def _list_txt_files() -> list[Path]:
    _ensure_txt_dir()
    return sorted(TXT_DIR.glob("*.txt"))


def _read_multiline_manual() -> str:
    print(
        "Введите транскрипцию диалога. Завершите ввод пустой строкой после текста:",
        flush=True,
    )
    lines: list[str] = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if line == "" and lines:
            break
        lines.append(line)
    return "\n".join(lines).strip()


def _prompt_pick_txt_file(files: list[Path], *, allow_manual: bool = True) -> Path | None:
    """
    Меню выбора файла из txt/. Возвращает Path или None, если выбран ручной ввод (0).
    При allow_manual=False — только номера 1…N (для --pick-txt).
    """
    print("Папка txt — выберите файл с транскрипцией:\n", flush=True)
    for i, p in enumerate(files, start=1):
        print(f"  {i}) {p.name}", flush=True)
    if allow_manual:
        print("  0) ввести текст вручную в терминале\n", flush=True)
    else:
        print(flush=True)
    hi = len(files)
    sys.stdout.flush()
    while True:
        try:
            raw = input("Номер (цифра и Enter): ").strip()
        except EOFError:
            raise SystemExit(1) from None
        if raw == "":
            print("Введите число.", flush=True)
            continue
        try:
            n = int(raw)
        except ValueError:
            print("Нужно целое число.", flush=True)
            continue
        if allow_manual and n == 0:
            return None
        if not allow_manual and n == 0:
            print(f"Укажите номер файла от 1 до {hi}.", flush=True)
            continue
        if 1 <= n <= hi:
            return files[n - 1]
        rng = f"0…{hi}" if allow_manual else f"1…{hi}"
        print(f"Допустимо: {rng}.", flush=True)


def read_transcript(args: argparse.Namespace) -> str:
    if args.file:
        path = Path(args.file)
        if not path.is_file():
            raise FileNotFoundError(f"Файл не найден: {path}")
        return path.read_text(encoding="utf-8")
    if args.text:
        return args.text
    if not sys.stdin.isatty():
        return sys.stdin.read()
    txt_files = _list_txt_files()
    if txt_files:
        chosen = _prompt_pick_txt_file(txt_files)
        if chosen is not None:
            return chosen.read_text(encoding="utf-8")
    return _read_multiline_manual()


def read_transcript_with_pick_mode(args: argparse.Namespace) -> str:
    """Учитывает --pick-txt: только интерактивный выбор из txt/."""
    if args.pick_txt:
        files = _list_txt_files()
        if not files:
            raise FileNotFoundError(
                f"В папке {TXT_DIR} нет файлов .txt. Добавьте транскрипции в txt/."
            )
        chosen = _prompt_pick_txt_file(files, allow_manual=False)
        assert chosen is not None
        return chosen.read_text(encoding="utf-8")
    return read_transcript(args)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Генерация PDF-отчёта по транскрипции диалога с клиентом."
    )
    parser.add_argument(
        "-f",
        "--file",
        type=str,
        help="Путь к текстовому файлу с транскрипцией",
    )
    parser.add_argument(
        "-t",
        "--text",
        type=str,
        help="Транскрипция одной строкой (для скриптов)",
    )
    parser.add_argument(
        "--pick-txt",
        action="store_true",
        help="Только выбор .txt из папки txt (без пункта «вручную»)",
    )
    parser.add_argument(
        "--usd-rub",
        type=float,
        default=None,
        metavar="RATE",
        help="Курс USD/RUB (руб/$) без запроса; иначе спросим или возьмём USD_RUB_RATE из .env",
    )
    parser.add_argument(
        "--no-cost-report",
        action="store_true",
        help="Не выводить отчёт по токенам и стоимости",
    )
    args = parser.parse_args()

    if args.file and args.text:
        print("Укажите либо --file, либо --text, не оба сразу.", file=sys.stderr)
        return 2
    if args.pick_txt and (args.file or args.text):
        print("Нельзя совмещать --pick-txt с --file или --text.", file=sys.stderr)
        return 2

    try:
        transcript = read_transcript_with_pick_mode(args)
        result = process_dialog_with_ai(transcript)
        pdf_path = generate_report_pdf(result.data)
    except Exception as e:
        print(f"Ошибка: {e}", file=sys.stderr)
        return 1

    try:
        rel = pdf_path.relative_to(_PROJECT)
    except ValueError:
        rel = pdf_path
    print(f"Отчёт успешно создан: {rel}")

    if not args.no_cost_report:
        cost = compute_cost_usd(result.prompt_tokens, result.completion_tokens)
        rate = resolve_usd_rub_rate(
            interactive=sys.stdin.isatty(),
            cli_rate=args.usd_rub,
        )
        print_token_cost_report(
            model=result.model,
            prompt_tokens=result.prompt_tokens,
            completion_tokens=result.completion_tokens,
            total_tokens=result.total_tokens,
            cost=cost,
            usd_rub=rate,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
