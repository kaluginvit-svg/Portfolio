"""
HTTP-клиент для open.er-api.com v6/latest.
"""
import json
import requests


def get_currency_rates(base: str) -> dict:
    """
    GET https://open.er-api.com/v6/latest/{base}.
    При status_code != 200 или ошибке API возвращает dict с ключом "error".
    Иначе — полный ответ API (в т.ч. result, base_code, rates).
    """
    url = f"https://open.er-api.com/v6/latest/{base}"
    try:
        response = requests.get(url, timeout=10)
    except requests.exceptions.RequestException as e:
        return {"result": "error", "error": f"Ошибка сети: {e}"}
    if response.status_code != 200:
        msg = {
            400: "Неверный запрос (возможно, неизвестный код валюты)",
            429: "Слишком много запросов. Подождите перед повтором.",
            500: "Ошибка сервера. Попробуйте позже.",
        }.get(response.status_code, f"Ошибка HTTP {response.status_code}")
        return {"result": "error", "error": msg}
    try:
        data = response.json()
    except json.JSONDecodeError:
        return {"result": "error", "error": "Неверный ответ сервера (не JSON)"}
    if data.get("result") == "error":
        return {"result": "error", "error": data.get("error-type", "Неизвестная ошибка API")}
    return data
