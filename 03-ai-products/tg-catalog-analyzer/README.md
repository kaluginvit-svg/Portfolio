# Каталогизация Telegram-канала в SQLite

Этот проект импортирует JSON-экспорт Telegram Desktop в SQLite-базу.

## Требования

- Python 3.8+
- Экспорт Telegram Desktop в формате JSON (`result.json`)

## Запуск окружения

Пример для PowerShell:

```
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Быстрый старт

1. Подготовьте экспорт Telegram Desktop (файл `result.json`).
2. Запустите скрипт:
   `python catalog_tg_posts.py`
3. Введите путь к папке экспорта и при необходимости путь к БД.
   По умолчанию имя БД формируется из названия папки экспорта.
   Пример пути:
   `C:\Users\Виталий\Downloads\Telegram Desktop\ИнфоПовод`
4. Скрипт создаст (или обновит) базу `tg_catalog.db` в текущей папке.

## Что импортируется

- `messages` из `result.json`
- Все ключи сообщений сохраняются в отдельных колонках (автоматически)
- Полный объект `media` сохраняется в колонке `media_json`
- Исходный JSON сообщения сохраняется в `raw_json`

## Структура таблицы

Таблица `posts` создаётся автоматически.

Основные поля:
- `channel_id`, `channel_name`
- `message_id` (PK вместе с `channel_id`)
- `text_flat` (склеенный текст)
- `text_json` (сырой текст из JSON)
- `media_json` (сырой media)
- `raw_json` (полный JSON сообщения)

## Примечания

- Текст сообщений может быть строкой, списком или объектами с форматированием —
  он аккуратно объединяется в обычный текст.
- Повторный импорт обновляет записи (используется `INSERT OR REPLACE`).

## Переменные окружения (OpenRouter)

Скрипт `check_openrouter.py` берёт значения из окружения через `os.getenv`:

- `OPENROUTER_API_KEY` — API ключ (обязательно)
- `OPENROUTER_MODEL` — модель (необязательно, по умолчанию `openai/gpt-4o-mini`)
- `OPENROUTER_TIMEOUT_SECONDS` — таймаут ответа в секундах (необязательно, по умолчанию `300`)

Пример для PowerShell:

```
setx OPENROUTER_API_KEY "ваш_ключ"
setx OPENROUTER_MODEL "openai/gpt-4o"
setx OPENROUTER_TIMEOUT_SECONDS "300"
```

## Анализ БД через OpenRouter

Скрипт `analyze_db_openrouter.py` отправляет краткую сводку БД и примеры сообщений
в OpenRouter и печатает ответ.

Пример:

```
python analyze_db_openrouter.py --db tg_catalog_ИнфоПовод.db --limit 60
```

## Анализ и рубрикация JSON через OpenRouter

Скрипт `analyze_json_rubrication.py` читает `result.json`, отправляет сводку и примеры
в OpenRouter и печатает ответ. Промпт можно ввести в терминале многострочно
(завершение — пустая строка).

Пример:

```
python analyze_json_rubrication.py --json result.json --limit 80
```
