"""
Основной файл телеграм-бота.
Содержит инициализацию бота и обработчики сообщений.
"""

import logging
import random
import telebot
from telebot import types
from config import Config
from database import Database
from states import UserStates, FormState
from backup import BackupManager

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Инициализация бота
bot = telebot.TeleBot(Config.TELEGRAM_BOT_TOKEN)

# Инициализация подключения к базе данных
db = Database(
    host=Config.DB_HOST,
    port=Config.DB_PORT,
    database=Config.DB_NAME,
    user=Config.DB_USER,
    password=Config.DB_PASSWORD
)

# Инициализация управления состояниями пользователей
user_states = UserStates()

# Инициализация менеджера резервного копирования (Excel и SQLite)
backup_manager = BackupManager(excel_path="backup.xlsx", sqlite_path="backup.db")

# Имя таблицы для работы бота
FORM_TABLE_NAME = "serials"  # Работаем только с таблицей serials


@bot.message_handler(commands=['start'])
def handle_start(message: types.Message):
    """Обработчик команды /start."""
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    
    logger.info(f"Пользователь {username} (ID: {user_id}) запустил бота")
    
    welcome_text = (
        f"Привет, {username}!\n\n"
        "Я бот для сбора информации о сериалах.\n"
        "Используй /help для получения списка доступных команд."
    )
    
    bot.reply_to(message, welcome_text)


@bot.message_handler(commands=['help'])
def handle_help(message: types.Message):
    """Обработчик команды /help."""
    help_text = (
        "Доступные команды:\n\n"
        "/start - Начать работу с ботом\n"
        "/help - Показать это сообщение\n"
        "/form - Добавить информацию о сериале\n"
        "/status - Проверить статус подключения к базе данных"
    )
    
    bot.reply_to(message, help_text)


@bot.message_handler(commands=['status'])
def handle_status(message: types.Message):
    """Обработчик команды /status - проверка подключения к БД."""
    if not db.connection:
        db.connect()
    
    if db.test_connection():
        tables = db.get_tables()
        status_text = (
            "✅ Подключение к базе данных активно\n\n"
            f"Найдено таблиц: {len(tables)}\n"
        )
        
        if tables:
            status_text += "Таблицы в базе данных:\n"
            for table in tables:
                status_text += f"  • {table}\n"
    else:
        status_text = "❌ Ошибка подключения к базе данных"
    
    bot.reply_to(message, status_text)


@bot.message_handler(commands=['form'])
def handle_form(message: types.Message):
    """
    Обработчик команды /form - начало заполнения информации о сериале.
    """
    user_id = message.from_user.id
    logger.info(f"Пользователь {user_id} начал заполнение информации о сериале")
    
    # Инициализируем резервные копии при первом запуске
    try:
        columns = db.get_table_columns(FORM_TABLE_NAME)
        backup_manager.initialize(FORM_TABLE_NAME, columns)
        logger.info("Резервные копии (Excel и SQLite) инициализированы")
    except Exception as e:
        logger.warning(f"Не удалось инициализировать резервные копии (не критично): {e}")
    
    # Сбрасываем предыдущее состояние, если было
    user_states.reset_state(user_id)
    
    # Устанавливаем состояние ожидания названия сериала
    user_states.set_state(user_id, FormState.WAITING_SERIAL)
    
    form_text = (
        "📺 Начинаем заполнение информации о сериале.\n\n"
        "1️⃣ Как называется сериал?\n"
        "Напиши название сериала."
    )
    
    bot.reply_to(message, form_text)


@bot.message_handler(func=lambda message: True)
def handle_message(message: types.Message):
    """
    Обработчик всех сообщений с проверкой состояния пользователя.
    """
    user_id = message.from_user.id
    state = user_states.get_state(user_id)
    
    # Если пользователь в процессе заполнения формы
    if state == FormState.WAITING_SERIAL:
        handle_serial_input(message)
    elif state == FormState.WAITING_DIRECTOR:
        handle_director_input(message)
    elif state == FormState.WAITING_YEAR:
        handle_year_input(message)
    elif state == FormState.WAITING_STATUS:
        handle_status_input(message)
    elif state == FormState.WAITING_RATING:
        handle_rating_input(message)
    else:
        # Обычное сообщение - показываем помощь
        bot.reply_to(
            message,
            "Не понимаю эту команду. Используй /help для списка доступных команд."
        )


def handle_serial_input(message: types.Message):
    """Обработчик ввода названия сериала."""
    user_id = message.from_user.id
    serial_name = message.text.strip()
    
    if not serial_name or len(serial_name) < 2:
        bot.reply_to(
            message,
            "❌ Пожалуйста, введите корректное название сериала (минимум 2 символа)."
        )
        return
    
    # Сохраняем название сериала
    user_states.set_form_data(user_id, 'Сериал', serial_name)
    
    # Переходим к следующему шагу
    user_states.set_state(user_id, FormState.WAITING_DIRECTOR)
    
    bot.reply_to(
        message,
        (
            f"✅ Название сериала сохранено: {serial_name}\n\n"
            "2️⃣ Кто режиссер?\n"
            "Напиши имя режиссера."
        )
    )


def handle_director_input(message: types.Message):
    """Обработчик ввода режиссера."""
    user_id = message.from_user.id
    director = message.text.strip()
    
    if not director or len(director) < 2:
        bot.reply_to(
            message,
            "❌ Пожалуйста, введите корректное имя режиссера (минимум 2 символа)."
        )
        return
    
    # Сохраняем режиссера
    user_states.set_form_data(user_id, 'Режиссер', director)
    
    # Переходим к следующему шагу
    user_states.set_state(user_id, FormState.WAITING_YEAR)
    
    bot.reply_to(
        message,
        (
            f"✅ Режиссер сохранен: {director}\n\n"
            "3️⃣ Какой год выпуска?\n"
            "Введи год (например, 2020)."
        )
    )


