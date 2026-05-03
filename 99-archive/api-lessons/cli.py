"""
Консольный интерфейс: курсы по базе (RUB, EUR, GBP), конвертер суммы, валидация кодов.
"""
import api_client
import storage

BASE_FOR_RATES = "USD"
DEFAULT_PATH = "currency_rate.json"
DECIMAL_PLACES = 4
RATES_DISPLAY_CODES = ["RUB", "EUR", "GBP"]


def _load_rates_for_base(base: str, path: str = DEFAULT_PATH) -> tuple[dict | None, str | None]:
    """
    Загружает данные для одной базы (base_code, rates).
    Если файл есть и моложе 24 часов и в нём есть эта база — читает из файла, иначе — обновляет через API.
    Возвращает (data с полями base_code и rates, error_message).
    """
    base = (base or "USD").strip().upper()
    if storage.cache_fresh(path) and storage.read_from_file(path):
        raw = storage.read_from_file(path)
        data = storage.get_rates_for_base(raw, base)
        if data and data.get("rates") is not None:
            return data, None
    data = api_client.get_currency_rates(base)
    if data.get("result") == "error":
        return None, data.get("error", "Неизвестная ошибка")
    storage.save_to_file(data, path)
    return data, None


def _load_rates(path: str = DEFAULT_PATH) -> tuple[dict | None, str | None]:
    """
    Загружает словарь rates (код валюты -> курс к базе).
    Возвращает (rates, error_message). error_message не None при ошибке.
    """
    if storage.cache_fresh(path) and storage.read_from_file(path):
        raw = storage.read_from_file(path)
        data = storage.get_rates_for_base(raw, BASE_FOR_RATES)
        if data and data.get("rates"):
            return data["rates"], None
    data = api_client.get_currency_rates(BASE_FOR_RATES)
    if data.get("result") == "error":
        return None, data.get("error", "Неизвестная ошибка")
    storage.save_to_file(data, path)
    return data.get("rates") or {}, None


def _validate_code(code: str, rates: dict) -> str | None:
    """Возвращает сообщение об ошибке, если код невалиден; иначе None."""
    code = (code or "").strip().upper()
    if not code:
        return "Не указан код валюты."
    if code not in rates:
        available = ", ".join(sorted(rates.keys())[:20]) + ("..." if len(rates) > 20 else "")
        return f"Код валюты «{code}» не найден. Доступные коды (rates.keys()): {available}"
    return None


def convert_amount(amount: float, from_code: str, to_code: str, rates: dict) -> float:
    """Конвертация суммы из from_code в to_code по rates (база USD). 4 знака после запятой."""
    return round(amount * (rates[to_code] / rates[from_code]), DECIMAL_PLACES)


def main_cli() -> None:
    try:
        _run_cli()
    except (EOFError, KeyboardInterrupt):
        print("\nВвод отменён.")
    except Exception as e:
        print(f"Ошибка: {e}")


def _run_rates_by_base() -> None:
    """Мини-CLI: ввод базовой валюты → вывод курсов для RUB, EUR, GBP. Кэш 24 ч."""
    base = input("Базовая валюта (например USD): ").strip().upper() or "USD"
    path = DEFAULT_PATH
    data, err = _load_rates_for_base(base, path)
    if err:
        print(f"Ошибка: {err}")
        return
    rates = data.get("rates") or {}
    print(f"\nКурс 1 {base} к выбранным валютам:")
    for code in RATES_DISPLAY_CODES:
        if code in rates:
            print(f"  {code}: {rates[code]}")
        else:
            print(f"  {code}: —")


def _run_cli() -> None:
    path = DEFAULT_PATH
    choice = input("1 — курсы по базе (RUB, EUR, GBP), 2 — конвертер суммы. Ваш выбор: ").strip() or "1"
    if choice == "1":
        _run_rates_by_base()
        return
    if choice != "2":
        print("Неверный выбор. Запустите снова.")
        return

    rates, err = _load_rates(path)
    if err:
        print(f"Ошибка загрузки курсов: {err}")
        return
    if not rates:
        print("Нет данных о курсах. Проверьте кэш или сеть.")
        return

    from_currency = input("\nИз валюты (код, например USD): ").strip().upper()
    to_currency = input("В валюту (код, например RUB): ").strip().upper()
    amount_str = input("Сумма: ").strip().replace(",", ".")

    msg = _validate_code(from_currency, rates)
    if msg:
        print(msg)
        return
    msg = _validate_code(to_currency, rates)
    if msg:
        print(msg)
        return

    try:
        amount = float(amount_str)
    except ValueError:
        print("Сумма должна быть числом.")
        return
    if amount < 0:
        print("Сумма не должна быть отрицательной.")
        return

    result = convert_amount(amount, from_currency, to_currency, rates)
    print(f"\n{amount} {from_currency} = {result} {to_currency}")


if __name__ == "__main__":
    main_cli()
