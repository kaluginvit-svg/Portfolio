# Автоматический отчёт в Google Sheets

Публичная выкладка: в репозиторий **не** коммитьте JSON-ключи GCP; в проекте только [`service_account.example.json`](service_account.example.json). См. [`SECURITY.md`](SECURITY.md).

Модуль [`google_sheets.py`](google_sheets.py) (CRUD + форматирование) и симулятор [`report_generator.py`](report_generator.py) (tkinter).

Подробности по заданию — на платформе курса (ZeroCoder).  
Чек-лист Cloud/таблица: [`GCP_и_таблица.md`](GCP_и_таблица.md).  
Описание payload API: [`PAYLOAD_Sheets_API.md`](PAYLOAD_Sheets_API.md).

Чеклист сдачи: [`Чеклист_сдачи.md`](Чеклист_сдачи.md).

## Установка

```bash
cd 02-automation/google-sheets-report
python -m pip install -r requirements.txt
```

## Запуск симулятора

Удобнее сразу передать **URL таблицы** (или только ID) в терминале — поле в окне будет заполнено и заблокировано:

```powershell
python report_generator.py "https://docs.google.com/spreadsheets/d/ВАШ_ID/edit"
# или переменная окружения:
$env:GOOGLE_SPREADSHEET_URL="https://docs.google.com/..."
python report_generator.py
```

При запуске без аргумента URL/ID можно ввести вручную в поле «Таблица».

Дальше в форме задаются заголовок, **даты периода**, подразделение, ответственный и т.д. — «Записать отчёт в Google Sheets» строит **оформленный «документ»** на листе (объединения, рамки, шапка, подвал).

Нужен **JSON сервисного аккаунта**; учётную запись из `client_email` добавьте к таблице как **Редактор**.

Подробнее: [GCP_и_таблица.md](GCP_и_таблица.md).

## Пример без GUI

[`start.py`](start.py) читает/пишет `Лист1` через тот же подход к ключу. Ключ см. выше; таблица: **`GOOGLE_SPREADSHEET_URL`** (полная ссылка) или **`GOOGLE_SPREADSHEET_ID`**.

## Сдача (без утечки секретов)

- Скриншот созданного листа с данными и форматированием **или** ссылку на таблицу с доступом для проверяющего (как принято на курсе).
- Краткий текст: что сделано, версия Python, как воспроизвести запуск.
- В архив/репозиторий **не** включать JSON ключ сервисного аккаунта; при желании добавьте пример без секретов.
