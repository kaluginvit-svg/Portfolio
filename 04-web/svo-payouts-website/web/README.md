# Лендинг svorazbor.ru — выплаты семье погибшего участника СВО

**Release candidate** для production: **Next.js 15 (App Router)**, **TypeScript**, **Tailwind CSS v4**, UI в духе **shadcn/ui** (Radix + CVA), **Framer Motion**, **React Hook Form** + **Zod**.

Публичный прод-домен: **`https://svorazbor.ru`**. Локальная разработка — каталог **`web/`**.

## Быстрый старт

```bash
cd web
cp .env.example .env
npm install
npm run dev
```

Откройте [http://localhost:3000](http://localhost:3000).

### Launch checklist (перед / сразу после деплоя)

| Шаг | Действие |
|-----|----------|
| **Env** | На сервере: **`NEXT_PUBLIC_SITE_URL=https://svorazbor.ru`**, **`NODE_ENV=production`**, **`PORT=3000`**, **`LEADS_*`**, при Docker — **`GHCR_IMAGE_OWNER`**. См. **`web/.env.example`** и **`deploy/env.production.example`**. |
| **Аналитика** | Заполнить **`NEXT_PUBLIC_GA_ID`** / **`NEXT_PUBLIC_YM_ID`**; в интерфейсах завести цели по именам из **`src/lib/analytics/events.ts`**. |
| **Telegram** | **`TELEGRAM_BOT_TOKEN`**, **`TELEGRAM_CHAT_ID`**; без них лиды всё равно пишутся в файл (**`telegramSent: false`**). |
| **Вебхук** | **`LEAD_WEBHOOK_URL`** — POST JSON `{ event: "lead.created", lead }` после сохранения лида; опционально **`LEAD_WEBHOOK_SECRET`** → `Authorization: Bearer …`. Без URL — **`webhookSent: false`**, заявка всё равно сохраняется. |
| **DNS** | **A** / **AAAA** для **`svorazbor.ru`** (и **www**, если используете) → IP VPS. |
| **SSL** | **Certbot** (`certbot --nginx -d …`) или TLS на обратном прокси. |
| **Индексация** | После выкладки открыть **`/robots.txt`**, **`/sitemap.xml`**, проверить превью ссылки (OG) и canonical в исходнике главной. |
| **Smoke** | С сервера (Docker): `curl -sS http://127.0.0.1:3001/api/health` → OK; в браузере: квиз (fresh + clarify), отправка формы, **`/thanks`**. Локально/CI: **`npm run smoke`**. |

Дополнительно перед первым продом: **favicon** (`src/app/icon.svg` или замена по [доке Next.js](https://nextjs.org/docs/app/api-reference/file-conventions/metadata/app-icons)), актуальность текстов **`/privacy`** и **`/consent`**.

**Вебхук (n8n) не вызывается / узел пустой:** переменная **`LEAD_WEBHOOK_URL`** должна быть в **`.env` в каталоге с `docker-compose.yml` на VPS** (образ не читает `web/.env`). После правок: **`docker compose up -d`**. Проверка: **`docker exec svo-site printenv LEAD_WEBHOOK_URL`**. В браузере в ответе **`POST /api/lead`** смотрите **`webhookSent`**. В n8n: workflow **включён** (Active), узел Webhook — метод **POST**, URL **Production** (не «Listen for test event»). Логи контейнера: **`docker logs svo-site 2>&1 | tail -80`** — ищите **`[webhook]`**. Если задан **`LEAD_WEBHOOK_SECRET`**, приёмник должен ожидать **`Authorization: Bearer …`**, иначе уберите секрет с сайта.

## Скрипты

| Команда              | Назначение                                      |
| -------------------- | ----------------------------------------------- |
| `npm run dev`        | Разработка                                      |
| `npm run build`      | Продакшен-сборка                                |
| `npm start`          | Запуск после `build`                            |
| `npm run lint`       | ESLint                                          |
| `npm run test`       | Vitest: все `src/**/*.test.ts` (unit + integration) |
| `npm run test:integration` | Только `*.integration.test.ts` |
| `npm run test:e2e`   | Playwright (`e2e/`, перед прогоном `build` + `start`, см. ниже) |
| `npm run test:e2e:ui` | Playwright в интерактивном UI |
| `npm run test:all`   | `test` + `test:e2e` |
| `npm run smoke`      | `lint` + `test` + `build` (локальная проверка)   |
| `npm run docker:build` | Локальная сборка Docker-образа (из каталога `web/`) |

## Тесты

### Unit и integration (Vitest)

- **Unit:** калькулятор (`getRecipientsCount`, форматирование рублей), нормализация региона (`normalizeRegionInput`, `findRegionCatalogEntry`), телефон (`normalizeRuPhone`), «цена ожидания» (`computeDelayLossRub` в `delay-loss.ts`).
- **Integration:** сборка экрана выплат (`buildPayoutBreakdownView` — федеральный блок, региональные статусы, fallback), Zod `leadApiSchema` / `leadFormSchema`, навигация квиза (`getVisibleSteps`, `clampStepIndex`, перенос clarify → fresh).

```bash
cd web
npm run test
# только integration-файлы:
npm run test:integration
```

Конфиг: **`vitest.config.ts`**, тестовые файлы рядом с кодом: `*.test.ts`, `*.integration.test.ts`.

### E2E (Playwright)

Первый раз установите браузеры (достаточно Chromium):

```bash
cd web
npx playwright install chromium
```

По умолчанию **`playwright.config.ts`** поднимает продакшен-сервер на **`127.0.0.1:4173`** (переменная **`PW_TEST_PORT`**) командой `npm run build && npx next start -H 127.0.0.1 -p …`, чтобы не пересекаться с **`npm run dev`** на порту 3000. В CI задайте **`CI=1`**, чтобы каждый прогон поднимал новый сервер.

Переменная **`PLAYWRIGHT_BASE_URL`** переопределяет базовый URL (и должна совпадать с реально запущенным сервером).

```bash
npm run test:e2e
```

Покрыто: fresh flow до результата, clarify → расчёт → результат, форма (happy path и ошибка согласия), `/thanks`, «Назад» / «Очистить» / восстановление из `localStorage`, `/privacy` и `/consent`.

## Структура проекта

| Путь | Содержимое |
| ---- | ---------- |
| `src/app` | Маршруты: `/`, `/privacy`, `/consent`, `/thanks`, `POST /api/lead`, `opengraph-image.tsx`, `robots.ts`, `sitemap.ts`, метаданные, `icon.svg` |
| `src/data/seo/site-metadata.ts` | Title, description и ключевые слова для главной и юрстраниц |
| `src/lib/analytics/track.ts` | Отправка событий в GA4 и Метрику |
| `src/components/seo/home-json-ld.tsx` | JSON-LD главной: WebSite + FAQPage (`@graph`) |
| `src/components/sections` | Секции лендинга |
| `src/components/quiz` | Предварительный расчёт и экран результата |
| `src/components/ui` | Примитивы UI |
| `src/contexts/quiz-context.tsx` | Состояние расчёта + синхронизация с `localStorage` |
| `src/lib/storage/quiz-storage.ts` | Ключ `svo_quiz_v2`, валидация восстановленного JSON |
| `src/lib/calculator.ts` | Суммы и формулы |
| `src/lib/validation/lead.ts` | Zod: форма и API |
| `src/lib/leads` | Нормализация лида, хранилище (`file` \| `memory`), `patchLead` |
| `src/lib/telegram` | HTML-сообщение и отправка в Bot API (таймаут, логи) |
| `src/lib/phone` | Нормализация телефона (+7, сырой ввод) |
| `src/lib/site-url.ts` | Разбор `NEXT_PUBLIC_SITE_URL` |
| `src/data/texts` | Тексты лендинга и расчёта |

## SEO и аналитика

### Индексация

- Файл **`src/app/robots.ts`** отдаёт `robots.txt`: разрешена индексация сайта, закрыты **`/thanks`** и **`/api/`**, указан **`sitemap.xml`**.
- Файл **`src/app/sitemap.ts`** включает главную, **`/privacy`** и **`/consent`**. Страница **`/thanks`** в карту сайта не попадает.
- Общие meta, Open Graph, `metadataBase`, иконки и шаблон заголовка — **`src/app/layout.tsx`** и **`src/data/seo/site-metadata.ts`**.
- Страница **`/thanks`**: в **`src/app/thanks/page.tsx`** заданы **`noindex`** и **`nofollow`** (в т.ч. для `googleBot`).
- На главной выводится JSON-LD **WebSite** и **FAQPage** в одном `@graph` (**`src/components/seo/home-json-ld.tsx`**) — вопросы совпадают с блоком FAQ на странице.

### Google Analytics 4

1. Зайдите в [Google Analytics](https://analytics.google.com/) → **Администратор** → **Потоки данных** → веб-поток.
2. Скопируйте **идентификатор потока** (формат **`G-XXXXXXXXXX`**).
3. В `.env`: **`NEXT_PUBLIC_GA_ID=G-XXXXXXXXXX`**.
4. На сайте счётчик подключается пакетом **`@next/third-parties/google`** (**`GoogleAnalytics`** в **`src/app/layout.tsx`**).

**Проверка:** отчёт **Realtime** в GA4 — откройте сайт в браузере и убедитесь, что появился активный пользователь. Для отладки событий используйте **Admin → DebugView** (и при необходимости [расширение отладки](https://chrome.google.com/webstore/detail/google-analytics-debugger/jnkmfdileelhofjcijamephohjechhna)).

### Яндекс.Метрика

1. [metrika.yandex.ru](https://metrika.yandex.ru/) → добавьте счётчик и скопируйте **номер счётчика** (только цифры, обычно 8–10 знаков).
2. В `.env`: **`NEXT_PUBLIC_YM_ID=12345678`** (без пробелов и букв).
3. Скрипт подключается в **`src/app/layout.tsx`** через компонент **`YandexMetrika`**: загрузка **`afterInteractive`**, в разметке есть **`noscript`** с пикселем `mc.yandex.ru/watch/...`.

**Проверка:** в Метрике раздел **Мониторинг → Сейчас на сайте**; либо установите [расширение для отладки](https://yandex.ru/support/metrica/general/debugger.html).

### Кастомные события

События уходят в **GA4** (`gtag`) и в Метрику как **`reachGoal`** с тем же именем. В интерфейсе Метрики для каждого имени создайте **цель типа «JavaScript-событие»** с таким же идентификатором.

| Имя события | Когда срабатывает |
|-------------|-------------------|
| `fresh_flow_selected` | Выбран сценарий «узнать выплаты» (`fresh`) |
| `stuck_flow_selected` | Выбран сценарий «прояснить ситуацию» (`clarify`) |
| `quiz_start` | Запущен квиз (после выбора сценария или после перехода из clarify) |
| `quiz_clarify_to_fresh` | Из экрана clarify запущен полный расчёт (сохранены ответы опроса) |
| `quiz_complete` | Квиз завершён (до показа результата / экрана благодарности) |
| `result_view` | Показан экран предварительного **результата расчёта** |
| `lead_form_start` | Первый фокус внутри формы заявки |
| `lead_form_submit` | Нажата отправка формы (до ответа сервера) |
| `lead_form_success` | Успешный ответ API лида, перед переходом на `/thanks` |

Параметры: у части событий передаётся **`flow_mode`** (`fresh` | `clarify` | `unknown`); у **`lead_form_success`** — **`telegram_sent`** (boolean).

Код: **`src/lib/analytics/events.ts`**, **`src/lib/analytics/track.ts`**; вызовы в **`quiz-context.tsx`**, **`QuizResult.tsx`**, **`lead-form-section.tsx`**.

## Лиды, `POST /api/lead` и Telegram

### Как это работает

1. Клиент отправляет JSON (форма + объект `quiz` с `flowMode`, `answers`, `completed`).
2. Сервер валидирует тело через **`leadApiSchema`** (`src/lib/validation/lead.ts`): имя, телефон (≥10 цифр), регион, согласие, **обязательный сценарий расчёта** `A` | `B`.
3. Телефон нормализуется (`src/lib/phone/normalize-ru-phone.ts`): в лид попадают **`phone`** (нормализованный) и **`phoneRaw`** (как ввели).
4. Запись собирается в **`StoredLeadRecord`** (`src/types/stored-lead.ts`) и **сохраняется** через **`LeadsStorage.save`**.
5. Вызывается **`sendLeadTelegramNotification`** (`src/lib/telegram/send-lead-notification.ts`): `sendMessage` с `parse_mode: HTML`, таймаут **12 с**, ошибки только в лог, без падения запроса.
6. Если Telegram ответил успешно, в файле/памяти обновляется флаг **`telegramSent: true`** (`patchLead`).
7. Ответ клиенту (при успешном сохранении):

   ```json
   { "ok": true, "success": true, "saved": true, "telegramSent": true, "webhookSent": true, "id": "…" }
   ```

   Если Telegram или вебхук недоступны или не настроены: **`saved: true`**, **`telegramSent` / `webhookSent`** могут быть **`false`**, HTTP **200** — заявка не теряется.

### Переменные окружения

См. **`.env.example`**. Имена:

- **`TELEGRAM_BOT_TOKEN`** — токен бота.
- **`TELEGRAM_CHAT_ID`** — куда слать (чат / канал / ваш id).
- **`CONTACT_TEXT`** — произвольная строка: в конец сообщения в Telegram и блок на **`/thanks`**.
- **`LEADS_STORAGE_MODE`** = `file` | `memory` (поддерживается и устаревшее **`STORAGE_MODE`**).
- **`LEADS_FILE_PATH`** — путь к JSON-массиву лидов (по умолчанию `./data/leads.json`); каталог создаётся автоматически.

### Как завести бота и узнать `chat_id`

1. В Telegram откройте [**@BotFather**](https://t.me/BotFather) → **/newbot** → имя и username → скопируйте **токен** → вставьте в **`TELEGRAM_BOT_TOKEN`**.
2. Напишите боту любое сообщение (или добавьте бота в канал и разрешите ему постить, если нужен канал).
3. Узнать **chat_id**:
   - личка: откройте `https://api.telegram.org/bot<TOKEN>/getUpdates` в браузере после сообщения боту — в JSON найдите `"chat":{"id": … }`;
   - или используйте бота [**@userinfobot**](https://t.me/userinfobot) для своего id;
   - для канала: добавьте бота админом, перешлите пост в [**@getidsbot**](https://t.me/getidsbot) или смотрите `getUpdates` с постом в канале (id канала обычно отрицательный, начинается с `-100`).

Вставьте число (или строку с id) в **`TELEGRAM_CHAT_ID`**.

### Как проверить отправку лида

1. Заполните `.env`, перезапустите `npm run dev`.
2. На сайте завершите предварительный расчёт (сценарий и шаги), откройте форму, отправьте заявку.
3. Должен прийти ответ **200** с **`saved: true`**; в чате — сообщение с эмодзи и полями лида.
4. Файл **`data/leads.json`** (или путь из **`LEADS_FILE_PATH`**) должен содержать новую запись с полями вроде **`telegramSent`**, **`phoneRaw`**.

На **Vercel** файловый режим непостоянен — для продакшена реализуйте свою БД и подключите её в **`getLeadsStorage()`** (`src/lib/leads/storage/factory.ts`).

## Деплой в production: Docker, GHCR, GitHub Actions, VPS, Nginx

**Целевой домен:** **`https://svorazbor.ru`**. DNS — у регистратора (A/AAAA на IP VPS; при необходимости отдельно **www**).

**Цепочка:** push в **`main`** / **`master`** (см. `paths` в `.github/workflows/deploy.yml`) → GitHub Actions собирает образ → **GHCR** (`ghcr.io/<owner>/svo-site`) → SSH на VPS → `docker compose pull && up -d` → **Nginx** (прокси на `127.0.0.1:3001`) → **HTTPS**.

**Файлы в репозитории:**

| Файл | Назначение |
|------|------------|
| `web/Dockerfile` | Multi-stage build, **standalone** Next.js |
| `web/.dockerignore` | Исключения для контекста сборки |
| `docker-compose.yml` | Сервис `app`, на хосте **127.0.0.1:3001** → контейнер **:3000**, том **`./data:/app/data`**, healthcheck **`/api/health`** |
| `.github/workflows/deploy.yml` | Build → push GHCR → deploy на VPS |
| `.github/workflows/ci.yml` | Lint, test, build на PR/push в `web/**` |
| `.github/workflows/deploy-vps.yml` | Legacy: PM2 + rsync (только ручной запуск) |
| **`deploy/nginx/svorazbor.ru.conf`** | Шаблон виртуального хоста под прод-домен |
| `deploy/nginx/svo.kalugin-consultig.ru.conf` | Пример для другого хоста (legacy) |
| **`deploy/env.production.example`** | Образец `.env` рядом с compose на VPS |

Локальная сборка образа (из **корня** репозитория): **`make docker-build`** или `docker build -f web/Dockerfile -t svo-site:local ./web`.

### Лиды и том данных

В режиме **`LEADS_STORAGE_MODE=file`** лиды пишутся в **`./data/leads.json`** относительно **`process.cwd()`** (в контейнере **`/app`**). В **`docker-compose.yml`** смонтировано **`./data:/app/data`** — файл на диске VPS **не теряется** при redeploy.

### Ограничение по zero-downtime

При `docker compose up -d` контейнер кратковременно перезапускается. Полный zero-downtime — отдельно (blue/green, два инстанса за балансировщиком).

### Чеклист перед первым деплоем

- [ ] Репозиторий на GitHub, ветка **`main`** или **`master`**.
- [ ] На VPS: Docker Engine и Compose v2 (`docker compose version`).
- [ ] DNS **A** / **AAAA** для **`svorazbor.ru`** (и **www**, если нужен) → IP VPS.
- [ ] В GitHub заполнены секреты Actions (таблица ниже).
- [ ] На VPS в **`VPS_APP_DIR`**: `docker-compose.yml`, **`.env`**, каталог **`data/`** с владельцем **uid 1001** (пользователь **`nextjs`** в образе).

### Секреты и переменные GitHub (Settings → Secrets and variables → Actions)

**Секреты** (Sensitive):

| Secret | Описание |
|--------|----------|
| `VPS_HOST` | IP или домен для SSH |
| `VPS_USER` | Пользователь SSH |
| `VPS_SSH_KEY` | Приватный ключ **ed25519** или RSA, полный PEM (`BEGIN` / `END`) |
| `VPS_PORT` | Опционально; SSH-порт, по умолчанию **22** |

**Переменные** (Repository variables, вкладка **Variables**):

| Variable | Описание |
|----------|----------|
| **`VPS_APP_DIR`** | Абсолютный путь на сервере, например **`/var/www/svorazbor`**. Так путь **не маскируется** в логах Actions как `***`, проще отлаживать. Если Variable не задана, workflow берёт **Secret** с тем же именем **`VPS_APP_DIR`**. |

Образ в GHCR публикуется через **`GITHUB_TOKEN`** (`packages: write`). На VPS: `docker login ghcr.io` с тем же токеном. При **403** на `docker pull` (приватный пакет) — PAT с **`read:packages`** в секрет **`GHCR_READ_TOKEN`** и правка логина в **`deploy.yml`** (комментарий в workflow).

**Важно:** **`GHCR_IMAGE_OWNER`** в `.env` на VPS — **строчными буквами**, как в URL GHCR. В workflow owner нормализуется в lower case.

### Что положить на VPS

**Рекомендуемый путь на сервере:** **`/var/www/svorazbor`** (его же задайте в **Variable** **`VPS_APP_DIR`** в GitHub).

#### Автоматическая подготовка `/var/www/svorazbor`

На VPS (Ubuntu/Debian), из **корня клона** этого репозитория:

```bash
git clone https://github.com/kaluginvit72/SVO_viplaty_site.git
cd SVO_viplaty_site
sudo bash deploy/scripts/setup-var-www-svorazbor.sh
```

Скрипт **[`deploy/scripts/setup-var-www-svorazbor.sh`](../deploy/scripts/setup-var-www-svorazbor.sh)**:

- создаёт **`/var/www/svorazbor`** и **`data/`**;
- копирует **`docker-compose.yml`**;
- если **`.env`** ещё нет — копирует **`deploy/env.production.example`** → **`.env`** (`chmod 600`);
- выставляет владельца **`data/`** на **uid 1001** (пользователь **`nextjs`** в контейнере);
- владелец каталога и файлов compose — пользователь, от которого вы вызывали `sudo` (**`$SUDO_USER`**), чтобы тот же пользователь мог запускать **`docker compose`** и чтобы совпадал SSH-пользователь из GitHub Actions.

После скрипта отредактируйте **`/var/www/svorazbor/.env`** (Telegram, при необходимости аналитика; **`GHCR_IMAGE_OWNER`** в шаблоне уже **`kaluginvit72`** — при другом аккаунте GitHub замените).

#### Вручную (если без скрипта)

В каталоге **`VPS_APP_DIR`**:

1. **`docker-compose.yml`** из корня репозитория.
2. **`.env`** из **`deploy/env.production.example`**, заполнить; `chmod 600 .env`.
3. Каталог **`data/`** с **`chown -R 1001:1001`** на **`data/`** (см. пошаговый раздел ниже).

### Пошаговый деплой на VPS: контейнер и запуск

Ниже — полный сценарий «с нуля» до работающего сайта за Nginx. Путь **`/var/www/svorazbor`** замените на свой **`VPS_APP_DIR`**.

#### 1. Подготовка VPS (Ubuntu / Debian)

1. Обновите пакеты: `sudo apt update && sudo apt upgrade -y`.
2. Установите **Docker Engine** и плагин **Compose** (официальная инструкция: [Install Docker Engine on Ubuntu](https://docs.docker.com/engine/install/ubuntu/)). Кратко: добавьте репозиторий Docker, затем:
   ```bash
   sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
   ```
3. Проверка: `docker --version` и `docker compose version`.
4. Чтобы запускать compose **без** `sudo` (по желанию):
   ```bash
   sudo usermod -aG docker "$USER"
   ```
   Выйдите из SSH-сессии и зайдите снова (или `newgrp docker`).
5. Включите автозапуск Docker после перезагрузки (обычно уже так): `sudo systemctl enable --now docker`.

#### 2. Каталог на сервере и файлы

Проще всего — скрипт **`deploy/scripts/setup-var-www-svorazbor.sh`** (см. подраздел **«Автоматическая подготовка `/var/www/svorazbor`»** выше): запуск из клона репозитория на VPS под **`sudo bash …`**.

Вручную:

```bash
sudo mkdir -p /var/www/svorazbor/data
sudo chown -R "$USER:$USER" /var/www/svorazbor
cd /var/www/svorazbor
```

Скопируйте **`docker-compose.yml`** с ПК: `scp docker-compose.yml user@YOUR_VPS_IP:/var/www/svorazbor/`. Создайте **`.env`** из **`deploy/env.production.example`**, **`chmod 600 .env`**, затем **`sudo chown -R 1001:1001 /var/www/svorazbor/data`**.

В **`.env`** проверьте **`GHCR_IMAGE_OWNER`** (строчными буквами, как в **`ghcr.io/<owner>/svo-site`**).

#### 3. Образ в GHCR: когда он появляется

- **Автоматически:** после push в **`main`** / **`master`** (см. `paths` в **`.github/workflows/deploy.yml`**) workflow собирает образ и пушит **`ghcr.io/<owner>/svo-site:latest`**.
- **Первый раз:** дождитесь успешного прогона **Actions → Deploy** или соберите образ локально и загрузите в GHCR вручную (редко нужно).

Пока образа нет, **`docker compose pull`** на VPS завершится ошибкой — сначала должен отработать CI или нужен ручной push образа.

#### 4. Вход в GitHub Container Registry на VPS и запуск контейнера

На сервере, в каталоге с **`docker-compose.yml`**:

```bash
cd /var/www/svorazbor
```

Для **публичного** пакета GHCR логин не обязателен. Для **приватного** — один раз залогиньтесь (PAT с правом **`read:packages`** или классический токен с этим scope):

```bash
echo "ВАШ_GITHUB_PAT" | docker login ghcr.io -u ВАШ_GITHUB_LOGIN --password-stdin
```

Workflow при деплое сам выполняет `docker login` для пользователя **`github.actor`**; при ручном первом запуске без CI используйте PAT, как выше.

Загрузите образ и поднимите сервис:

```bash
docker compose pull
docker compose up -d --remove-orphans
```

В **`docker-compose.yml`** у сервиса **`app`** задано **`restart: always`** — контейнер поднимется после перезагрузки VPS.

#### 5. Проверка, что приложение запущено

```bash
docker compose ps
docker compose logs -f --tail=100 app
curl -sS http://127.0.0.1:3001/api/health
```

Ожидается ответ **HTTP 200** от **`/api/health`**. На хосте приложение проброшено на **`127.0.0.1:3001`** (внутри контейнера — **3000**), наружу только **Nginx** (**80**/**443**).

#### 6. Firewall (рекомендуется)

Если включён **ufw**, откройте HTTP/HTTPS; порты **3001**/**3000** приложения снаружи не открывайте (достаточно Nginx):

```bash
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable
sudo ufw status
```

#### 7. Nginx и HTTPS

Дальше — как в подразделах **[Nginx](#nginx)** и **[HTTPS (Certbot)](#https-certbot)** ниже: прокси на **`127.0.0.1:3001`** (см. **`deploy/nginx/svorazbor.ru.conf`**), затем Certbot.

#### 8. Обновление версии (после каждого успешного деплоя из GitHub)

На VPS (вручную или тем же скриптом, что в **Actions**):

```bash
cd /var/www/svorazbor
docker compose pull
docker compose up -d --remove-orphans
```

Лиды в **`./data`** сохраняются.

#### Ручная сборка на VPS (без GHCR)

Если образ в реестр пока не пушится, на сервере можно собрать из клона репозитория (нужны **Node не в рантайме** — только Docker):

```bash
cd /path/to/repo   # корень, где лежит каталог web/
docker build -f web/Dockerfile -t svo-site:local ./web
```

Временно в **`docker-compose.yml`** замените строку **`image: ghcr.io/${GHCR_IMAGE_OWNER}/svo-site:latest`** на **`image: svo-site:local`** и выполните **`docker compose up -d`** без **`pull`**. После появления образа в GHCR верните **`image`** и **`GHCR_IMAGE_OWNER`**.

### Обязательные переменные в `.env` на VPS

См. **`deploy/env.production.example`**. Ключевые:

- **`GHCR_IMAGE_OWNER`** — GitHub login/org **lowercase**.
- **`NEXT_PUBLIC_SITE_URL=https://svorazbor.ru`** (без завершающего `/`).
- **`LEADS_FILE_PATH=./data/leads.json`**, **`NODE_ENV=production`**, **`PORT=3000`**.
- Опционально: **`NEXT_PUBLIC_GA_ID`**, **`NEXT_PUBLIC_YM_ID`**, **`TELEGRAM_*`**, **`CONTACT_TEXT`**.

### Nginx

1. Установите Nginx на VPS.
2. Скопируйте **`deploy/nginx/svorazbor.ru.conf`** → например **`/etc/nginx/sites-available/svorazbor.ru.conf`**.
3. Включите сайт и перезагрузите:

   ```bash
   sudo ln -sf /etc/nginx/sites-available/svorazbor.ru.conf /etc/nginx/sites-enabled/
   sudo nginx -t && sudo systemctl reload nginx
   ```

   Если **www** не используется — уберите **`www.svorazbor.ru`** из **`server_name`** в конфиге до выдачи сертификата.

### HTTPS (Certbot)

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d svorazbor.ru -d www.svorazbor.ru
```

(Один домен — только `-d svorazbor.ru`.) Certbot добавит `listen 443 ssl` и при необходимости редирект HTTP → HTTPS.

### Обновление после `git push`

1. Workflow **Deploy (Docker → GHCR → VPS)** пушит **`latest`** и **`<github.sha>`** в **`ghcr.io/<owner>/svo-site`**.
2. На VPS скрипт деплоя подтягивает актуальный **`docker-compose.yml`** с **raw.githubusercontent.com** (ветка **`main`** / текущая), затем **`docker compose pull`** и **`docker compose up -d`** — иначе на сервере оставался бы старый compose (например порт **3000**).
3. Том **`./data`** сохраняется.

### Первый раз на VPS (обязательно до первого успешного Deploy)

Зайдите по SSH **тем же пользователем**, что в секрете **`VPS_USER`** (не обязательно `root`). Выполните:

```bash
sudo mkdir -p /var/www/svorazbor
sudo chown -R "$USER:$USER" /var/www/svorazbor
cd /tmp
rm -rf SVO_viplaty_site
git clone https://github.com/kaluginvit72/SVO_viplaty_site.git
cd SVO_viplaty_site
sudo bash deploy/scripts/setup-var-www-svorazbor.sh
```

Скрипт снова выставит владельца **`data/`** на **uid 1001** и положит **`docker-compose.yml`** / **`.env`**. Затем отредактируйте **`/var/www/svorazbor/.env`**.

Проверка от **того же пользователя**, что в Actions:

```bash
test -d /var/www/svorazbor && ls -la /var/www/svorazbor
```

В GitHub → **Variables** → **`VPS_APP_DIR`** = **`/var/www/svorazbor`** (без кавычек, без пробелов, без `/` в конце). Либо тот же текст в Secret — но в логах путь будет скрыт.

Если каталог создавали только под **`root`**, а Actions ходят под **`deploy`**, выдайте владельца: **`sudo chown -R deploy:deploy /var/www/svorazbor`**, затем снова **`sudo chown -R 1001:1001 /var/www/svorazbor/data`**.

### Если job «Deploy on VPS» в GitHub Actions падает

| Симптом | Что сделать |
|--------|-------------|
| **`Unexpected input(s) 'script_stop'`** | В репозитории в **`.github/workflows/deploy.yml`** не должно быть **`script_stop`** (в **appleboy/ssh-action@v1.2.x** этого поля нет). Закоммитьте актуальный файл из репозитория и запушьте в **`main`**. |
| **`Нет каталога VPS_APP_DIR или нет прав`** / **`cd: … No such file`** | Выполните раздел **«Первый раз на VPS»** выше по этой странице. Убедитесь, что **`VPS_USER`** может выполнить **`cd /var/www/svorazbor`**. |
| **`Bind for 0.0.0.0:3000 failed: port is already allocated`** | На хосте занят **3000**. В **`docker-compose.yml`** приложение проброшено на **`127.0.0.1:3001`**, Nginx — на **3001** (шаблон **`deploy/nginx/svorazbor.ru.conf`**). Скопируйте актуальный **`docker-compose.yml`** на VPS или вручную замените строку портов на **`127.0.0.1:3001:3000`**, затем **`docker compose up -d`**. |
| **`missing server host`** | Не задан **`VPS_HOST`** (или другие обязательные секреты). |

### Проверка контейнера и логи

```bash
cd /var/www/svorazbor   # ваш VPS_APP_DIR
docker compose ps
docker compose logs -f --tail=200 app
curl -sS http://127.0.0.1:3001/api/health
```

### Ручной откат образа

В **`docker-compose.yml`** временно укажите тег по SHA из GHCR, затем на VPS: **`docker compose pull && docker compose up -d`**, либо образ по digest `ghcr.io/owner/svo-site@sha256:…`.

---

## Legacy: деплой через PM2 и rsync

Альтернатива Docker: workflow **`.github/workflows/deploy-vps.yml`** (**Deploy to VPS (legacy PM2)**) — только **ручной запуск** в GitHub (**Actions → Run workflow**). Автодеплой по push для этого пути **отключён**.

**Секреты** для legacy отличаются от Docker-деплоя:

| Secret | Описание |
|--------|----------|
| `VPS_HOST` | IP или домен |
| `VPS_USER` | Пользователь SSH |
| `VPS_SSH_PRIVATE_KEY` | Полный приватный ключ PEM |
| `VPS_DEPLOY_PATH` | Каталог на сервере **без** завершающего `/` |
| `VPS_SSH_KNOWN_HOSTS` | Опционально: вывод `ssh-keyscan -H хост` |

На сервере нужны **Node.js 20+**, глобальный **PM2**, каталог деплоя, **`.env`**, каталог **`data/`** для лидов, после первого выкладывания — **`pm2 start deploy/ecosystem.config.cjs`** (файл **`ecosystem.config.cjs`** кладётся standalone-сборкой в каталог деплоя скриптом workflow). В **`.env`**: **`NEXT_PUBLIC_SITE_URL=https://svorazbor.ru`**, Telegram, **`LEADS_FILE_PATH=./data/leads.json`** — как в Docker-разделе и **`web/.env.example`**.

Если корень репозитория — только **`web/`**, перенесите **`.github`** внутрь `web` и поправьте пути в workflow (без префикса `web/`, см. комментарии в **`deploy/VPS.md`** — там краткая заметка для этого случая).

### CI (без деплоя)

**`.github/workflows/ci.yml`** — **`npm run lint`**, **`npm run test`** и **`npm run build`** на push и PR в **`main`** / **`master`** при изменениях в **`web/`**.

## Предварительный расчёт и прогресс

- Прогресс хранится в браузере под ключом **`svo_quiz_v2`**. Старый ключ `svo_quiz_v1` при первом заходе удаляется.
- Битый JSON в `localStorage` игнорируется, расчёт начинается с чистого состояния.
- Сценарий **B**: шаг «куда подали» и «сколько ждёте» объединены в один экран.
- Сброс расчёта запрашивает подтверждение, чтобы не потерять ответы случайно.

## Примечание про папку с кириллицей

Корневая папка репозитория с кириллицей мешает `create-next-app` задать корректный `name` в `package.json`, поэтому приложение лежит в подкаталоге **`web/`** с латинским именем пакета.
