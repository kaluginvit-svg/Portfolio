# Погода-API

Консольное приложение для получения текущей погоды через [OpenWeather API](https://openweathermap.org/api).

## Возможности

- **Погода по городу** — ввод названия города, геокодинг и вывод погоды
- **Погода по координатам** — ввод широты и долготы
- Кэширование ответов (3 часа)
- Повторные запросы при сетевых ошибках и лимитах API

## Установка

1. Клонируйте репозиторий и перейдите в папку проекта.

2. Создайте виртуальное окружение:
```bash
python -m venv venv
```

3. Активируйте виртуальное окружение:
   - Windows: `venv\Scripts\activate`
   - Linux/Mac: `source venv/bin/activate`

4. Установите зависимости:
```bash
pip install -r requirements.txt
```

5. Скопируйте пример настроек и укажите API-ключ:
```bash
copy .env.example .env
```
Откройте `.env` и подставьте свой ключ OpenWeather (получить бесплатно: https://openweathermap.org/api).

## Использование

Запуск:
```bash
python main.py
```

В меню:
- **1** — погода по названию города
- **2** — погода по координатам (широта, долгота)
- **0** — выход

## Технологии

- Python 3.11+
- Requests — HTTP-запросы к API
- python-dotenv — загрузка `API_KEY` из `.env`

## API

Используется [OpenWeather API](https://openweathermap.org/api): геокодинг и текущая погода (units=metric, lang=ru).
