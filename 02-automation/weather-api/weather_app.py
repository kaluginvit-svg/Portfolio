"""
Приложение для получения текущей погоды через OpenWeather API.
Поддерживает запрос по городу или координатам, кэширование, ретраи при ошибках.
"""
import os
import json
import time
from datetime import datetime
from dotenv import load_dotenv
import requests

load_dotenv()
API_KEY = os.getenv("API_KEY")

CACHE_FILE = "weather_cache.json"
CACHE_MAX_AGE_SEC = 3 * 3600  # 3 часа
MAX_RETRIES = 3
RETRY_DELAYS = [1, 2, 4]  # секунды для экспоненциальной паузы


def get_coordinates(city: str) -> tuple[float, float]:
    """
    Получает координаты (широта, долгота) по названию города через геокодинг OpenWeather.
    Использует limit=5 для получения нескольких вариантов. Если найдено несколько городов,
    возвращает координаты первого (самого популярного).
    """
    if not API_KEY:
        raise ValueError("API_KEY не найден в .env файле. Получите ключ на https://openweathermap.org/api")
    
    # Убираем lang=ru из геокодинга, так как он может ограничивать поиск
    url = f"http://api.openweathermap.org/geo/1.0/direct?q={city}&limit=5&appid={API_KEY}"
    
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0:
                    # Если найдено несколько городов, показываем список и выбираем первый
                    if len(data) > 1:
                        print(f"\nНайдено {len(data)} вариантов:")
                        for i, item in enumerate(data[:5], 1):
                            country = item.get("country", "")
                            state = item.get("state", "")
                            name = item.get("name", "")
                            location = f"{name}"
                            if state:
                                location += f", {state}"
                            if country:
                                location += f", {country}"
                            print(f"  {i}. {location}")
                        print(f"Используется первый вариант: {data[0].get('name', '')}, {data[0].get('country', '')}")
                    return data[0]["lat"], data[0]["lon"]
                else:
                    # Пробуем поиск без дополнительных параметров
                    alt_url = f"http://api.openweathermap.org/geo/1.0/direct?q={city}&limit=5&appid={API_KEY}"
                    alt_response = requests.get(alt_url, timeout=10)
                    if alt_response.status_code == 200:
                        alt_data = alt_response.json()
                        if alt_data and len(alt_data) > 0:
                            return alt_data[0]["lat"], alt_data[0]["lon"]
                    raise ValueError(f"Город '{city}' не найден. Попробуйте указать страну через запятую, например: '{city}, Russia'")
            elif response.status_code == 401:
                error_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
                error_msg = error_data.get("message", "Неверный API-ключ")
                raise ValueError(f"Ошибка авторизации (401): {error_msg}. Проверьте API_KEY в .env файле.")
            elif response.status_code == 429:
                if attempt < MAX_RETRIES - 1:
                    delay = RETRY_DELAYS[attempt]
                    print(f"Превышен лимит запросов (429). Повтор через {delay} сек...")
                    time.sleep(delay)
                    continue
                else:
                    raise ValueError("Превышен лимит запросов. Попробуйте позже.")
            else:
                error_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
                error_msg = error_data.get("message", f"HTTP {response.status_code}")
                raise ValueError(f"Ошибка геокодинга ({response.status_code}): {error_msg}")
        except requests.exceptions.RequestException as e:
            if attempt < MAX_RETRIES - 1:
                delay = RETRY_DELAYS[attempt]
                print(f"Ошибка сети: {e}. Повтор через {delay} сек...")
                time.sleep(delay)
                continue
            else:
                raise ValueError(f"Ошибка сети после {MAX_RETRIES} попыток: {e}")
    
    raise ValueError("Не удалось получить координаты")


def get_weather_by_coordinates(lat: float, lon: float) -> dict:
    """
    Получает текущую погоду по координатам (широта, долгота).
    Использует units=metric и lang=ru.
    Возвращает словарь с данными погоды.
    """
    if not API_KEY:
        raise ValueError("API_KEY не найден в .env файле. Получите ключ на https://openweathermap.org/api")
    
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric&lang=ru"
    
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 401:
                error_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
                error_msg = error_data.get("message", "Неверный API-ключ")
                raise ValueError(f"Ошибка авторизации (401): {error_msg}. Проверьте API_KEY в .env файле.")
            elif response.status_code == 429:
                if attempt < MAX_RETRIES - 1:
                    delay = RETRY_DELAYS[attempt]
                    print(f"Превышен лимит запросов (429). Повтор через {delay} сек...")
                    time.sleep(delay)
                    continue
                else:
                    raise ValueError("Превышен лимит запросов. Попробуйте позже.")
            else:
                error_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
                error_msg = error_data.get("message", f"HTTP {response.status_code}")
                raise ValueError(f"Ошибка получения погоды ({response.status_code}): {error_msg}")
        except requests.exceptions.RequestException as e:
            if attempt < MAX_RETRIES - 1:
                delay = RETRY_DELAYS[attempt]
                print(f"Ошибка сети: {e}. Повтор через {delay} сек...")
                time.sleep(delay)
                continue
            else:
                raise ValueError(f"Ошибка сети после {MAX_RETRIES} попыток: {e}")
    
    raise ValueError("Не удалось получить погоду")


