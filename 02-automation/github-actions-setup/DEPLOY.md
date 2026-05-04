# Автоматический деплой (GHCR)

Две джобы: сборка и пуш образа в **GitHub Container Registry (ghcr.io)**, затем деплой на сервер по SSH — на сервере образ скачивается из GHCR и запускается.

---

## Обзор

| Джоба | Назначение |
|-------|-------------|
| **build-and-push** | Сборка Docker-образа и публикация в GHCR (`ghcr.io/<owner>/<repo>`) |
| **deploy** | Подключение по SSH, вход в GHCR, загрузка образа, запуск контейнера |

Для пуша в GHCR используется встроенный `GITHUB_TOKEN`. Деплой выполняется только после успешного завершения первой джобы. Вторая джоба не запускается, если не задан секрет **SSH_HOST**.

---

## Когда запускается

- **При пуше в ветку `main`** — сборка → пуш в GHCR → деплой на сервер.
- **Вручную** — **Actions** → **Build and Deploy** → **Run workflow**.

---

## Джоба 1: Сборка и пуш

1. Checkout репозитория.
2. Вход в **GitHub Container Registry** (`ghcr.io`) по встроенному `GITHUB_TOKEN`.
3. Формирование тегов: `latest` (при пуше в `main`) и по SHA коммита.
4. Сборка образа и пуш в GHCR: **`ghcr.io/<owner>/<repo>:latest`** (owner/repo — из имени репозитория).

---

## Джоба 2: Деплой по SSH

1. Подключение к серверу по SSH (секреты `SSH_HOST`, `SSH_USER`, `SSH_PRIVATE_KEY`, при необходимости `SSH_PORT`).
2. На сервере:
   - **Вход в GHCR** — `docker login ghcr.io` с `GHCR_USERNAME` и `GHCR_TOKEN` (PAT с правом **read:packages**).
   - **Загрузка образа** — `docker pull ghcr.io/<owner>/<repo>:latest`.
   - Остановка и удаление старого контейнера `time-api`.
   - **Запуск** — `docker run -d --name time-api -p 8080:8080 --restart unless-stopped ...`.
   - **Очистка** — `docker image prune -f`.

Приложение доступно на сервере по порту **8080**.

---

## Секреты репозитория

**Settings** → **Secrets and variables** → **Actions**.

| Секрет | Обязательный | Описание |
|--------|--------------|----------|
| `GHCR_TOKEN` | Да | GitHub PAT (classic) с правом **read:packages** — чтобы сервер мог скачивать образ из GHCR. |
| `GHCR_USERNAME` | Да | Логин GitHub пользователя, которому принадлежит токен (владелец PAT). |
| `SSH_HOST` | Да* | IP или hostname сервера. *Деплой не запускается, если не задан. |
| `SSH_USER` | Да | Пользователь для SSH. |
| `SSH_PRIVATE_KEY` | Да | Приватный SSH-ключ целиком. |
| `SSH_PORT` | Нет | Порт SSH (по умолчанию 22). |

Для пуша в GHCR отдельный секрет не нужен — используется встроенный `GITHUB_TOKEN`.

---

## Требования к серверу

- Установлен **Docker**.
- Пользователь из `SSH_USER` может запускать `docker` (например, в группе `docker`).
- В `~/.ssh/authorized_keys` добавлен публичный ключ, соответствующий `SSH_PRIVATE_KEY`.
- Открыт порт SSH и при необходимости порт **8080**.

---

## Первая настройка

1. **GitHub:** создать Classic PAT с правом **read:packages** ([Tokens (classic)](https://github.com/settings/tokens/new)), сохранить в секрет `GHCR_TOKEN`, логин — в `GHCR_USERNAME`.
2. **Сервер:** установить Docker, настроить пользователя и SSH-ключ, добавить пользователя в группу `docker`.
3. **GitHub:** добавить секреты `GHCR_TOKEN`, `GHCR_USERNAME`, `SSH_HOST`, `SSH_USER`, `SSH_PRIVATE_KEY` (и при необходимости `SSH_PORT`).
4. Запустить workflow (пуш в `main` или **Run workflow**), проверить логи и на сервере — `docker ps`, `curl http://localhost:8080/health`.

---

## Возможные проблемы

| Симптом | Что проверить |
|--------|----------------|
| Ошибка при SSH | `SSH_HOST`, `SSH_USER`, `SSH_PRIVATE_KEY`, доступность сервера и порта. |
| Ошибка при push в GHCR | Права job: `packages: write`. Репозиторий и пакет привязаны к одному владельцу. |
| `denied` при pull на сервере | PAT с правом **read:packages** (classic). `GHCR_USERNAME` — логин владельца токена. Для приватного пакета — пакет доступен этому пользователю. |
| `Cannot connect to the Docker daemon` | Пользователь `SSH_USER` в группе `docker`, после этого — новый сеанс SSH. |

Имя контейнера и порт заданы в `script` джобы **deploy** в `.github/workflows/deploy.yml`. Образ — `ghcr.io/<owner>/<repo>` (как в переменной `IMAGE_NAME`).
