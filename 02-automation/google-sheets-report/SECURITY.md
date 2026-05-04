# Секреты и публичный репозиторий

Урок использует **сервисный аккаунт Google Cloud** (JSON с `private_key`). Такие файлы **нельзя** коммитить.

## Что не попадает в git

- Любые ваши `*.json` с реальным ключом из GCP (в т.ч. имена вида `excel-*-….json`).
- Файл удобно хранить как `service_account.json` в папке урока (**в `.gitignore`** через правило `*.json`).

## После клона

1. Скачайте ключ сервисного аккаунта в [Google Cloud Console](https://console.cloud.google.com/) (IAM → сервисные аккаунты → ключи).
2. Скопируйте [`service_account.example.json`](service_account.example.json) → **`service_account.json`** и вставьте значения из скачанного файла (или положите скачанный JSON под именем `service_account.json`).
3. Добавьте `client_email` из JSON в таблицу Google Sheets с ролью **Редактор**.

Если ключ когда‑либо оказался в истории git: **удалите** его из истории (`git filter-repo` / BFG) и **перевыпустите** ключ в GCP.
