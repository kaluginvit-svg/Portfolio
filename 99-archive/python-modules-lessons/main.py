from __future__ import annotations

import argparse
import sys

from utils import add_note, delete_note, list_notes


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Управление заметками.")
    subparsers = parser.add_subparsers(dest="command")

    add_parser = subparsers.add_parser("add", help="Добавить новую заметку")
    add_parser.add_argument("text", help="Текст заметки")

    subparsers.add_parser("list", help="Показать все заметки")

    delete_parser = subparsers.add_parser("delete", help="Удалить заметку по номеру")
    delete_parser.add_argument("number", type=int, help="Номер заметки из списка")

    return parser


def handle_add(text: str) -> None:
    add_note(text)
    print("Заметка добавлена.")


def handle_list() -> None:
    notes = list_notes()
    if not notes:
        print("Заметок нет.")
        return
    for idx, note in enumerate(notes, start=1):
        print(f"{idx}. {note}")


def handle_delete(number: int) -> None:
    try:
        removed = delete_note(number)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
    print(f"Удалено: {removed}")


def interactive_menu() -> None:
    """Простой текстовый выбор действий."""
    while True:
        print("Выберите действие:")
        print("1. Добавить заметку")
        print("2. Показать все заметки")
        print("3. Удалить заметку по номеру")
        print("4. Выход")

        choice = input("> ").strip()

        if choice == "1":
            text = input("Текст заметки: ").strip()
            if text:
                handle_add(text)
            else:
                print("Пустая заметка не добавлена.")
        elif choice == "2":
            handle_list()
        elif choice == "3":
            number_raw = input("Номер заметки: ").strip()
            if not number_raw.isdigit():
                print("Нужно указать номер.")
                continue
            handle_delete(int(number_raw))
        elif choice == "4":
            print("Выход.")
            break
        else:
            print("Неверный выбор. Попробуйте снова.")


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        # Запуск без аргументов показывает меню выбора действий.
        interactive_menu()
    elif args.command == "add":
        handle_add(args.text)
    elif args.command == "list":
        handle_list()
    elif args.command == "delete":
        handle_delete(args.number)
    else:
        parser.error("Неизвестная команда")


if __name__ == "__main__":
    main()

