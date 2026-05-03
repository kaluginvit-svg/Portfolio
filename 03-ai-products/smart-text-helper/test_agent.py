import logging

from text_agent import TextAgent

logger = logging.getLogger(__name__)

# Нумерованные команды (0 — в главное меню, без выхода из диалога)
COMMANDS = [
    (0, "В главное меню (выбор модели и команд)"),
    (1, "Выход из программы"),
    (2, "Режим: обычная модель (OpenAI)"),
    (3, "Режим: думающая модель (Claude)"),
    (4, "Очистить историю диалога"),
    (5, "Показать меню команд"),
]


def print_help() -> None:
    print("Команды (введите номер):")
    for num, desc in COMMANDS:
        print(f"  {num} — {desc}")
    print()


def run_command(agent: TextAgent, choice: str) -> bool:
    """Выполняет команду по номеру. Возвращает False для выхода из программы, True — продолжить цикл."""
    try:
        num = int(choice.strip())
    except ValueError:
        return True
    if num == 0:
        print_help()
        return True
    if num == 1:
        print("Выход. Сохраняю историю...")
        return False
    if num == 2:
        agent.set_mode("openai")
        print(f"Режим переключен на: {agent.mode}")
        return True
    if num == 3:
        agent.set_mode("claude")
        print(f"Режим переключен на: {agent.mode}")
        level = input(
            f"Уровень рассуждения (low / medium / high) [{agent.reasoning_effort}]: "
        ).strip().lower()
        if level and level in ("low", "medium", "high"):
            agent.set_reasoning_effort(level)
            print(f"Уровень рассуждения: {agent.reasoning_effort}")
        elif level and level not in ("low", "medium", "high"):
            print("Допустимы только: low, medium, high. Оставлен текущий.")
        return True
    if num == 4:
        agent.messages = []
        print("История диалога очищена.")
        return True
    if num == 5:
        print_help()
        return True
    return True


def main() -> None:
    agent = TextAgent(mode="openai")
    agent.load_history()

    print("Консольный ассистент запущен.")
    print(f"Текущий режим: {agent.mode}")
    print(f"Уровень рассуждения (Claude): {agent.reasoning_effort}")
    print_help()

    while True:
        try:
            user_input = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nЗавершение работы...")
            break

        if not user_input:
            continue

        # Проверяем: введён номер команды (0 — в меню, 1 — выход, 2–5 — команды)?
        if user_input in ("0", "1", "2", "3", "4", "5"):
            if not run_command(agent, user_input):
                break
            continue

        # Обычное сообщение пользователя
        result = agent.generate_response(user_input)
        text = result.get("text", "")
        reasoning = result.get("reasoning")

        print("\nАссистент:")
        print(text)

        if reasoning and agent.mode == "claude":
            print("\n[Reasoning]")
            for key in ("effort", "reasoning_tokens", "total_tokens"):
                if key in reasoning:
                    val = reasoning[key]
                    print(f"{key}: {val if val is not None else '—'}")
            for k, v in reasoning.items():
                if k not in ("effort", "reasoning_tokens", "total_tokens"):
                    print(f"{k}: {v}")

        print()

    agent.save_history()
    print("Готово. История сохранена.")


if __name__ == "__main__":
    main()
