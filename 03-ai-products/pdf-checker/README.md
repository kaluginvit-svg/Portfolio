# PDF-чекер

> **Проблема:** бухгалтерии / операционке нужно массово генерировать PDF-чеки и счета по списку записей — корректно с кириллицей, без ручной правки шаблона под каждый случай.  
> **Решение:** утилита читает CSV/JSON, выбирает строку по `invoice_id`, рендерит HTML-шаблон с плейсхолдерами `{{ field }}` (включая вложенные `{{ customer.name }}`), печатает в PDF через WeasyPrint. Шрифт DejaVu Sans подкачивается сам.  
> **Стек:** Python, pandas, WeasyPrint, HTML-шаблоны с Jinja-стиль плейсхолдерами.  
> **Ценность:** готовая основа для массовой генерации счетов/актов из выгрузки из 1С/CRM; шаблон редактируется без затрагивания кода.

---

Утилита генерирует PDF-чеки по данным из CSV/JSON и HTML-шаблона. PDF строится через WeasyPrint, кириллица поддерживается шрифтом DejaVu Sans (скачивается автоматически).

## Структура
- `data/` — входные CSV/JSON.
- `templates/` — HTML-шаблоны с плейсхолдерами `{{ field }}`.
- `output/` — готовые PDF.
- `fonts/` — кэш скачанного DejaVu Sans.

## Установка
1) Python 3.9+.  
2) Создайте и активируйте виртуальное окружение:
   - Windows (PowerShell): `python -m venv .venv` и `.venv\Scripts\Activate.ps1`
   - Windows (cmd): `python -m venv .venv` и `.venv\Scripts\activate.bat`
   - macOS/Linux: `python3 -m venv .venv` и `source .venv/bin/activate`
3) Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```
   На Windows WeasyPrint может запросить GTK/WebKit (см. документацию WeasyPrint).

## Данные
- CSV: каждая строка — запись (читается pandas).
- JSON: список объектов либо объект, содержащий массив объектов.
- Поле идентификатора счета: одно из `invoice_id`, `invoice`, `invoiceid`, `id`.
- Вложенные словари разворачиваются в ключи с точкой: `customer.name` доступен как `{{ customer.name }}`.

## Шаблон
HTML с плейсхолдерами `{{ key }}`. Примеры: `{{ invoice_id }}`, `{{ total }}`, `{{ customer.name }}`.

## Запуск
```bash
python script.py
```
1) Выберите файл из `data/` и шаблон из `templates/` (нумерованное меню).  
2) Выберите нужный `invoice_id`.  
3) PDF сохранится в `output/` и откроется системной программой.

## Примечания
- При первом запуске шрифт DejaVu Sans скачивается в `fonts/` для корректной печати кириллицы.
- Имя файла PDF санитизируется: `invoice_<id>.pdf`.