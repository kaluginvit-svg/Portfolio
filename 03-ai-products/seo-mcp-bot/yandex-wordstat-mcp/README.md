# Yandex Wordstat MCP Server

MCP сервер для работы с Yandex Wordstat API через FastAPI.

## Установка

### 1. Создайте виртуальное окружение

```bash
python -m venv .venv
```

### 2. Активируйте виртуальное окружение

**Windows:**
```bash
.venv\Scripts\activate
```

**Linux/macOS:**
```bash
source .venv/bin/activate
```

### 3. Установите зависимости

```bash
pip install -r requirements.txt
```

### 4. Настройте переменные окружения

Скопируйте `.env.example` в `.env` и укажите ваш OAuth токен:

```bash
# Windows
copy .env.example .env

# Linux/macOS
cp .env.example .env
```

Откройте `.env` и замените `ВАШ_OAUTH_ТОКЕН_ОТ_ЯНДЕКСА` на ваш реальный токен.

## Получение OAuth токена

1. Зарегистрируйтесь в [Yandex Cloud](https://yandex.cloud/)
2. Включите Search API → Wordstat
3. Создайте OAuth приложение: https://yandex.ru/support2/wordstat/ru/content/api-wordstat
4. Получите токен вида `y0_Ag...`

## Запуск

**Windows:**
```bash
python mcp_server.py
```

**Linux/macOS:**
```bash
./run.sh
```

## Настройка в Cursor

Добавьте в `C:\Users\Виталий\.cursor\mcp.json`:

```json
{
  "mcpServers": {
    "yandex-wordstat": {
      "command": "python",
      "args": ["C:\\_Рабочая_папка\\Проекты_программирование\\SEO-бот\\yandex-wordstat-mcp\\mcp_server.py"],
      "env": {
        "PYTHONUNBUFFERED": "1"
      }
    }
  }
}
```

**Важно:** Укажите полный путь к `mcp_server.py` в вашем проекте.

## Использование

После перезапуска Cursor, используйте в чате:

```
Используй MCP yandex-wordstat.
Вызови метод top_requests с phrase="искусственный интеллект", period="weekly", regions=[225].
```

## API методы

### `/v1/topRequests` - Популярные запросы
Получить данные за последние 30 дней о популярных запросах.

**Параметры:**
- `phrase` (string) - одна фраза ИЛИ
- `phrases` (array) - массив фраз (максимум 128)
- `numPhrases` (int) - количество в ответе (по умолчанию 50, максимум 2000)
- `regions` (array[int]) - список ID регионов ([213] - Москва, [2] - СПб, [225] - Россия)
- `devices` (array[string]) - типы устройств: `["all"]`, `["desktop"]`, `["phone"]`, `["tablet"]`

**Квота:** 1 единица на запрос

### `/v1/dynamics` - Динамика запросов
Получить динамику числа запросов во времени.

**Параметры:**
- `phrase` (обязательный) - фраза (допускается только оператор +)
- `period` (обязательный) - `"monthly"`, `"weekly"`, `"daily"`
- `fromDate` (обязательный) - начало периода (YYYY-MM-DD)
- `toDate` (опционально) - конец периода (YYYY-MM-DD)
- `regions` (array[int]) - список ID регионов
- `devices` (array[string]) - типы устройств

**Квота:** 1 единица на запрос

### `/v1/regions` - Распределение по регионам
Получить распределение запросов по регионам за последние 30 дней.

**Параметры:**
- `phrase` (обязательный) - фраза
- `regionType` (string) - `"cities"`, `"regions"`, `"all"` (по умолчанию `"all"`)
- `devices` (array[string]) - типы устройств

**Квота:** 2 единицы на запрос

### `/v1/getRegionsTree` - Дерево регионов
Получить список всех доступных регионов.

**Параметры:** нет

**Квота:** не расходует квоту

### `/v1/userInfo` - Информация о пользователе
Получить информацию о квотах и ограничениях.

**Параметры:** нет

**Квота:** не расходует квоту

## Получение токена

См. [GET_TOKEN.md](GET_TOKEN.md) для инструкции по получению OAuth токена.
