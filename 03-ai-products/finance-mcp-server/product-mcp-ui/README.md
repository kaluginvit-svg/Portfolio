# product-mcp-ui

Внутренний **web-интерфейс** для финансового MCP backend **product-mcp**: загрузка файлов, запуск tools через UI, таблицы и карточки с результатами. Это **не** агент и **не** чат — только UI-клиент и тонкий server adapter.

## Связь с product-mcp

- Бизнес-логика и расчёты остаются в **product-mcp** (Python, SQLite, `registry.dispatch`).
- UI вызывает `POST /api/tools` с телом `{ "tool": "...", "payload": { ... } }`.
- Next.js (Node) либо:
  1. **Запускает** `scripts/mcp_invoke.py` через subprocess с `PRODUCT_MCP_PATH`, либо
  2. Проксирует на **HTTP bridge**, если задан `MCP_BASE_URL` (POST `{tool,payload}` на `/invoke`).

Если путь к Python-проекту не задан, adapter возвращает **mock-ответы**, чтобы UI оставался рабочим офлайн.

## Требования

- Node.js 18+
- npm или pnpm
- Для реальных данных: Python 3.11+ с зависимостями **product-mcp** (`pip install -r requirements.txt` в каталоге product-mcp)

## Установка

```bash
cd product-mcp-ui
npm install
```

## Настройка `.env`

Скопируйте `.env.example` в `.env`:

| Переменная | Назначение |
|------------|------------|
| `PRODUCT_MCP_PATH` | Абсолютный путь к папке **product-mcp** (где лежит `registry.py`) |
| `MCP_PYTHON` | Команда Python (`python` / `py` / `python3`) |
| `MCP_BASE_URL` | Опционально: URL внешнего bridge вместо subprocess |
| `UPLOAD_DIR` | Куда сохранять загрузки (по умолчанию `./data/uploads`) |
| `INTERNAL_API_BASE_URL` | Резерв под отдельный API (обычно пусто) |
| `NEXT_PUBLIC_APP_NAME` | Имя в шапке |

Пример (Windows, скорректируйте путь):

```env
PRODUCT_MCP_PATH=C:\path\to\product-mcp
MCP_PYTHON=python
NEXT_PUBLIC_APP_NAME=product-mcp-ui
```

## Запуск

```bash
npm run dev
```

Откройте [http://localhost:3000](http://localhost:3000).

## Страницы

| Путь | Назначение |
|------|------------|
| `/` | Dashboard: KPI-карточки, счётчик alerts из `health_check`, последние импорты |
| `/import` | CSV / XLSX / PDF / TXT: `import_csv` или `import_contract` |
| `/records` | `list_financial_records` + фильтры + экспорт CSV |
| `/kpis` | `calculate_kpis` |
| `/plan-vs-fact` | `plan_vs_fact` + таблица отклонений + commentary |
| `/liquidity` | `liquidity_forecast` + таблица + график (Recharts) |
| `/payments` | `payment_calendar` |
| `/contracts` | `list_contracts` + `contract_risk_scan` |
| `/investments` | `list_investment_projects`, `add_investment_project`, `evaluate_investment` |
| `/reports` | `export_report` + ссылка на скачивание из `product-mcp/data/exports` |

## Поток загрузки файла

1. Пользователь выбирает файл и тип (`statement_type`).
2. `POST /api/upload` (multipart): файл пишется в `UPLOAD_DIR`.
3. **XLSX/XLS** конвертируются в CSV на Node (`xlsx`) и вызывается `import_csv` с путём к CSV.
4. **Contract** → `import_contract` (только PDF/TXT/MD).
5. Ответ: счётчики, ошибки, предупреждения, превью строк CSV.

## Как выполняется tool

1. Клиент: `fetch("/api/tools", { body: JSON.stringify({ tool, payload }) })` или хук `useToolMutation`.
2. `src/lib/mcp-server.ts`: `callMcpTool` → Python script или HTTP.
3. Python `scripts/mcp_invoke.py`: инициализация БД, `register_all`, `registry.dispatch(tool, payload)`, JSON в stdout.

## HTTP bridge (опционально)

Реализуйте сервис, который принимает:

`POST /invoke`  
`{ "tool": "calculate_kpis", "payload": { ... } }`

и возвращает тот же JSON, что и `registry.dispatch` (`{ success, result }` / `{ success: false, error }`). Укажите базовый URL в `MCP_BASE_URL`.

## Ограничения MVP

- Каждый вызов Python — **новый процесс** (холодный старт).
- Пагинация списков на стороне UI (MCP отдаёт до лимита строк).
- Список alerts в dashboard — только **число** из `health_check`; детали рисков — после `contract_risk_scan` на странице Contracts.
- Скачивание отчётов работает для файлов в `PRODUCT_MCP_PATH/data/exports` (проверка пути на path traversal).

## Идеи расширения

- Долгоживущий Python HTTP service вместо subprocess.
- Отдельный MCP tool `list_alerts` в product-mcp.
- Server-side pagination через новые параметры tools.
- Auth (SSO) и роли.

## Структура (основное)

```
product-mcp-ui/
├── scripts/mcp_invoke.py
├── src/app/           # App Router, страницы, api/tools, api/upload, api/export
├── src/components/    # layout, common, charts, ui
├── src/lib/           # mcp-server, mcp-client, formatters, paths
├── src/types/, src/schemas/, src/hooks/
└── README.md
```
