# Demo Checklist

Используйте этот сценарий после заполнения `.env` реальными ключами и добавления бота в Telegram-группу.

## Перед Запуском

- `.env` заполнен значениями из `.env.example`.
- `EMBEDDING_MODEL=text-embedding-3-large`.
- `PINECONE_INDEX_DIMENSION=3072`.
- Pinecone index существует с dimension `3072` или будет создан автоматически.
- У Telegram-бота отключен Privacy Mode через BotFather.
- Бот добавлен в тестовую группу.

## Команды

```bash
pip install -r requirements.txt
python bot.py
```

## Сценарий В Telegram

1. Отправить `/help`.
2. Отправить `/start_listening`.
3. Отправить 8-12 сообщений от двух участников на рабочую тему.
4. Отправить `/status`.
5. Отправить `/ask Какие аргументы были за вариант A и вариант B?`.
6. Упомянуть бота: `@bot_username Что думаешь?`.
7. Отправить `/stop_listening`.
8. Проверить, что итог содержит резюме, позиции участников, решения, action items и открытые вопросы.

## Скриншоты Для Сдачи

- Структура проекта.
- Терминал с запущенным `python bot.py`.
- Telegram-команды `/start_listening`, `/status`, `/ask`, `/stop_listening`.
- Ответ бота по контексту.
- Итоговое summary.
- Pinecone index/namespace со свежими records.
