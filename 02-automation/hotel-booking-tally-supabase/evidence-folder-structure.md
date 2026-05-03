# Структура папки доказательств (скрины/экспорт) — рекомендуемая

Цель: быстро собрать материалы под “Что сдавать” из ТЗ + раздел 22 отчёта.

## Папка (пример)
`/GraduationProject_Evidence_HotelBooking/`

## Файлы (рекомендуемые имена)
### 01 — n8n workflows
- `01-workflow-a-webhook.png` — скрин воркфлоу A целиком
- `02-workflow-b-daily-report.png` — скрин воркфлоу B целиком

### 02 — Supabase tables
- `03-supabase-rooms.png` — таблица `rooms` с seed/test данными
- `04-supabase-bookings.png` — таблица `bookings` с результатами тестов (+ `created_at`)

### 03 — Emails
- `05-email-client-found.png` — письмо клиенту (номер найден)
- `06-email-client-not-found.png` — письмо клиенту (номер не найден)
- `07-email-manager-daily-report.png` — письмо менеджеру (ежедневный отчёт)

### 04 — Executions (успешные запуски)
- `08-execution-t1-found.png`
- `09-execution-t2-not-found.png`
- `10-execution-t3-duplicate.png`
- `11-execution-t4-missing-field.png`
- `12-execution-t5-daily-report.png`

### 05 — Key nodes settings (по желанию, но полезно)
- `13-node-webhook-settings.png`
- `14-node-supabase-select-rooms.png`
- `15-node-supabase-update-room.png`
- `16-node-supabase-insert-booking.png`
- `17-node-gmail-client.png`
- `18-node-gmail-manager.png`

### 06 — Exports
- `workflow-a.json`
- `workflow-b.json`

### 07 — Process scheme
- `process-scheme.png` (или ссылка в отчёте)

## Минимум (если времени мало)
Достаточно: `01, 03, 04, 05, 07, 08+09, workflow-a.json, workflow-b.json`.

