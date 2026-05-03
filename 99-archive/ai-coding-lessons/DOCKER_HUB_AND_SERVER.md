# Публикация образа в Docker Hub и запуск на сервере

Пошаговое руководство для учебного проекта. В репозитории **два** независимых `Dockerfile`:

| Образ | Где лежит Dockerfile | Что внутри | Типичный порт |
|--------|----------------------|------------|----------------|
| **Python (Flask + Gunicorn)** | корень проекта `(кодинг)/` | `app.py`, SQLite, `passwords.txt` | **5000** |
| **Go** | каталог `go-server/` | бинарник `userserver` | **8080** |

На Docker Hub удобно завести **два репозитория** (например `yourname/userserver-web` и `yourname/userserver-go`) или один репозиторий с **разными тегами** (`:python`, `:go`). Ниже — вариант с **двумя репозиториями** и тегом **`latest`**.

---

## Часть 1. Подготовка Docker Hub

1. Зайдите на [hub.docker.com](https://hub.docker.com/) и создайте аккаунт (или войдите).
2. **Create repository**:
   - **Repository name**: например `userserver-web` (для Python) и отдельно `userserver-go` (для Go).
   - **Visibility**: Public (для учебы достаточно) или Private (платные лимиты/настройки).
3. Запомните **имя пользователя** Docker Hub (например `ivanov`) — оно участвует в полном имени образа:  
   `ivanov/userserver-web:latest`.

Полное имя образа всегда: **`docker.io/<username>/<repository>:<tag>`**  
Часто пишут короче: **`<username>/<repository>:<tag>`**.

---

## Часть 2. На вашем компьютере (Windows): сборка и отправка

Установите [Docker Desktop](https://www.docker.com/products/docker-desktop/), войдите в аккаунт (опционально через `docker login`).

Откройте PowerShell. Замените **`YOUR_USER`** на ваш логин Docker Hub.

### 2.1. Вход в Docker Hub из терминала

```powershell
docker login
```

Введите логин и **Access Token** (рекомендуется) или пароль.  
Токен: Docker Hub → Account Settings → Security → New Access Token.

### 2.2. Образ Python (Flask) из **корня** проекта

Перейдите в папку, где лежат `Dockerfile`, `app.py`, `requirements.txt`:

```powershell
cd "C:\_Рабочая_папка\ZeroCoder\Обучение\Профессия_Вайб-кодер\Уроки\Уроки с AI_3 (кодинг)"
```

Сборка с **правильным тегом** под Docker Hub:

```powershell
docker build -t YOUR_USER/userserver-web:latest .
```

Проверка локально (порт **5000**):

```powershell
docker run --rm -p 5000:5000 -v test_py_data:/app/data YOUR_USER/userserver-web:latest
```

В браузере: `http://127.0.0.1:5000/` или `/health`. Остановка: **Ctrl+C**.

Отправка в реестр:

```powershell
docker push YOUR_USER/userserver-web:latest
```

После успешного push образ появится на странице репозитория на hub.docker.com.

### 2.3. Образ Go из каталога `go-server`

```powershell
cd "C:\_Рабочая_папка\ZeroCoder\Обучение\Профессия_Вайб-кодер\Уроки\Уроки с AI_3 (кодинг)\go-server"
```

```powershell
docker build -t YOUR_USER/userserver-go:latest .
```

Проверка (порт **8080**):

```powershell
docker run --rm -p 8080:8080 -v test_go_data:/app/data YOUR_USER/userserver-go:latest
```

```powershell
docker push YOUR_USER/userserver-go:latest
```

### 2.4. Версионирование (рекомендуется)

Не полагайтесь только на `latest`. После изменений кода:

```powershell
docker build -t YOUR_USER/userserver-web:v1.0.1 .
docker push YOUR_USER/userserver-web:v1.0.1
docker push YOUR_USER/userserver-web:latest
```

На сервере тогда можно зафиксировать версию `v1.0.1` для воспроизводимости.

---

## Часть 3. Сервер (Linux, пример Ubuntu 22.04)

### 3.1. Установка Docker и Compose

По официальной инструкции: [Install Docker Engine on Ubuntu](https://docs.docker.com/engine/install/ubuntu/).

Кратко:

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo usermod -aG docker $USER
```

Выйдите из SSH и зайдите снова (или `newgrp docker`), чтобы команда `docker` работала без `sudo`.

### 3.2. Скачать образ с Docker Hub

Замените `YOUR_USER`:

```bash
docker pull YOUR_USER/userserver-go:latest
```

или для Python:

```bash
docker pull YOUR_USER/userserver-web:latest
```

Образ **публичный** — `docker login` на сервере не нужен. **Приватный** — сначала `docker login`.

### 3.3. Запуск контейнера (Go, порт 8080)

```bash
docker run -d \
  --name userserver-go \
  --restart unless-stopped \
  -p 8080:8080 \
  -v go_app_data:/app/data \
  YOUR_USER/userserver-go:latest
```

- **`-d`** — в фоне.  
- **`--restart unless-stopped`** — после перезагрузки сервера контейнер поднимется сам.  
- **`-p 8080:8080`** — снаружи порт 8080 на хосте.  
- **`-v go_app_data:/app/data`** — том для SQLite и файла паролей (данные сохраняются).

Проверка:

```bash
curl http://127.0.0.1:8080/health
```

Логи:

```bash
docker logs -f userserver-go
```

Остановка и удаление:

```bash
docker stop userserver-go
docker rm userserver-go
```

### 3.4. Запуск контейнера (Python, порт 5000)

```bash
docker run -d \
  --name userserver-web \
  --restart unless-stopped \
  -p 5000:5000 \
  -v py_app_data:/app/data \
  YOUR_USER/userserver-web:latest
```

```bash
curl http://127.0.0.1:5000/health
```

---

## Часть 4. Файрвол и доступ из интернета

1. **На сервере** откройте только нужный порт, например:

   ```bash
   sudo ufw allow 8080/tcp
   sudo ufw enable
   sudo ufw status
   ```

2. В панели **облачного провайдера** (AWS, Timeweb, Selectel и т.д.) в **Security Group / Firewall** разрешите входящий TCP на тот же порт на **публичный IP** сервера.

3. Обращение с вашего ПК: `http://SERVER_IP:8080/health`.

**Важно:** для продакшена лучше не светить приложение напрямую на мир, а поставить **Nginx** или **Caddy** с HTTPS и проксировать на `127.0.0.1:8080`. Это отдельная тема (Let’s Encrypt, домен).

---

## Часть 5. Docker Compose на сервере с образом из Hub

Локально у вас `docker-compose.yml` с **`build: .`**. На сервере обычно **не клонируют репозиторий для сборки**, а тянут готовый образ.

Создайте на сервере файл `docker-compose.yml` (пример для **Go**):

```yaml
services:
  web:
    image: YOUR_USER/userserver-go:latest
    ports:
      - "8080:8080"
    environment:
      DB_PATH: /app/data/users.db
      PASSWORDS_FILE: /app/data/passwords.txt
    volumes:
      - app_data:/app/data
    restart: unless-stopped

volumes:
  app_data:
```

Запуск:

```bash
docker compose pull
docker compose up -d
```

Обновление после нового `push` на Hub:

```bash
docker compose pull
docker compose up -d
```

---

## Часть 6. Типичный цикл «изменил код → обновил сервер»

1. На ПК: правки кода → пересборка → тег (например `v1.0.2`) → `docker push YOUR_USER/userserver-go:v1.0.2` и при необходимости `...:latest`.
2. На сервере: `docker pull YOUR_USER/userserver-go:v1.0.2` → перезапуск контейнера или `docker compose up -d` с тем же тегом в `image:`.

---

## Часть 7. Безопасность (краткий чеклист)

- Не храните пароли Docker Hub в репозитории; для CI используйте **secrets**.
- Учебный API **не** аутентифицирует клиентов — не выкладывайте его в открытый интернет без **HTTPS**, **ограничения по IP** или **VPN**.
- Резервные копии: том Docker (`docker volume inspect`) — продумайте бэкап каталога данных или `users.db` / `passwords.txt` с сервера.

---

## Часть 8. Частые проблемы

| Симптом | Что проверить |
|--------|----------------|
| `denied: requested access to the resource is denied` | Правильный ли тег `YOUR_USER/имя-репозитория`, выполнен ли `docker login`. |
| На сервере `Connection refused` | Запущен ли контейнер (`docker ps`), открыт ли порт в UFW и у провайдера. |
| Старый код на сервере | Сделали ли `docker pull` нового тега и перезапуск (`docker compose up -d --force-recreate`). |
| Данные пропали после `docker run` без `-v` | Нужен **именованный том** или **bind-mount** на каталог. |

---

## Краткая шпаргалка команд

```text
# Локально (после сборки)
docker login
docker tag local-image YOUR_USER/repo:tag   # если нужно переименовать
docker push YOUR_USER/repo:tag

# Сервер
docker pull YOUR_USER/repo:tag
docker run -d --restart unless-stopped -p 8080:8080 -v data:/app/data YOUR_USER/repo:tag
```

Если нужен один сценарий (только Python или только Go), достаточно повторить шаги для одного образа и одного порта.
