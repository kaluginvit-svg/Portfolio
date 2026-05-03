import csv
import io

from aiogram import Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, Message

from app.db.sqlite import add_task, list_tasks
from app.states import TaskStates

router = Router()


@router.message(Command("add"))
async def add_task_handler(message: Message, state: FSMContext) -> None:
    """
    Обработчик команды /add.
    Запрашивает у пользователя ввод текста задачи.
    """
    await state.set_state(TaskStates.waiting_for_task_text)
    await message.answer(
        "➕ <b>Добавление задачи</b>\n\n"
        "📝 Введите текст задачи:",
        parse_mode="HTML",
    )


@router.message(Command("list"))
async def list_tasks_handler(message: Message) -> None:
    """
    Обработчик команды /list.
    Отправляет отдельное сообщение со списком всех задач.
    """
    tasks = list_tasks()
    if not tasks:
        await message.answer(
            "📋 <b>Список задач пуст</b>\n\n"
            "Используйте команду /add для добавления новой задачи.",
            parse_mode="HTML",
        )
        return

    # Формируем отдельное сообщение со списком задач
    lines = ["📋 <b>Список задач:</b>\n"]
    for task_id, text, user, created_at in tasks:
        lines.append(
            f"<b>#{task_id}</b> {text}\n"
            f"👤 {user} | 🕐 {created_at}\n"
        )

    await message.answer(
        "\n".join(lines),
        parse_mode="HTML",
    )


@router.message(Command("list_csv"))
async def list_csv_handler(message: Message) -> None:
    """
    Обработчик команды /list_csv.
    Отправляет отдельное сообщение с CSV-файлом всех задач.
    """
    tasks = list_tasks()

    if not tasks:
        await message.answer(
            "📊 <b>Список задач пуст</b>\n\n"
            "Нет данных для экспорта в CSV.",
            parse_mode="HTML",
        )
        return

    # Формируем CSV файл с поддержкой UTF-8 и BOM для корректного отображения в Excel
    output = io.StringIO()
    # Используем точку с запятой как разделитель для Excel (особенно важно для русской локализации)
    writer = csv.writer(output, delimiter=";", quoting=csv.QUOTE_MINIMAL)
    writer.writerow(["id", "text", "user", "created_at"])
    for row in tasks:
        writer.writerow(row)

    # Добавляем BOM (Byte Order Mark) для UTF-8, чтобы Excel корректно читал русские символы
    csv_text = output.getvalue()
    csv_bytes = csv_text.encode("utf-8-sig")  # utf-8-sig добавляет BOM
    file = BufferedInputFile(csv_bytes, filename="tasks.csv")

    # Отправляем отдельное сообщение с файлом
    await message.answer_document(
        file,
        caption="📊 <b>Экспорт задач в CSV</b>\n\n"
        "Файл с вашими задачами готов к скачиванию.",
        parse_mode="HTML",
    )


@router.message(StateFilter(TaskStates.waiting_for_task_text))
async def process_task_text(message: Message, state: FSMContext) -> None:
    """
    Обработчик ввода текста задачи после команды /add.
    Добавляет задачу в базу данных и отправляет отдельное сообщение с подтверждением.
    """
    # Проверяем, что это не команда
    if message.text and message.text.startswith("/"):
        await message.answer(
            "⚠️ Пожалуйста, введите текст задачи, а не команду.\n"
            "Для отмены используйте команду /cancel"
        )
        return

    if not message.text or not message.text.strip():
        await message.answer(
            "⚠️ Текст задачи не может быть пустым.\n"
            "Пожалуйста, введите текст задачи."
        )
        return

    text = message.text.strip()
    user = (
        message.from_user.full_name
        if message.from_user
        else message.from_user.username or "Unknown"
    )

    # Добавляем задачу в базу данных
    add_task(text=text, user=user)

    # Очищаем состояние
    await state.clear()

    # Отправляем отдельное сообщение с подтверждением
    await message.answer(
        f"✅ <b>Задача добавлена!</b>\n\n"
        f"📝 <b>Текст:</b> {text}\n"
        f"👤 <b>Автор:</b> {user}",
        parse_mode="HTML",
    )


@router.message(Command("cancel"))
async def cancel_handler(message: Message, state: FSMContext) -> None:
    """
    Обработчик команды /cancel для отмены текущего действия.
    """
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("Нет активных действий для отмены.")
        return

    await state.clear()
    await message.answer("❌ Действие отменено.")