def save_cache(weather_data: dict, city: str = None, lat: float = None, lon: float = None) -> None:
    """Сохраняет успешный ответ в кэш с метаданными."""
    cache_data = {
        "city": city,
        "lat": lat,
        "lon": lon,
        "fetched_at": datetime.now().isoformat(),
        "weather": weather_data
    }
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache_data, f, ensure_ascii=False, indent=2)


def load_cache() -> dict | None:
    """Загружает кэш, если он существует и валиден."""
    try:
        if not os.path.exists(CACHE_FILE):
            return None
        
        mtime = os.path.getmtime(CACHE_FILE)
        if (time.time() - mtime) >= CACHE_MAX_AGE_SEC:
            return None
        
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            cache_data = json.load(f)
            return cache_data
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None


def format_weather_output(weather_data: dict, lat: float = None, lon: float = None) -> str:
    """Форматирует данные погоды в читаемую строку."""
    city = weather_data.get("name", "Неизвестно")
    temp = weather_data.get("main", {}).get("temp", "N/A")
    description = weather_data.get("weather", [{}])[0].get("description", "нет данных")
    result = f"Погода в {city}: {temp}°C, {description}"
    if lat is not None and lon is not None:
        result += f"\nКоординаты: {lat}, {lon}"
    return result


def get_weather_by_city(city: str) -> tuple[dict, float, float]:
    """Получает погоду по названию города с кэшированием. Возвращает (weather, lat, lon)."""
    try:
        lat, lon = get_coordinates(city)
        weather = get_weather_by_coordinates(lat, lon)
        save_cache(weather, city=city, lat=lat, lon=lon)
        return weather, lat, lon
    except ValueError as e:
        cache = load_cache()
        if cache and cache.get("city", "").lower() == city.lower():
            print(f"Используем данные из кэша (возраст: {cache.get('fetched_at', 'неизвестно')})")
            weather = cache.get("weather")
            lat = cache.get("lat")
            lon = cache.get("lon")
            return weather, lat, lon
        raise


def get_weather_by_coords(lat: float, lon: float) -> dict:
    """Получает погоду по координатам с кэшированием."""
    try:
        weather = get_weather_by_coordinates(lat, lon)
        save_cache(weather, lat=lat, lon=lon)
        return weather
    except ValueError as e:
        cache = load_cache()
        if cache and abs(cache.get("lat", 0) - lat) < 0.01 and abs(cache.get("lon", 0) - lon) < 0.01:
            print(f"Используем данные из кэша (возраст: {cache.get('fetched_at', 'неизвестно')})")
            return cache.get("weather")
        raise


def main_cli() -> None:
    """Главная функция CLI с режимами ввода."""
    while True:
        try:
            print("\n" + "="*50)
            print("ПОГОДА - OpenWeather API")
            print("="*50)
            print("1 — по городу")
            print("2 — по координатам")
            print("0 — выход")
            
            choice = input("\nВаш выбор: ").strip()
            
            if choice == "0":
                print("Выход из программы.")
                break
            elif choice == "1":
                city = input("Введите название города: ").strip()
                if not city:
                    print("Название города не может быть пустым.")
                    continue
                try:
                    weather, lat, lon = get_weather_by_city(city)
                    print(format_weather_output(weather, lat=lat, lon=lon))
                except ValueError as e:
                    print(f"Ошибка: {e}")
            elif choice == "2":
                try:
                    lat_str = input("Введите широту: ").strip().replace(",", ".")
                    lon_str = input("Введите долготу: ").strip().replace(",", ".")
                    lat = float(lat_str)
                    lon = float(lon_str)
                    weather = get_weather_by_coords(lat, lon)
                    print(format_weather_output(weather, lat=lat, lon=lon))
                except ValueError as e:
                    print(f"Ошибка: {e}")
                except (TypeError, ValueError) as e:
                    print("Ошибка: неверный формат координат. Используйте числа.")
            else:
                print("Неверный выбор. Выберите 0, 1 или 2.")
        except (EOFError, KeyboardInterrupt):
            print("\nВвод отменён.")
            break
        except Exception as e:
            print(f"Неожиданная ошибка: {e}")


if __name__ == "__main__":
    main_cli()
