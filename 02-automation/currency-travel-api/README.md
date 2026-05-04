# Валюта в путешествиях (Telegram + API курсов)

**Что это:** Telegram-бот и утилиты для запроса **кросс-курсов** через [exchangerate.host](https://exchangerate.host) (ключ в `.env`: `EXCHANGERATE_API_KEY`).

**Стек:** Python, python-telegram-bot / aiogram (см. код в репозитории), `requests`, SQLite при необходимости.

**Запуск:** создайте `.env` по образцу (если есть `.env.example`), установите `requirements.txt`, запустите точку входа бота (`bot.py`).

**Статус:** учебно-продуктовый мини-сервис для демонстрации работы с внешним FX API и ботом.
