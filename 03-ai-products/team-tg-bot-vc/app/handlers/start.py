from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

router = Router()


@router.message(CommandStart())
async def start(message: Message) -> None:
    """
    Обработчик команды /start.
    Приветствует пользователя и показывает доступные команды.
    """
    await message.answer(
        "👋 Привет! Я бот для командных задач.\n\n"
        "💡 Доступные команды:\n"
        "• /add — добавить задачу (бот запросит текст задачи)\n"
        "• /list — показать список всех задач\n"
        "• /list_csv — получить CSV-файл со всеми задачами\n"
        "• /cancel — отменить текущее действие\n\n"
        "📝 Для добавления задачи отправьте /add, затем введите текст задачи в ответном сообщении.",
    )
