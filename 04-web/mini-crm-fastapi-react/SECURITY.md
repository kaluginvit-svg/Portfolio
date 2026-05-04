# Секреты и публичный репозиторий

Проект рассчитан на **публикацию в портфолио** без утечки ключей.

## Что никогда не коммитить

- JSON **OAuth client** из Google Cloud (`client_secret*.json` с реальным `client_secret`).
- **`config/google_settings.json`** — путь к секрету и ID папки Drive (локальные данные).
- **`data/google_token.pickle`** / **`data/google_token.json`** — пользовательский OAuth-токен.
- **`.env`** с любыми паролями и ключами.
- **SQLite** `data/*.db` с вашими данными (опционально для портфеля не нужна).

Примеры без секретов лежат рядом с суффиксом **`.example`** (`google_integration/client_secret.example.json`, `config/google_settings.example.json`).

## После клона репозитория

1. Скопируйте `google_integration/client_secret.example.json` → `google_integration/client_secret.json` и подставьте значения из [Google Cloud Console](https://console.cloud.google.com/) (OAuth 2.0 Client ID, тип *Web application*).
2. Скопируйте `config/google_settings.example.json` → `config/google_settings.json`, укажите путь к своему `client_secret.json` и **ID родительской папки** на Drive (фрагмент URL после `folders/`).
3. Скопируйте `.env.example` → `.env` при необходимости.
4. Запустите API, откройте UI **Настройки Google** и при необходимости скорректируйте пути; выполните **«Войти через Google»**.

## Если секрет уже попал в git

1. Удалите файл из истории (`git filter-repo` / BFG) или создайте **новый** репозиторий без старых коммитов.
2. В Google Cloud **сбросьте Client secret** для OAuth-клиента и выпустите новый JSON.
3. Ограничьте доступ: смените пароли, отзовите refresh-токен, пересоздайте при необходимости.
