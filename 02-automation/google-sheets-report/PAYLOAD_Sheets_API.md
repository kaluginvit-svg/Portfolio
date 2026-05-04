# Какие нужны payload (запросы к Google Sheets API)

Локально «секреты» приходят из **JSON ключ сервисного аккаунта** (`private_key`, `client_email`, `type: service_account`).

В код передаём путь к файлу ключей; ключ не кладём в репозиторий.

## Идентификаторы (почти во всех вызовах)

| Параметр | Откуда | Пример |
|----------|--------|--------|
| `spreadsheetId` | URL таблицы | `docs.google.com/.../d/{spreadsheetId}/edit` |
| `range` (A1) | Вы сами задаёте | `'Лист1'!A1:D10` |
| `valueInputOption` | Для записи значений | `USER_ENTERED` или `RAW` |

## Values API — тело с данными (`values`)

Все операции записи принимают **двумерный массив**:

```json
{
  "values": [
    ["Заголовок", "", ""],
    ["Колонка1", "Колонка2", "Колонка3"],
    [1, 2, 3]
  ]
}
```

Правило из урока: **размер `values` (строк × столбцов) должен соответствовать выбранному диапазону** или логике `append`.

### `spreadsheets.values.update`

- **Параметры URL/клиента:** `spreadsheetId`, `range`, `valueInputOption`
- **Тело:** `{ "values": [[...], [...]] }`

### `spreadsheets.values.append`

- **Параметры:** `spreadsheetId`, `range` (якорь области), `valueInputOption`, часто `insertDataOption=INSERT_ROWS`
- **Тело:** `{ "values": [[...]] }`

### `spreadsheets.values.clear`

- **Параметры:** `spreadsheetId`, `range`
- **Тело:** обычно `{}`

## Метаданные и создание листа

### `spreadsheets.get`

- **Параметры:** `spreadsheetId`
- Ответ содержит `sheets[].properties.sheetId` — нужен для `batchUpdate` (форматирование).

### `spreadsheets.batchUpdate`

- **Тело:** `{ "requests": [ {...}, {...} ] }`
- Здесь передаются `mergeCells`, `repeatCell`, `addSheet` и т.д. — это **payload форматирования** из ДЗ («цвета, шрифты, объединение ячеек»).
