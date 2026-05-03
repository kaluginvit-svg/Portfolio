# Telegram-бот с долговременной памятью (база)

## Виртуальное окружение (venv)

Создать venv:

```bash
python -m venv .venv
```

Активировать venv:

Windows (PowerShell):

```powershell
.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
source .venv/bin/activate
```

## Установка зависимостей

```bash
pip install -r requirements.txt
```

## Переменные окружения

1. Скопируйте `.env.example` в `.env`
2. Заполните значения в `.env`:
   - `PINECONE_API_KEY`
   - `PINECONE_INDEX_NAME`
   - `PROXYAPI_BASE_URL` (для OpenAI‑совместимого SDK: `https://openai.api.proxyapi.ru/v1` или `https://api.proxyapi.ru/openai/v1`)
   - `PROXYAPI_API_KEY`
   - `TELEGRAM_BOT_TOKEN`
