import os
from dataclasses import dataclass
from dotenv import load_dotenv

# Загружаем переменные окружения из файла .env (если он существует)
# Это позволяет удобно хранить настройки в файле вместо системных переменных
load_dotenv()


@dataclass(frozen=True)
class Settings:
    """
    Настройки бота, загружаемые из переменных окружения.
    BOT_TOKEN - обязательная переменная (токен бота от BotFather)
    DATABASE_PATH - опциональная (путь к файлу БД, по умолчанию tasks.db)
    LOG_LEVEL - опциональная (уровень логирования, по умолчанию INFO)
    """
    bot_token: str
    database_path: str
    log_level: str


def _load_settings() -> Settings:
    # Обязательная переменная - токен бота
    token = os.getenv("BOT_TOKEN")
    if not token:
        error_message = (
            "\n❌ ОШИБКА: Переменная окружения BOT_TOKEN не установлена или не видна.\n\n"
            "📝 Способы установки BOT_TOKEN:\n\n"
            "1️⃣  Использование файла .env (РЕКОМЕНДУЕТСЯ):\n"
            "   Создайте файл .env в корне проекта и добавьте:\n"
            "   BOT_TOKEN=ваш_токен_от_BotFather\n\n"
            "2️⃣  Временная установка в PowerShell (только для текущей сессии):\n"
            "   $env:BOT_TOKEN=\"ваш_токен_от_BotFather\"\n\n"
            "3️⃣  Постоянная установка в системе (для всех сессий):\n"
            "   [System.Environment]::SetEnvironmentVariable('BOT_TOKEN', 'ваш_токен_от_BotFather', 'User')\n"
            "   ⚠️ После установки перезапустите PowerShell!\n\n"
            "💡 Рекомендуется использовать файл .env - это удобнее и безопаснее.\n"
            "   Бот автоматически загрузит переменные из файла .env при запуске.\n\n"
            "🔍 Проверить установленную переменную:\n"
            "   echo $env:BOT_TOKEN\n\n"
            "🤖 Чтобы получить токен, создайте бота через @BotFather в Telegram:\n"
            "   /newbot → следуйте инструкциям → скопируйте токен\n"
        )
        raise RuntimeError(error_message)
    
    # Опциональные переменные с значениями по умолчанию
    database_path = os.getenv("DATABASE_PATH", "tasks.db")
    log_level = os.getenv("LOG_LEVEL", "INFO")
    
    return Settings(
        bot_token=token,
        database_path=database_path,
        log_level=log_level,
    )


settings = _load_settings()