def handle_year_input(message: types.Message):
    """Обработчик ввода года."""
    user_id = message.from_user.id
    year_str = message.text.strip()
    
    try:
        year = int(year_str)
        if year < 1900 or year > 2025:
            raise ValueError("Год вне допустимого диапазона")
    except ValueError:
        bot.reply_to(
            message,
            "❌ Неверный формат года. Введи год числом (например, 2020)."
        )
        return
    
    # Сохраняем год
    user_states.set_form_data(user_id, 'Год', str(year))
    
    # Переходим к следующему шагу
    user_states.set_state(user_id, FormState.WAITING_STATUS)
    
    bot.reply_to(
        message,
        (
            f"✅ Год сохранен: {year}\n\n"
            "4️⃣ Статус просмотра?\n"
            "Напиши: Просмотрено, Не просмотрено, В процессе или Запланировано"
        )
    )


def handle_status_input(message: types.Message):
    """Обработчик ввода статуса."""
    user_id = message.from_user.id
    status = message.text.strip()
    
    valid_statuses = ['Просмотрено', 'Не просмотрено', 'В процессе', 'Запланировано']
    if status not in valid_statuses:
        bot.reply_to(
            message,
            f"❌ Неверный статус. Используй один из: {', '.join(valid_statuses)}"
        )
        return
    
    # Сохраняем статус
    user_states.set_form_data(user_id, 'Статус', status)
    
    # Переходим к следующему шагу
    user_states.set_state(user_id, FormState.WAITING_RATING)
    
    bot.reply_to(
        message,
        (
            f"✅ Статус сохранен: {status}\n\n"
            "5️⃣ Рейтинг?\n"
            "Введи рейтинг от 0 до 10 (можно с десятичной частью, например 8.5)."
        )
    )


def handle_rating_input(message: types.Message):
    """Обработчик ввода рейтинга."""
    user_id = message.from_user.id
    rating_str = message.text.strip()
    
    try:
        rating = float(rating_str)
        if rating < 0 or rating > 10:
            raise ValueError("Рейтинг вне допустимого диапазона")
        rating = round(rating, 1)
    except ValueError:
        bot.reply_to(
            message,
            "❌ Неверный формат рейтинга. Введи число от 0 до 10 (например, 8.5)."
        )
        return
    
    # Сохраняем рейтинг
    user_states.set_form_data(user_id, 'Рейтинг', str(rating))
    
    # Получаем все данные формы
    form_data = user_states.get_form_data(user_id)
    
    # Получаем структуру таблицы
    columns = db.get_table_columns(FORM_TABLE_NAME)
    
    # Преобразуем типы данных для правильного сохранения
    for col in columns:
        col_name = col['column_name']
        col_type = col['data_type']
        
        if col_name in form_data:
            value = form_data[col_name]
            
            # Преобразуем год в integer
            if col_name == 'Год' and col_type in ('integer', 'int4', 'bigint', 'int8'):
                try:
                    form_data[col_name] = int(value)
                except:
                    pass
            
            # Преобразуем рейтинг в float/decimal
            if col_name == 'Рейтинг' and col_type in ('numeric', 'decimal', 'real', 'double precision'):
                try:
                    form_data[col_name] = float(value)
                except:
                    pass
    
    # Сохраняем данные в базу данных
    if db.insert_form_data(FORM_TABLE_NAME, form_data):
        # Автоматически выполняем резервное копирование сразу после успешного сохранения в БД
        try:
            backup_manager.save_data(FORM_TABLE_NAME, form_data, columns, db_connection=db)
            logger.info(f"Данные пользователя {user_id} автоматически сохранены во все резервные копии")
        except Exception as e:
            # Ошибка сохранения в резервные копии не должна прерывать работу бота
            logger.error(f"Ошибка автоматического резервного копирования (не критично): {e}")
        
        # Формируем сообщение об успехе
        success_text = (
            "✅ Информация о сериале успешно сохранена!\n\n"
            f"📋 Ваши данные:\n"
            f"• Сериал: {form_data.get('Сериал', 'Не указано')}\n"
            f"• Режиссер: {form_data.get('Режиссер', 'Не указано')}\n"
            f"• Год: {form_data.get('Год', 'Не указано')}\n"
            f"• Статус: {form_data.get('Статус', 'Не указано')}\n"
            f"• Рейтинг: {form_data.get('Рейтинг', 'Не указано')}\n"
        )
        
        bot.reply_to(message, success_text)
        logger.info(f"Информация о сериале пользователя {user_id} сохранена в базу данных")
    else:
        bot.reply_to(
            message,
            "❌ Ошибка при сохранении данных. Попробуйте позже или обратитесь к администратору."
        )
        logger.error(f"Ошибка сохранения информации о сериале пользователя {user_id}")
    
    # Сбрасываем состояние
    user_states.reset_state(user_id)


def main():
    """Основная функция запуска бота."""
    # Проверка конфигурации
    if not Config.validate():
        logger.error("Не все параметры конфигурации заданы. Проверьте .env файл.")
        return
    
    # Подключение к базе данных
    if not db.connect():
        logger.error("Не удалось подключиться к базе данных. Проверьте настройки.")
        return
    
    logger.info("Бот запущен и готов к работе")
    
    try:
        # Запуск бота
        bot.polling(none_stop=True, interval=0)
    except KeyboardInterrupt:
        logger.info("Остановка бота...")
    finally:
        # Закрываем подключения и файлы
        db.disconnect()
        backup_manager.close()
        logger.info("Бот остановлен")


if __name__ == '__main__':
    main()
