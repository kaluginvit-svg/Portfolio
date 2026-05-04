# Чек-лист: Google Cloud и таблица

Полный текст ДЗ — на платформе курса; в репозитории — чек-лист ниже и сопутствующие `.md` в этой папке.

## 1. Google Cloud (сервисный аккаунт)

1. [Google Cloud Console](https://console.cloud.google.com/) — создать проект (например, «Excel Factory»).
2. **APIs & Services → Library** — включить **Google Sheets API**.
3. **APIs & Services → Credentials** — **Create credentials → Service account**.
4. Для сервисного аккаунта: роль на уровне проекта по заданию — **Owner** или **Editor** (как в уроке).
5. **Keys → Add key → JSON** — скачать ключ, сохранить как файл (например `service_account.json`).

**Важно:** не коммитьте в git JSON с `private_key`; используйте `.gitignore`.

## 2. Google Таблица

1. Создать таблицу (или использовать существующую).
2. **Настройки доступа** — добавить **email сервисного аккаунта** из поля `client_email` в JSON, роль **Редактор**.

**ID таблицы** — фрагмент URL: `https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit`.

## 3. Локальный запуск

См. [README.md](README.md) в этой папке.
