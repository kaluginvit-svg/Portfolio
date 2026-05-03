"""
Точка входа: запуск конвертера валют (cli).
Ошибки не приводят к стектрейсу — выводятся сообщения пользователю.
"""
import sys


def main() -> None:
    try:
        from cli import main_cli
        main_cli()
    except Exception as e:
        print(f"Ошибка: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
