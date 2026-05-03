"""
Модуль для работы с OpenWeather API.
"""
import hashlib
import json
import logging
import os
import re
import time
from dotenv import load_dotenv
import requests

logger = logging.getLogger(__name__)

load_dotenv()
OW_API_KEY = os.getenv("OW_API_KEY")

BASE_URL = "https://api.openweathermap.org"
MAX_RETRIES = 3
RETRY_DELAYS = (1, 2, 4)
CACHE_FILE = "weather_cache.json"
CACHE_TTL = 600


def _cache_key(endpoint: str, params: dict) -> str:
    ep = re.sub(r"[^\w]", "_", endpoint).strip("_")
    if "lat" in params and "lon" in params:
        return f"{ep}_{params['lat']}_{params['lon']}"
    h = hashlib.md5(json.dumps(params, sort_keys=True).encode()).hexdigest()[:12]
    return f"{ep}_{h}"


def _cache_get(key: str):
    try:
        if not os.path.isfile(CACHE_FILE):
            return None
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            store = json.load(f)
        if not isinstance(store, dict):
            return None
        entry = store.get(key)
        if entry is None or (time.time() - entry.get("timestamp", 0)) > CACHE_TTL:
            return None
        return entry.get("data")
    except (OSError, json.JSONDecodeError, KeyError):
        return None


def _cache_set(key: str, data) -> None:
    try:
        store = {}
        if os.path.isfile(CACHE_FILE):
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                store = json.load(f)
        if not isinstance(store, dict):
            store = {}
        store[key] = {"timestamp": time.time(), "data": data}
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(store, f, ensure_ascii=False, indent=None)
    except OSError:
        pass


def call_openweather(endpoint: str, params: dict) -> dict | list | None:
    if not OW_API_KEY:
        logger.warning("OW_API_KEY не задан (проверьте .env)")
        return None
    key = _cache_key(endpoint, params)
    cached = _cache_get(key)
    if cached is not None:
        return cached
    url = f"{BASE_URL.rstrip('/')}/{endpoint.lstrip('/')}"
    q = {**params, "appid": OW_API_KEY}
    for attempt in range(MAX_RETRIES):
        try:
            r = requests.get(url, params=q, timeout=10)
            if r.status_code == 200:
                try:
                    data = r.json()
                except json.JSONDecodeError as e:
                    logger.error("OpenWeather JSON decode error: %s", e)
                    return None
                _cache_set(key, data)
                return data
            if r.status_code == 429 and attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAYS[attempt])
                continue
            logger.warning("OpenWeather HTTP %s for %s", r.status_code, endpoint)
            return None
        except requests.exceptions.RequestException as e:
            logger.warning("OpenWeather request error (attempt %s): %s", attempt + 1, e)
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAYS[attempt])
                continue
            return None
    return None


def get_coordinates(city: str, limit: int = 1) -> tuple[float, float] | None:
    data = call_openweather("geo/1.0/direct", {"q": city, "limit": limit, "lang": "ru"})
    if not data or not isinstance(data, list) or len(data) == 0:
        return None
    first = data[0]
    try:
        return (float(first["lat"]), float(first["lon"]))
    except (KeyError, TypeError, ValueError):
        return None


def get_current_weather(lat: float, lon: float) -> dict | None:
    data = call_openweather(
        "data/2.5/weather",
        {"lat": lat, "lon": lon, "units": "metric", "lang": "ru"},
    )
    return data if isinstance(data, dict) else None


def get_forecast_5d3h(lat: float, lon: float) -> list[dict] | None:
    data = call_openweather(
        "data/2.5/forecast",
        {"lat": lat, "lon": lon, "units": "metric", "lang": "ru"},
    )
    if not isinstance(data, dict):
        return None
    lst = data.get("list")
    return lst if isinstance(lst, list) else None


def get_air_pollution(lat: float, lon: float) -> dict | None:
    data = call_openweather("data/2.5/air_pollution", {"lat": lat, "lon": lon})
    if not isinstance(data, dict):
        return None
    lst = data.get("list")
    if not lst or not isinstance(lst, list):
        return None
    comp = lst[0].get("components") if lst else None
    return comp if isinstance(comp, dict) else None


WEATHER_DESC_EN_RU: dict[str, str] = {
    "clear sky": "ясно",
    "few clouds": "небольшая облачность",
    "scattered clouds": "рассеянные облака",
    "broken clouds": "облачно с прояснениями",
    "overcast clouds": "пасмурно",
    "shower rain": "ливень",
    "rain": "дождь",
    "light rain": "небольшой дождь",
    "moderate rain": "умеренный дождь",
    "thunderstorm": "гроза",
    "snow": "снег",
    "light snow": "небольшой снег",
    "mist": "дымка",
    "fog": "туман",
    "haze": "мгла",
    "drizzle": "морось",
    "light intensity drizzle": "слабая морось",
    "heavy intensity rain": "сильный дождь",
    "very heavy rain": "очень сильный дождь",
    "freezing rain": "ледяной дождь",
    "light intensity shower rain": "небольшой ливень",
    "heavy intensity shower rain": "сильный ливень",
    "ragged shower rain": "ливень с прояснениями",
}


def localize_weather_description(desc: str) -> str:
    if not desc or not isinstance(desc, str):
        return "—"
    key = desc.strip().lower()
    return WEATHER_DESC_EN_RU.get(key, desc)


_AQ_THRESHOLDS = {
    "pm2_5": (12, 35, 55),
    "pm10": (20, 50, 100),
    "no2": (40, 100, 200),
    "o3": (60, 100, 140),
    "so2": (20, 80, 250),
    "co": (4400, 9400, 20000),
}
_AQ_LABELS = ("Хорошо", "Удовлетворительно", "Вредно для чувствительных", "Вредно")
_AQ_COMMENTS = {
    "pm2_5": ("низкая", "умеренная", "повышенная", "высокая"),
    "pm10": ("низкая", "умеренная", "повышенная", "высокая"),
    "no2": ("низкий", "умеренный", "повышенный", "высокий"),
    "o3": ("низкий", "умеренный", "повышенный", "высокий"),
    "so2": ("низкий", "умеренный", "повышенный", "высокий"),
    "co": ("низкий", "умеренный", "повышенный", "высокий"),
}


def _level(value: float, thresholds: tuple) -> int:
    try:
        v = float(value)
    except (TypeError, ValueError):
        return 0
    for i, t in enumerate(thresholds):
        if v <= t:
            return i
    return len(thresholds)


def analyze_air_pollution(components: dict | None, extended: bool = False) -> dict:
    if components is None:
        return {"status": "нет данных", "details": {}}
    details = {}
    worst = 0
    for key, thresholds in _AQ_THRESHOLDS.items():
        val = components.get(key)
        lv = _level(val, thresholds) if val is not None else 0
        if lv > worst:
            worst = lv
        if extended:
            comments = _AQ_COMMENTS.get(key, ("—",) * 4)
            details[key] = {
                "value": val,
                "status": _AQ_LABELS[min(lv, len(_AQ_LABELS) - 1)],
                "comment": comments[min(lv, len(comments) - 1)] + " уровень",
            }
    status = _AQ_LABELS[min(worst, len(_AQ_LABELS) - 1)]
    return {"status": status, "details": details}
