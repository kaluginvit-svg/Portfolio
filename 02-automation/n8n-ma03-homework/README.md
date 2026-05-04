# ДЗ MA03: BPMN → Miro

**Что это:** скрипт **`service_desk_to_miro.py`** строит BPMN-процесс «возврат / претензия» (Retail) и выгружает его на **доску Miro** через API.

**Стек:** Python, `requests`, токен `MIRO_ACCESS_TOKEN` в `.env` (см. заголовок скрипта).

**Запуск:**

```bash
pip install requests
python service_desk_to_miro.py
```

Опционально: `MIRO_BOARD_URL` в `.env` или ввод URL при запросе.

**Статус:** учебное задание по модулю n8n/процессам; для воспроизведения нужна учётная запись Miro с правами на доску.
