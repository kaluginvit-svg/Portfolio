# Учебный проект: пользователи и пароли (рефакторинг «плохого» кода)

Демонстрация разделения слоёв, безопасной работы с SQLite и хранения паролей (PBKDF2). Исходная история проблем и исправлений описана в [bad_code_audit.md](bad_code_audit.md).

## Требования

- **Python 3.9+** (используется `typing.Optional` и импорты модулей из каталога проекта).
- **Зависимости**: [Flask](https://flask.palletsprojects.com/) и [Gunicorn](https://gunicorn.org/) (для Docker и продакшена). Установка: `pip install -r requirements.txt`.

## Структура проекта

| Файл | Назначение |
|------|------------|
| `api.py` | Публичный API: `add_user`, `store_password` — точка входа для скриптов, тестов и HTTP. |
| `app.py` | Flask: маршруты вызывают только `api`, без прямого доступа к SQLite/файлу паролей. |
| `users_repository.py` | Работа с SQLite: вставка пользователя (`insert_user`). |
| `password_storage.py` | Запись хеша пароля в файл (`append_password_hash`). |
| `settings.py` | Пути к БД и файлу паролей, параметры PBKDF2. |
| `bad_code.py` | Совместимость со старыми импортами `from bad_code import ...` (реэкспорт из `api`). |
| `bad_code_audit.md` | Аудит исходных антипаттернов и архитектура слоёв. |
| `go-server/` | Тот же REST API на **Go** (SQLite + PBKDF2). Инструкции: [go-server/README.md](go-server/README.md). |
| `openapi.yaml` | Контракт HTTP API в формате **OpenAPI 3.1** (общий для Flask и Go). |
| `DOCKER_HUB_AND_SERVER.md` | Публикация образа в **Docker Hub** и запуск на сервере (подробно). |
| `Dockerfile`, `docker-compose.yml` | Контейнер с **Gunicorn** + Flask; том для SQLite и файла паролей. |
| `scripts/init_db.py` | Создание таблицы `users` при старте контейнера / первом запуске. |
| `scripts/check_api.py` | Проверка всех сценариев эндпоинтов (см. раздел Docker). |

Рабочие файлы данных (создаются при работе): `users.db`, `passwords.txt` — пути задаются в `settings.py` или переменными окружения **`DB_PATH`** и **`PASSWORDS_FILE`** (удобно в Docker).

## Установка зависимостей

```text
pip install -r requirements.txt
```

Запуск кода выполняйте из **каталога проекта**, чтобы импорты `import api`, `import settings` находили модули:

```text
cd "путь\к\Уроки с AI_3 (кодинг)"
py -3 -c "import api; print(api.__all__)"
```

## Запуск веб-сервера (Flask)

После `pip install -r requirements.txt` и создания таблицы `users` (см. ниже):

```text
cd "путь\к\Уроки с AI_3 (кодинг)"
set FLASK_APP=app.py
flask run
```

В PowerShell вместо `set` используйте `$env:FLASK_APP = "app.py"`. Либо без переменной окружения:

```text
py -3 -m flask --app app run
```

Или напрямую: `py -3 app.py` (включён режим `debug` для разработки).

| Метод | Путь | Описание |
|--------|------|----------|
| GET | `/health` | Проверка: `{"status":"ok"}`. |
| POST | `/users` | Регистрация. Тело JSON: `name` (обязательно), `tags` (массив, опционально), `password` (строка, опционально). Ответ `201`: `{"id": <int>}`. |

Пример запроса:

```text
curl -X POST http://127.0.0.1:5000/users -H "Content-Type: application/json" -d "{\"name\":\"Alice\",\"tags\":[\"student\"],\"password\":\"secret\"}"
```

## Docker (локально и на сервере)

Нужны [Docker](https://docs.docker.com/get-docker/) и плагин Compose (часто входит в Docker Desktop).

Сборка и запуск в фоне (порт **5000**, SQLite и `passwords.txt` в именованном томе `app_data`):

```text
docker compose up --build -d
```

Проверка всех сценариев API с хоста (пока контейнер доступен на `127.0.0.1:5000`):

```text
python scripts/check_api.py
```

Другой базовый URL (например Go-сервер на 8080):

```text
set API_BASE=http://127.0.0.1:8080
python scripts/check_api.py
```

Остановка без удаления данных: `docker compose stop`. Полная остановка с удалением контейнеров: `docker compose down` (том `app_data` по умолчанию **сохраняется**).

Сборка образа без Compose:

```text
docker build -t userserver-web .
docker run --rm -p 5000:5000 -e DB_PATH=/app/data/users.db -e PASSWORDS_FILE=/app/data/passwords.txt -v app_data:/app/data userserver-web
```

В контекст сборки не попадает `go-server` (см. `.dockerignore`), чтобы образ оставался небольшим.

**Публикация образа в Docker Hub и запуск на VPS:** пошаговое руководство — [DOCKER_HUB_AND_SERVER.md](DOCKER_HUB_AND_SERVER.md).

## Инициализация базы данных

Без Docker таблица **не** создаётся автоматически (кроме сценария ниже). Перед первым вызовом `add_user` создайте схему, например в [DB Browser for SQLite](https://sqlitebrowser.org/) или из консоли:

```sql
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    tags TEXT NOT NULL
);
```

При необходимости добавьте индексы и ограничения под вашу модель данных.

Вручную из каталога проекта можно выполнить: `python scripts/init_db.py` (учитывает `DB_PATH` / `PASSWORDS_FILE`).

## Публичный API (`api.py`)

### `add_user(name: str, tags: Optional[list] = None) -> int`

Вставляет пользователя в `users.db`. К переданному списку тегов внутри добавляется строка `"new"` (исходный список вызывающего кода не изменяется). Теги сохраняются как JSON в колонке `tags`. Возвращает целочисленный `id` вставленной строки.

### `store_password(user_id: int, password: str) -> None`

Добавляет в конец `passwords.txt` строку с PBKDF2-SHA256: соль, число итераций и производное ключевое значение (формат: `user_id:salt_hex:iterations:dk_hex`).

Проверка пароля при входе в код **не реализована** — её нужно добавить отдельно (чтение соли и сравнение через `hmac.compare_digest`).

## Конфигурация (`settings.py`)

| Переменная | Описание |
|------------|----------|
| `DB_PATH` | Путь к файлу SQLite (строка). |
| `PASSWORDS_FILE` | `Path` к файлу с хешами. |
| `SALT_BYTES` | Длина соли в байтах. |
| `ITERATIONS` | Число итераций PBKDF2. |

## Безопасность и ограничения

- Запросы к БД параметризованы (защита от SQL-инъекций).
- Пароли не хранятся в открытом виде; используется PBKDF2-HMAC-SHA256 со случайной солью.
- Хранение хешей в **текстовом файле** подходит только для учебных целей; в продакшене обычно используют таблицу в БД и единую политику резервного копирования.
- Секреты не должны попадать в репозиторий; при появлении `.env` не коммитьте реальные значения (см. `.gitignore` при необходимости).

## Дальнейшее развитие

- Вынести создание таблицы в функцию `init_db()` или миграции.
- Добавить аутентификацию по паролю, rate limiting, HTTPS в продакшене.
- Добавить тесты и при необходимости `requirements-dev.txt` (pytest и т.д.).
