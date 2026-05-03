# Telegram-бот болталка

Простой бот на aiogram 3 с развёртыванием в Docker.

## Локальный запуск

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
# Создайте .env с BOT_TOKEN=...
python main.py
```

## Запуск в Docker

```powershell
docker-compose up --build
```

Остановка: `docker-compose down`.

Логи: stdout (`docker logs tg-chat-bot`), файл `logs/bot.log`, и [Better Stack / Logtail](https://betterstack.com/docs/logs/python/) при наличии `LOGTAIL_SOURCE_TOKEN`.

## Публикация образа в Docker Hub

1. **Войти в Docker Hub:**
   ```powershell
   docker login
   ```
   Введите логин и пароль (или токен) Docker Hub.

2. **Задать имя образа** — в корне проекта создайте/дополните `.env`:
   ```env
   DOCKERHUB_USER=ваш_логин_на_dockerhub
   BOT_TOKEN=ваш_токен_бота
   ```
   Либо при сборке:
   ```powershell
   $env:DOCKERHUB_USER="ваш_логин"
   docker-compose build
   ```

3. **Собрать и отправить образ:**
   ```powershell
   docker-compose build
   docker push ваш_логин/tg-chat-bot:latest
   ```
   Либо без docker-compose:
   ```powershell
   docker build -t ваш_логин/tg-chat-bot:latest .
   docker push ваш_логин/tg-chat-bot:latest
   ```

4. На другом сервере образ можно запускать так:
   ```bash
   docker run -d --restart unless-stopped --env-file .env ваш_логин/tg-chat-bot:latest
   ```

## Переменные окружения

| Переменная       | Описание                          |
|------------------|-----------------------------------|
| `BOT_TOKEN`      | Токен бота от @BotFather          |
| `DOCKERHUB_USER` | Логин Docker Hub (для имени образа) |
| `LOG_DIR`        | Каталог для логов (по умолчанию `logs`) |
| `LOGTAIL_SOURCE_TOKEN` | HTTP source token Better Stack (опционально) |
