"""
CLI: интерактивный запуск агента с сохранением истории в memory.json.
Запуск из каталога agent/:  python run.py
"""
from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

# Запуск как скрипт из папки agent/
if __name__ == "__main__" and __package__ is None:
    _d = Path(__file__).resolve().parent
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

_verbose_argv = "--verbose" in sys.argv or "-v" in sys.argv

from log_config import get_trace_callback, setup_logging

_AGENT_DIR = Path(__file__).resolve().parent
setup_logging(_AGENT_DIR, verbose=_verbose_argv)

from colorama import Fore, Style, init
from agent import build_executor, lc_history_from_pairs
from session_memory import append_turn, load_memory_file, pairs_from_memory, save_memory_file

init(autoreset=True)

_log = logging.getLogger("local_agent.run")
_trace = get_trace_callback()

MEMORY_NAME = "memory.json"


def _memory_path() -> Path:
    return Path(__file__).resolve().parent / MEMORY_NAME


def load_memory() -> dict:
    return load_memory_file(_memory_path())


def save_memory(data: dict) -> None:
    save_memory_file(_memory_path(), data)


def main() -> None:
    verbose = _verbose_argv
    try:
        executor = build_executor(verbose=verbose)
    except RuntimeError as e:
        _log.error("Не удалось создать агента: %s", e)
        print(e, file=sys.stderr)
        sys.exit(1)

    memory = load_memory()
    pairs = pairs_from_memory(memory["messages"])
    _log.info(
        "Сессия CLI: в памяти сообщений=%s, пар для контекста=%s",
        len(memory.get("messages", [])),
        len(pairs),
    )

    print(
        f"{Fore.YELLOW}Локальный AI-агент.{Style.RESET_ALL} "
        "Команды: /exit — выход, /clear — очистить историю в памяти."
    )
    print("Модель:", os.getenv("OPENAI_MODEL", "gpt-4o-mini"))
    print(f"Логи: {_AGENT_DIR / 'logs' / 'agent.log'} (в консоли — INFO; в файле — DEBUG).")
    while True:
        try:
            line = input(f"\n{Fore.CYAN}Вы:{Style.RESET_ALL} ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not line:
            continue
        if line.lower() in ("/exit", "/quit", ":q"):
            break
        if line.lower() == "/clear":
            memory = {"messages": [], "turn_summaries": []}
            save_memory(memory)
            pairs = []
            _log.info("Память очищена (/clear).")
            print("История в memory.json очищена.")
            continue

        history = lc_history_from_pairs(pairs)
        _log.info(
            "Запрос пользователя (len=%s), сообщений в chat_history=%s",
            len(line),
            len(history),
        )
        _log.debug("Текст запроса: %s", line[:4000])
        try:
            out = executor.invoke(
                {"input": line, "chat_history": history},
                config={"callbacks": [_trace]},
            )
        except Exception as e:
            _log.exception("Ошибка при executor.invoke: %s", e)
            print(f"Ошибка: {e}", file=sys.stderr)
            continue

        answer = (out.get("output") or "").strip()
        _log.info("Ответ агента (len=%s)", len(answer))
        _log.debug("Текст ответа: %s", answer[:4000])
        print(f"\n{Fore.GREEN}Агент:{Style.RESET_ALL}\n{answer}")

        summary = f"Пользователь: {line[:120]}. Ответ: {answer[:200]}"
        append_turn(memory, line, answer, summary)
        pairs = pairs_from_memory(memory["messages"])
        save_memory(memory)
        _log.debug("Память сохранена, сообщений=%s", len(memory["messages"]))


if __name__ == "__main__":
    main()
