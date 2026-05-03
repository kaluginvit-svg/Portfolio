# Урок LangChain 2 — агент с инструментами

Учебный проект по **LangChain**: агент на `create_agent`, два tool (из урока и свой), структурированный ответ и память диалога через checkpoint.

## Зачем это

Демонстрация паттерна «LLM + tools + structured output» из урока (VPg03): модель сама выбирает инструмент, ответ приводится к схеме `WeatherResponse`, история для одного `thread_id` сохраняется в памяти чекпоинтера.

## Стек

| Компонент | Назначение |
|-----------|------------|
| Python 3.11+ | Запуск скрипта |
| `langchain` | `create_agent` |
| `langchain-openai` | `ChatOpenAI` |
| `langgraph` | `MemorySaver` (checkpoint) |
| `pydantic` v2 | Схема `WeatherResponse` |
| `python-dotenv` | Загрузка `.env` |

Зависимости: файл `requirements_lesson_agent.txt`.

## Структура репозитория

```
.
├── lesson_agent.py              # точка входа: агент, tools, invoke
├── requirements_lesson_agent.txt
├── .env                         # ключи и URL (не коммитьте в открытый репозиторий)
└── README.md
```

## Установка

В каталоге урока:

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements_lesson_agent.txt
```

Создайте `.env` рядом с `lesson_agent.py` (без файла скрипт завершится с сообщением «Нет .env»).

Пример переменных:

```env
PROXY_API=ваш-ключ
URL=https://api.openai.com/v1
MODEL_NAME=gpt-4o-mini
TEMPERATURE=0.2
```

Для совместимого с OpenAI прокси или локального сервера достаточно поменять `URL` и при необходимости `MODEL_NAME`.

## Запуск

```bash
python lesson_agent.py
```

Скрипт последовательно отправляет два тестовых запроса и печатает **`structured_response`** для каждого:

1. Вопрос о погоде — ожидается использование `get_weather_for_location`.
2. Подсчёт слов во фразе — ожидается вызов `count_words`.

При ошибке аутентификации проверьте `PROXY_API` и `URL`. Коды **402 / 429** обрабатываются с подсказкой про баланс или лимит.

## Что внутри `lesson_agent.py`

- **`get_weather_for_location`** — tool «как в уроке», пока заглушка с фиксированным текстом о погоде.
- **`count_words`** — свой tool: число «слов» по разбиению строки пробелами (грубая оценка длины ТЗ).
- **`WeatherResponse`** — поле `weather_conditions`: строка или `None`, если тема не про погоду (по задумке урока).
- **`MemorySaver`** и один `thread_id` — чтобы при расширении скрипта сохранялся контекст беседы в рамках потока.

Системный промпт короткий: по-русски; какой tool для чего — явно указан.

## Идеи для доработки

Заменить заглушку погоды на реальный API, уточнить разбиение слов (регулярки, языки), добавить аргументы командной строки для своих запросов вместо захардкоженных строк в `main()`.
