# Деплой на VPS (legacy: PM2 + rsync)

> **Рекомендуемый production-путь:** Docker + GHCR + Compose + Nginx — см. **[web/README.md](../web/README.md)** (раздел про Docker) и workflow **`.github/workflows/deploy.yml`**.

Приложение собирается в режиме **`output: "standalone"`** и выкладывается в каталог на сервере через **rsync** по **SSH**. Процесс перезапускается через **PM2**. Этот сценарий оставлен для обратной совместимости; автодеплой по push отключён (только **Run workflow** в GitHub Actions).

## Если корень репозитория — только папка `web`

Перенесите каталог **`.github`** внутрь `web` и в файлах workflow уберите префикс `web/`:

- удалите `defaults.working-directory: web` / `working-directory: ${{ env.APP_DIR }}`, выполняйте команды из корня;
- в шаге rsync укажите источник `.next/standalone/` вместо `web/.next/standalone/`;
- в `cache-dependency-path` укажите `package-lock.json`.

## Первичная настройка VPS

1. **Node.js 20+** (например, через [NodeSource](https://github.com/nodesource/distributions) или `nvm`).
2. **PM2** глобально: `npm i -g pm2`
3. Пользователь для деплоя (например `deploy`) и каталог, например `/var/www/svo-landing`:

   ```bash
   sudo mkdir -p /var/www/svo-landing
   sudo chown deploy:deploy /var/www/svo-landing
   ```

4. **SSH-ключ** только для деплоя (ed25519):

   ```bash
   ssh-keygen -t ed25519 -f ./github-actions-deploy -C "github-actions-svo"
   ```

   Публичный ключ добавьте в `~/.ssh/authorized_keys` пользователя на VPS.

5. На сервере создайте **`.env`** в каталоге деплоя (файл **не** копируется из GitHub — секреты только на VPS):

   ```env
   NODE_ENV=production
   PORT=3000
   TELEGRAM_BOT_TOKEN=
   TELEGRAM_CHAT_ID=
   CONTACT_TEXT=
   LEADS_STORAGE_MODE=file
   LEADS_FILE_PATH=./data/leads.json
   NEXT_PUBLIC_SITE_URL=https://svorazbor.ru
   ```

   PM2 подхватит переменные, если запускать с `--update-env` (workflow уже вызывает `reload ... --update-env`).  
   Либо один раз на сервере: `pm2 start ecosystem.config.cjs` после первого rsync и при необходимости настройте `ecosystem.config.cjs` с `env_file` (PM2 5.x) или экспортируйте переменные перед `pm2 start`.

6. **Первый запуск** вручную после первого успешного деплоя (или один раз с локальной машины залейте сборку):

   ```bash
   cd /var/www/svo-landing
   pm2 start ecosystem.config.cjs
   pm2 save
   pm2 startup
   ```

7. **Nginx** (пример прокси на порт 3000):

   ```nginx
   server {
     server_name svorazbor.ru;
     location / {
       proxy_pass http://127.0.0.1:3000;
       proxy_http_version 1.1;
       proxy_set_header Host $host;
       proxy_set_header X-Real-IP $remote_addr;
       proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
       proxy_set_header X-Forwarded-Proto $scheme;
     }
   }
   ```

## Секреты в GitHub

Репозиторий → **Settings → Secrets and variables → Actions**.

| Секрет | Описание |
|--------|----------|
| `VPS_HOST` | IP или домен VPS (`203.0.113.10` или `app.example.ru`) |
| `VPS_USER` | SSH-пользователь (`deploy`) |
| `VPS_SSH_PRIVATE_KEY` | **Полный** приватный ключ (включая `-----BEGIN ... KEY-----`) |
| `VPS_DEPLOY_PATH` | Абсолютный путь на сервере (`/var/www/svo-landing`), **без** завершающего `/` |
| `VPS_SSH_KNOWN_HOSTS` | *Опционально.* Вывод `ssh-keyscan -H ваш-хост` — надёжнее, чем автоматический `ssh-keyscan` в CI |

Опционально: в job деплоя в workflow можно указать `environment: production` в GitHub — тогда в **Environments** можно включить required reviewers и отдельные секреты.

## GitHub Actions

- **`CI`** (`.github/workflows/ci.yml`) — `lint` + `build` на push/PR в `main`/`master`.
- **`Deploy (Docker → GHCR → VPS)`** (`.github/workflows/deploy.yml`) — основной production-деплой; подробности в **[web/README.md](../web/README.md)**.
- **`Deploy to VPS (legacy PM2)`** (`.github/workflows/deploy-vps.yml`) — только **Run workflow** вручную: rsync + PM2.

Актуальная сводка по деплою — в **[web/README.md](../web/README.md)**.

## Проверка

1. Запушьте в `main`.
2. Вкладка **Actions** — успешный **Deploy to VPS**.
3. На сервере: `pm2 status`, откройте сайт в браузере.

## Лиды на диске

Убедитесь, что каталог для `LEADS_FILE_PATH` существует и доступен пользователю процесса (например `mkdir -p /var/www/svo-landing/data` и права на запись).
