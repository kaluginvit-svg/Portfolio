import asyncio
import logging

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command

from app.config import BOT_TOKEN
from app.services import call_ai_api

logger = logging.getLogger(__name__)
logger.info("Initializing bot application...")

dp = Dispatcher()


@dp.message(Command("start"))
async def cmd_start(message: types.Message) -> None:
	logger.info("Command /start from user=%s (@%s)", message.from_user.id, message.from_user.username)
	welcome_text = (
		"Привет! 👋\n\n"
		"Я AI-ассистент. Задавай мне вопросы, и я постараюсь помочь!\n\n"
		"Я отвечаю через OpenRouter. Пиши свой вопрос! 💬"
	)
	await message.answer(welcome_text)


@dp.message(Command("ping"))
async def cmd_ping(message: types.Message) -> None:
	logger.info("Command /ping from user=%s", message.from_user.id)
	await message.answer("pong 🏓")


@dp.message(Command("help"))
async def cmd_help(message: types.Message) -> None:
	logger.info("Command /help from user=%s", message.from_user.id)
	help_text = """
🤖 Доступные команды:
/start - Начать работу
/ping - Проверка соединения
/help - Справка

Просто пиши мне вопросы или делись своими мыслями - я отвечу! 💬
	"""
	await message.answer(help_text)


@dp.message(F.text)
async def handle_user_message(message: types.Message) -> None:
	"""Обработка текстовых сообщений пользователя через выбранный API"""
	user_id = message.from_user.id
	user_text = message.text.strip()
	
	logger.info(f"📨 Сообщение от user={user_id}: {user_text[:100]}")
	
	if not user_text:
		await message.answer("Пожалуйста, напиши что-то 😊")
		return

	agent_name = "OpenRouter"
	processing_msg = await message.answer(f"⏳ Думаю над ответом ({agent_name})...")
	
	try:
		# Обратиться к выбранному API
		logger.info(f"🔄 Запрос к {agent_name} для user={user_id}")
		response = await call_ai_api(user_text)
		
		if response:
			logger.info(f"✅ Успешно получен ответ от {agent_name} для user={user_id}")
			# Отредактировать сообщение с ответом
			await processing_msg.edit_text(response)
		else:
			logger.warning(f"⚠️ Пустой ответ от {agent_name} для user={user_id}")
			error_msg = (
				f"❌ Не удалось получить ответ от {agent_name}.\n\n"
				"Возможные причины:\n"
				"• API недоступен\n"
				"• Превышен лимит запросов\n"
				"• Неверный API ключ\n\n"
				"Попробуй позже или проверь логи."
			)
			await processing_msg.edit_text(error_msg)
			
	except Exception as exc:
		logger.exception(f"❌ Ошибка обработки сообщения от user={user_id}: {exc}")
		error_msg = f"❌ Произошла ошибка при обработке сообщения: {str(exc)[:100]}"
		try:
			await processing_msg.edit_text(error_msg)
		except:
			await message.answer(error_msg)



@dp.message()
async def handle_fallback(message: types.Message) -> None:
	"""Обработчик для всех остальных типов сообщений"""
	logger.info("Fallback handler for user=%s", message.from_user.id)
	await message.answer(
		"Я пока поддерживаю только текстовые сообщения. Напиши мне вопрос! 😊"
	)



async def main() -> None:
	"""Main entry point for the bot"""
	logger.info("=" * 60)
	logger.info("🚀 Starting Telegram Bot...")
	logger.info("=" * 60)
	
	# Проверка BOT_TOKEN
	if not BOT_TOKEN or BOT_TOKEN == "PASTE_YOUR_TOKEN_HERE":
		logger.error("❌ BOT_TOKEN не установлен в переменных окружения!")
		logger.error("Пожалуйста, установите BOT_TOKEN в файле .env")
		return
	
	logger.info("✅ BOT_TOKEN загружен успешно")
	
	# Создание бота и диспетчера
	bot = Bot(token=BOT_TOKEN)
	
	try:
		# Получение информации о боте
		bot_info = await bot.get_me()
		logger.info(f"✅ Подключено к боту: @{bot_info.username}")
		logger.info(f"Bot ID: {bot_info.id}")
		logger.info("=" * 60)
		logger.info("📡 Начинается polling...")
		logger.info("=" * 60)
		
		# Запуск polling
		await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
		
	except Exception as exc:
		logger.error(f"❌ Ошибка при запуске бота: {exc}")
		raise
	finally:
		logger.info("🛑 Бот остановлен")
		await bot.session.close()


if __name__ == "__main__":
	try:
		asyncio.run(main())
	except KeyboardInterrupt:
		logger.info("Бот остановлен пользователем (Ctrl+C)")
	except Exception as exc:
		logger.error(f"Критическая ошибка: {exc}", exc_info=True)

