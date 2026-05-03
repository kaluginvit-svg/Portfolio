# Текст Для Сдачи

В проекте реализован Telegram AI-бот для командного чата на PyTelegramBotAPI, Haystack, OpenAI через proxyapi.ru и Pinecone.

Что реализовано:

- команды `/start_listening`, `/stop_listening`, `/status`, `/help`, `/ask`;
- запись сообщений командного чата в активной сессии;
- сохранение metadata автора, чата, времени, message id и session id;
- индексация сообщений через Haystack pipeline в Pinecone;
- поиск релевантного контекста через retrieval pipeline;
- ответы бота по вопросу или упоминанию в чате;
- итоговое summary после `/stop_listening`: резюме, позиции участников, решения, action items, открытые вопросы и рекомендация;
- конфигурация только через `.env`;
- проверка Pinecone dimension `3072` для `text-embedding-3-large`;
- SQLite-состояние сессий;
- логирование и обработка ошибок;
- README, demo checklist, архитектурная схема `architecture.png` и unit-тесты.

Проверки:

```bash
python -m compileall bot.py src tests
python -m pytest
```

Локальные тесты проходят: 6 passed.
