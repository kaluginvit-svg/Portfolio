# HTTP-сервер на Go (аналог Flask `app.py`)

Тот же контракт, что у Python-версии: SQLite `users.db`, файл `passwords.txt` с PBKDF2-SHA256, маршруты `GET /health` и `POST /users`.

## Требования

- [Go](https://go.dev/dl/) **1.21+** (установите и убедитесь, что `go version` работает в терминале).
- Сеть для первой загрузки модулей (`go mod download` выполняется автоматически при сборке).

## Установка зависимостей и сборка

Находясь в каталоге `go-server` (рядом с `go.mod`):

```text
go mod tidy
go build -o userserver ./cmd/userserver
```

На Windows: `go build -o userserver.exe ./cmd/userserver`.

Запуск без бинарника:

```text
go run ./cmd/userserver
```

## Docker

Имя каталога — **`go-server`** (через дефис), не `go_server`.

При старте сервер сам создаёт таблицу `users`, если её ещё нет (удобно в контейнере). Пути к данным задаются **`DB_PATH`** и **`PASSWORDS_FILE`**.

**Сборка из каталога `go-server`:**

```text
cd go-server
docker build -t go-server .
docker run --rm -p 8080:8080 -v go_app_data:/app/data go-server
```

**Сборка из корня репозитория** (родительская папка содержит `go-server/`):

```text
docker build -f go-server/Dockerfile -t go-server go-server
docker run --rm -p 8080:8080 -v go_app_data:/app/data go-server
```

В образе по умолчанию: `DB_PATH=/app/data/users.db`, `PASSWORDS_FILE=/app/data/passwords.txt`.

Проверка тех же эндпоинтов с хоста (скрипт лежит в **корне** Python-проекта, на уровень выше `go-server`):

```text
set API_BASE=http://127.0.0.1:8080
python scripts/check_api.py
```

## Переменные окружения

| Переменная | Значение по умолчанию | Описание |
|------------|------------------------|----------|
| `DB_PATH` | `users.db` | Путь к файлу SQLite (как в Python `settings.py`). |
| `PASSWORDS_FILE` | `passwords.txt` | Путь к файлу с хешами паролей. |
| `HTTP_ADDR` | (см. ниже) | Полный адрес прослушивания, например `:5000` или `127.0.0.1:8080`. Имеет приоритет над `PORT`. |
| `PORT` | не задан | Если `HTTP_ADDR` пустой, к порту добавляется двоеточие: `5000` → `:5000`. |
| (если оба пусты) | `:8080` | Как у многих примеров на Go (Flask по умолчанию использует 5000 — задайте `PORT=5000` при необходимости). |

Примеры:

```text
set HTTP_ADDR=:5000
userserver.exe
```

PowerShell:

```text
$env:HTTP_ADDR = ":5000"; .\userserver.exe
```

## База данных

При запуске бинарника таблица `users` создаётся сама (`CREATE TABLE IF NOT EXISTS` в `internal/repository/migrate.go`), отдельный шаг не обязателен.

Файл `users.db` появится по пути из **`DB_PATH`** (по умолчанию — в **текущей рабочей директории**).

Справочно — тот же SQL, что в [schema.sql](schema.sql):

```sql
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    tags TEXT NOT NULL
);
```

Можно выполнить через [DB Browser for SQLite](https://sqlitebrowser.org/) или:

```text
sqlite3 users.db ".read schema.sql"
```

(если установлен `sqlite3` в PATH).

## API

### `GET /health`

Ответ `200`, тело JSON:

```json
{"status":"ok"}
```

### `POST /users`

Заголовок: `Content-Type: application/json`.

Тело:

| Поле | Обязательность | Описание |
|------|------------------|----------|
| `name` | да, непустая строка | Имя пользователя. |
| `tags` | нет | Массив строк; к копии списка на сервере добавляется `"new"`, в БД сохраняется JSON. |
| `password` | нет | Строка; если не пустая, в конец `passwords.txt` дописывается строка `user_id:salt_hex:iterations:dk_hex` (PBKDF2-HMAC-SHA256, 390000 итераций, соль 16 байт — как в Python). |

Успех: `201 Created`, тело:

```json
{"id": 1}
```

Ошибки валидации: `400`, пример:

```json
{"error":"поле name (строка) обязательно"}
```

Ошибка БД/файла: `500`, пример:

```json
{"error":"не удалось сохранить пользователя"}
```

Неверный HTTP-метод для пути: `405`.

## Примеры запросов

Проверка живости (порт по умолчанию 8080):

```text
curl -s http://127.0.0.1:8080/health
```

Создание пользователя с тегами и паролем:

```text
curl -s -X POST http://127.0.0.1:8080/users -H "Content-Type: application/json" -d "{\"name\":\"Alice\",\"tags\":[\"student\"],\"password\":\"secret\"}"
```

Только имя:

```text
curl -s -X POST http://127.0.0.1:8080/users -H "Content-Type: application/json" -d "{\"name\":\"Bob\"}"
```

## Файлы данных

| Файл | Назначение |
|------|------------|
| `users.db` | SQLite (таблица `users`). |
| `passwords.txt` | Построчно хеши паролей в формате, совместимом с Python `password_storage.py`. |

Запускайте сервер из одной и той же рабочей директории, чтобы пути к файлам не «прыгали».

## Соответствие Python-проекту

- Драйвер SQLite без CGO: [modernc.org/sqlite](https://pkg.go.dev/modernc.org/sqlite) (удобно на Windows без компилятора C).
- Криптография: `golang.org/x/crypto/pbkdf2` + `crypto/sha256` — те же параметры, что в `settings.py` (`SALT_BYTES`, `ITERATIONS`).

## Структура проекта (модульность)

```text
go-server/
  Dockerfile                 — образ на Alpine (multi-stage)
  cmd/userserver/main.go     — точка входа: БД, wiring, ListenAndServe
  internal/
    config/                  — пути (в т.ч. DB_PATH, PASSWORDS_FILE), PBKDF2, ListenAddr из env
    models/                  — DTO JSON (запросы/ответы API)
    jsonutil/                — разбор json.RawMessage (name, tags, password)
    httputil/                — JSON-ответы, проверка HTTP-метода
    handlers/                — маршруты: health, create user → вызов service
    service/                 — сценарий создания пользователя (тег "new", БД, пароль)
    repository/              — SQLite users, migrate.go (CREATE TABLE), файл password hashes
    passwordhash/            — одна строка PBKDF2 для файла (как в Python)
  go.mod
  schema.sql
  README.md
```

Пакет `internal/...` не предназначен для импорта внешними модулями (соглашение Go). Бизнес-правила сосредоточены в `service`, транспорт — в `handlers`.

После сборки рядом с `go-server` появится бинарник `userserver` / `userserver.exe` — он уже перечислен в `.gitignore`.

## Дополнительно: язык Go с нуля (на фоне Python)

Вводный текст: [GO_INTRO_RU.md](GO_INTRO_RU.md) — зачем Go рядом с Python, где его применяют, разбор синтаксиса и идей на примере этого проекта.
