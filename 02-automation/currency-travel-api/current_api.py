import os
import requests
from dotenv import load_dotenv

# Загружаем переменные из .env (EXCHANGERATE_API_KEY)
# Получить ключ: https://exchangerate.host (бесплатный тариф)
load_dotenv()
API_KEY = os.environ.get("EXCHANGERATE_API_KEY", "").strip()


def get_current_rate(
    default: str = "USD",
    currencies: list[str] = ["EUR", "GBP", "JPY"],
) -> dict:
    url = "https://api.exchangerate.host/live"
    params = {
        "access_key": API_KEY,
        "source": default,
        "currencies": ",".join(currencies)
        # ",".join(currencies) — объединение в строку с разделителем-запятой
    }

    response = requests.get(url, params=params)
    data = response.json()
    return data


def convert_currency(
    amount: float,
    from_currency: str,
    to_currency: str,
) -> dict:
    """Конвертация суммы из одной валюты в другую."""
    url = "https://api.exchangerate.host/convert"
    params = {
        "access_key": API_KEY,
        "from": from_currency,
        "to": to_currency,
        "amount": amount,
    }

    response = requests.get(url, params=params)
    data = response.json()
    return data


def get_rate(from_currency: str, to_currency: str) -> float | None:
    """
    Получить курс через endpoint /convert (amount=1).
    Возвращает курс или None при ошибке.
    """
    data = convert_currency(1.0, from_currency, to_currency)
    if data.get("success") and "result" in data:
        return float(data["result"])
    return None


if __name__ == "__main__":
    if not API_KEY:
        print("Предупреждение: задайте EXCHANGERATE_API_KEY в файле .env")
        print("Получить ключ: https://exchangerate.host")
    # Пример: курс рубля относительно USD, EUR, GBP, JPY, CNY
    data = get_current_rate(default="RUB", currencies=["USD", "EUR", "GBP", "JPY", "CNY"])
    print(data["quotes"])
