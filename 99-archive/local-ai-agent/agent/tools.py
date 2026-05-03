"""
Инструменты агента: поиск, HTTP, файлы, терминал, погода, крипта, валюты, QR.
"""
from __future__ import annotations

import json
import logging
import re
import subprocess
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import qrcode
import requests
from duckduckgo_search import DDGS
from langchain_core.tools import tool

# Корень проекта (родитель каталога agent/)
_AGENT_DIR = Path(__file__).resolve().parent
_WORKSPACE_ROOT = _AGENT_DIR.parent

_SESSION = requests.Session()
_SESSION.headers.update({"User-Agent": "LocalAIAgent/1.0"})

_log = logging.getLogger("local_agent.tools")


def _safe_workspace_path(relative_path: str) -> Path:
    """Путь только внутри рабочей области проекта."""
    rel = relative_path.strip().replace("\\", "/").lstrip("/")
    if ".." in rel.split("/"):
        raise ValueError("Путь не должен содержать '..'.")
    base = _WORKSPACE_ROOT.resolve()
    full = (base / rel).resolve()
    try:
        full.relative_to(base)
    except ValueError as e:
        raise ValueError("Доступ только к файлам внутри каталога проекта.") from e
    return full


_DANGEROUS_TERMINAL = re.compile(
    r"(;|\|\||`|\$\(|>|<|rm\s+-rf|mkfs|dd\s+if=|:(){ :|:& };|"
    r"format\s+|shutdown|reboot|wget\s+|curl\s+|powershell\s+-enc|"
    r"Invoke-Expression|base64\s+-d|certutil)",
    re.IGNORECASE,
)


def _terminal_command_safe(cmd: str) -> bool:
    if not cmd.strip():
        return False
    if _DANGEROUS_TERMINAL.search(cmd):
        return False
    return True


@tool
def web_search(query: str) -> str:
    """Поиск в интернете через DuckDuckGo. Используй для новостей, фактов, справки, когда нет специализированного инструмента."""
    q = (query or "").strip()
    _log.info("web_search: старт query=%r", q[:500])
    if not q:
        _log.warning("web_search: пустой запрос")
        return "Пустой запрос."
    try:
        with DDGS() as ddgs:
            hits = list(ddgs.text(q, max_results=6))
    except Exception as e:
        _log.warning("web_search: сбой DDGS: %s", e, exc_info=True)
        return f"Ошибка поиска: {e}"
    if not hits:
        _log.info("web_search: ноль результатов")
        return "Ничего не найдено."
    lines = []
    for i, h in enumerate(hits, 1):
        title = h.get("title", "")
        body = h.get("body", "")
        href = h.get("href", "")
        lines.append(f"{i}. {title}\n   {body}\n   {href}")
    out = "\n\n".join(lines)
    _log.info("web_search: готово, результатов=%s, длина текста=%s", len(hits), len(out))
    return out


@tool
def http_request(
    url: str,
    method: str = "GET",
    headers_json: str = "",
    body_json: str = "",
) -> str:
    """HTTP-запрос (GET/POST/PUT/PATCH/DELETE). headers_json и body_json — JSON-строки или пустые. Только http/https."""
    u = (url or "").strip()
    _log.info("http_request: старт method=%s url=%s", (method or "GET").upper(), u[:500])
    parsed = urlparse(u)
    if parsed.scheme not in ("http", "https"):
        _log.warning("http_request: отклонён scheme url=%s", u[:200])
        return "Разрешены только URL с http или https."
    m = (method or "GET").upper().strip()
    if m not in ("GET", "POST", "PUT", "PATCH", "DELETE", "HEAD"):
        _log.warning("http_request: неподдерживаемый метод %s", m)
        return f"Неподдерживаемый метод: {m}"
    hdrs: dict[str, str] = {}
    if headers_json.strip():
        try:
            hdrs = json.loads(headers_json)
            if not isinstance(hdrs, dict):
                return "headers_json должен быть JSON-объектом."
        except json.JSONDecodeError as e:
            return f"Неверный headers_json: {e}"
    data: Any = None
    json_body: Any = None
    if body_json.strip() and m in ("POST", "PUT", "PATCH"):
        try:
            json_body = json.loads(body_json)
        except json.JSONDecodeError as e:
            _log.warning("http_request: неверный body_json: %s", e)
            return f"Неверный body_json: {e}"
    _log.debug(
        "http_request: заголовки keys=%s json_body_type=%s",
        list(hdrs.keys()),
        type(json_body).__name__,
    )
    try:
        r = _SESSION.request(
            m,
            u,
            headers=hdrs,
            json=json_body,
            data=data,
            timeout=30,
        )
        text = r.text[:8000] if r.text else ""
        _log.info(
            "http_request: ответ status=%s len_body=%s",
            r.status_code,
            len(r.text or ""),
        )
        return f"status={r.status_code}\nheaders={dict(r.headers)}\n\n{text}"
    except requests.RequestException as e:
        _log.warning("http_request: сеть/HTTP ошибка: %s", e, exc_info=True)
        return f"Ошибка запроса: {e}"


@tool
def read_file(relative_path: str) -> str:
    """Читает текстовый файл относительно корня проекта (родитель папки agent/)."""
    _log.info("read_file: %s", relative_path)
    try:
        p = _safe_workspace_path(relative_path)
    except ValueError as e:
        _log.warning("read_file: небезопасный путь: %s", e)
        return str(e)
    if not p.is_file():
        _log.warning("read_file: нет файла %s", relative_path)
        return f"Файл не найден: {relative_path}"
    try:
        text = p.read_text(encoding="utf-8", errors="replace")[:50000]
        _log.info("read_file: прочитано символов=%s", len(text))
        return text
    except OSError as e:
        _log.warning("read_file: OSError %s", e, exc_info=True)
        return f"Не удалось прочитать: {e}"


@tool
def write_file(relative_path: str, content: str) -> str:
    """Записывает текст в файл (создаёт каталоги при необходимости). Путь относительно корня проекта."""
    clen = len(content or "")
    _log.info("write_file: %s символов=%s", relative_path, clen)
    try:
        p = _safe_workspace_path(relative_path)
    except ValueError as e:
        _log.warning("write_file: небезопасный путь: %s", e)
        return str(e)
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content or "", encoding="utf-8")
        _log.info("write_file: успех %s", p)
        return f"Записано: {relative_path} ({clen} символов)."
    except OSError as e:
        _log.warning("write_file: OSError %s", e, exc_info=True)
        return f"Ошибка записи: {e}"


@tool
def run_terminal_command(command: str) -> str:
    """Выполняет одну команду в shell в каталоге проекта. Ограничено: блокируются опасные конструкции и пайпы."""
    cmd = (command or "").strip()
    _log.info("run_terminal_command: %s", cmd[:500])
    if not _terminal_command_safe(cmd):
        _log.warning("run_terminal_command: отклонено политикой безопасности")
        return (
            "Команда отклонена политикой безопасности "
            "(пайпы, перенаправления, rm -rf и т.п. запрещены)."
        )
    try:
        # Windows: shell=True для встроенных команд (dir, type); ограничение — наш regex
        proc = subprocess.run(
            cmd,
            shell=True,
            cwd=str(_WORKSPACE_ROOT),
            capture_output=True,
            text=True,
            timeout=120,
            encoding="utf-8",
            errors="replace",
        )
        out = (proc.stdout or "") + (proc.stderr or "")
        if len(out) > 12000:
            out = out[:12000] + "\n...[обрезано]"
        _log.info(
            "run_terminal_command: exit=%s out_len=%s",
            proc.returncode,
            len(out or ""),
        )
        return f"exit={proc.returncode}\n{out or '(нет вывода)'}"
    except subprocess.TimeoutExpired:
        _log.warning("run_terminal_command: timeout")
        return "Превышено время выполнения (120 с)."
    except OSError as e:
        _log.warning("run_terminal_command: OSError %s", e, exc_info=True)
        return f"Ошибка запуска: {e}"


def _geocode_city(name: str) -> tuple[str, float, float]:
    """Название города → (label, lat, lon)."""
    n = (name or "").strip()
    if not n:
        raise ValueError("Укажите город.")
    geo = _SESSION.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={"name": n, "count": 1, "language": "ru"},
        timeout=15,
    )
    geo.raise_for_status()
    gj = geo.json()
    results = gj.get("results") or []
    if not results:
        raise ValueError(f"Город не найден: {n}")
    r0 = results[0]
    return (r0.get("name", n), float(r0["latitude"]), float(r0["longitude"]))


def get_weather_for_city(city: str) -> dict[str, Any]:
    """Геокодинг + текущая погода Open-Meteo."""
    name = (city or "").strip()
    _log.info("get_weather_for_city: %r", name)
    label, lat, lon = _geocode_city(name)
    _log.debug("geocoding: %s lat=%s lon=%s", label, lat, lon)
    w = _SESSION.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": lat,
            "longitude": lon,
            "current_weather": "true",
        },
        timeout=15,
    )
    w.raise_for_status()
    _log.debug("forecast: status=%s", w.status_code)
    wj = w.json()
    cw = wj.get("current_weather") or {}
    _log.info(
        "get_weather_for_city: t=%s wind=%s code=%s",
        cw.get("temperature"),
        cw.get("windspeed"),
        cw.get("weathercode"),
    )
    return {
        "city": label,
        "latitude": lat,
        "longitude": lon,
        "temperature_c": cw.get("temperature"),
        "windspeed_kmh": cw.get("windspeed"),
        "winddirection_deg": cw.get("winddirection"),
        "weathercode": cw.get("weathercode"),
        "time": cw.get("time"),
    }


def _forecast_at_local_hour(
    label: str,
    lat: float,
    lon: float,
    local_date: str,
    hour: int,
) -> dict[str, Any]:
    """Почасовой прогноз Open-Meteo: локальная дата YYYY-MM-DD и час 0–23."""
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", local_date.strip()):
        raise ValueError(
            "Дата прогноза должна быть в формате YYYY-MM-DD (локальное время места)."
        )
    if hour < 0 or hour > 23:
        raise ValueError("Час должен быть от 0 до 23 (локальное время места).")
    local_date = local_date.strip()
    w = _SESSION.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": lat,
            "longitude": lon,
            "hourly": "temperature_2m,weathercode,windspeed_10m",
            "forecast_days": 16,
            "timezone": "auto",
        },
        timeout=20,
    )
    w.raise_for_status()
    wj = w.json()
    hourly = wj.get("hourly") or {}
    times: list[str] = hourly.get("time") or []
    temps = hourly.get("temperature_2m") or []
    codes = hourly.get("weathercode") or []
    winds = hourly.get("windspeed_10m") or []
    prefix = f"{local_date}T{hour:02d}:"
    idx = next((i for i, t in enumerate(times) if t.startswith(prefix)), None)
    if idx is None:
        avail = f"{times[0]} … {times[-1]}" if times else "нет рядов"
        raise ValueError(
            f"Нет слота прогноза на {local_date} {hour:02d}:00 (доступный диапазон: {avail})."
        )
    return {
        "city": label,
        "time_local": times[idx],
        "temperature_c": temps[idx] if idx < len(temps) else None,
        "weathercode": codes[idx] if idx < len(codes) else None,
        "windspeed_kmh": winds[idx] if idx < len(winds) else None,
    }


@tool
def get_weather(
    city: str,
    forecast_local_date: str = "",
    forecast_local_hour: int = -1,
) -> str:
    """Погода по городу (геокодинг Open-Meteo). Текущая: только city. Прогноз на конкретный час: укажи forecast_local_date=YYYY-MM-DD и forecast_local_hour=0-23 в локальном времени места (для «завтра в 12:00» сам вычисли календарную дату «завтра»). «Центр Москвы» → city=Москва."""
    city = (city or "").strip()
    h = forecast_local_hour if forecast_local_hour is not None else -1
    d_str = (forecast_local_date or "").strip()

    use_forecast = bool(d_str) and h >= 0
    if (d_str and h < 0) or (not d_str and h >= 0):
        return (
            "Для прогноза на час нужны оба параметра: "
            "forecast_local_date (YYYY-MM-DD) и forecast_local_hour (0–23) "
            "в часовом поясе города."
        )

    try:
        if not use_forecast:
            d = get_weather_for_city(city)
            return (
                f"Город: {d['city']} (текущая погода)\n"
                f"Температура: {d['temperature_c']} °C\n"
                f"Ветер: {d['windspeed_kmh']} км/ч, направление: {d['winddirection_deg']}°\n"
                f"Код погоды (WMO): {d['weathercode']}\n"
                f"Время снимка: {d['time']}"
            )
        label, lat, lon = _geocode_city(city)
        _log.info(
            "get_weather: прогноз %s %s %02d:00 локальное",
            label,
            d_str,
            h,
        )
        d = _forecast_at_local_hour(label, lat, lon, d_str, h)
        return (
            f"Город: {d['city']} (прогноз по локальному времени места)\n"
            f"Время (локальное): {d['time_local']}\n"
            f"Температура: {d['temperature_c']} °C\n"
            f"Ветер: {d['windspeed_kmh']} км/ч\n"
            f"Код погоды (WMO): {d['weathercode']}"
        )
    except Exception as e:
        _log.warning("get_weather: ошибка для %r: %s", city, e, exc_info=True)
        return f"Ошибка погоды: {e}"


def get_crypto_price(coin: str, currency: str) -> float:
    """CoinGecko: coin — id (bitcoin, ethereum), currency — usd, eur, rub."""
    cid = (coin or "").strip().lower()
    cur = (currency or "usd").strip().lower()
    _log.info("get_crypto_price: id=%s vs=%s", cid, cur)
    if not cid or not cur:
        raise ValueError("Нужны coin и currency.")
    r = _SESSION.get(
        "https://api.coingecko.com/api/v3/simple/price",
        params={"ids": cid, "vs_currencies": cur},
        timeout=20,
    )
    r.raise_for_status()
    data = r.json()
    if cid not in data or cur not in data[cid]:
        _log.warning("get_crypto_price: нет пары в ответе keys=%s", list(data.keys()))
        raise ValueError(f"Нет данных для {cid} в {cur}. Проверь id на coingecko.com.")
    price = float(data[cid][cur])
    _log.info("get_crypto_price: %s", price)
    return price


@tool
def crypto_price_tool(coin_id: str, vs_currency: str = "usd") -> str:
    """Цена криптовалюты через CoinGecko. coin_id: bitcoin, ethereum, solana; vs_currency: usd, eur, rub."""
    try:
        price = get_crypto_price(coin_id, vs_currency)
    except Exception as e:
        _log.warning(
            "crypto_price_tool: %s/%s — %s",
            coin_id,
            vs_currency,
            e,
            exc_info=True,
        )
        return f"Ошибка: {e}"
    return f"{coin_id} / {vs_currency.upper()}: {price}"


def _fetch_fiat_rates_map(base: str) -> tuple[str, dict[str, float]]:
    """Курсы: 1 единица base = X quote (currency-api через jsDelivr). Возвращает (дата, словарь)."""
    b = (base or "").strip().lower()
    if len(b) != 3 or not b.isalpha():
        raise ValueError("Код базовой валюты — 3 латинские буквы ISO 4217 (например USD, EUR, RUB).")
    url = (
        "https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/"
        f"v1/currencies/{b}.json"
    )
    r = _SESSION.get(url, timeout=25)
    r.raise_for_status()
    data = r.json()
    as_of = str(data.get("date") or "—")
    block = data.get(b)
    if not isinstance(block, dict):
        raise ValueError("Неожиданный ответ сервиса курсов.")
    out: dict[str, float] = {}
    for k, v in block.items():
        if isinstance(v, (int, float)):
            out[str(k).lower()] = float(v)
    if not out:
        raise ValueError("Пустой список курсов.")
    return as_of, out


@tool
def get_fiat_exchange_rates(
    base_currency: str,
    target_currencies: str,
    amount: float = 1.0,
) -> str:
    """Курсы обычных (фиатных) валют: USD, EUR, RUB и др. base_currency — одна база. target_currencies — коды через запятую (EUR,RUB). amount — сколько единиц базы пересчитать (по умолчанию 1). Не путать с криптой — для неё crypto_price_tool."""
    base = (base_currency or "").strip()
    raw_targets = (target_currencies or "").strip()
    _log.info(
        "get_fiat_exchange_rates: base=%s targets=%s amount=%s",
        base,
        raw_targets,
        amount,
    )
    try:
        amt = float(amount)
    except (TypeError, ValueError):
        return "amount должен быть числом."
    if amt <= 0:
        return "amount должен быть положительным."
    targets = [t.strip().lower() for t in raw_targets.split(",") if t.strip()]
    if not targets:
        return "Укажите target_currencies, например: EUR,RUB"
    try:
        as_of, rates = _fetch_fiat_rates_map(base)
    except Exception as e:
        _log.warning("get_fiat_exchange_rates: API %s", e, exc_info=True)
        return f"Ошибка курсов: {e}"
    lines = [f"База: {base.upper()}, дата курсов (по данным API): {as_of}"]
    for t in targets:
        if t == base.lower():
            lines.append(f"{t.upper()}: 1 {base.upper()} = 1 {t.upper()} (та же валюта)")
            continue
        rate = rates.get(t)
        if rate is None:
            lines.append(f"{t.upper()}: курс недоступен в ответе (проверь код валюты).")
            continue
        converted = amt * rate
        lines.append(
            f"{t.upper()}: 1 {base.upper()} = {rate} {t.upper()} | "
            f"{amt} {base.upper()} = {converted:.6g} {t.upper()}"
        )
    return "\n".join(lines)


@tool
def generate_qr_code(content: str, relative_path: str) -> str:
    """Сохраняет QR-код в PNG внутри проекта. content — текст или URL. relative_path — путь от корня проекта, только .png (например qrcodes/pay.png)."""
    data = content or ""
    _log.info(
        "generate_qr_code: len(content)=%s path=%s",
        len(data),
        relative_path,
    )
    if len(data) > 2048:
        return "Текст для QR слишком длинный (макс. 2048 символов)."
    try:
        p = _safe_workspace_path(relative_path)
    except ValueError as e:
        _log.warning("generate_qr_code: путь %s", e)
        return str(e)
    if p.suffix.lower() != ".png":
        return "Укажите файл с расширением .png"
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=2,
        )
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        img.save(str(p))
    except Exception as e:
        _log.warning("generate_qr_code: %s", e, exc_info=True)
        return f"Не удалось создать QR: {e}"
    _log.info("generate_qr_code: сохранено %s", p)
    return f"QR сохранён: {relative_path} ({len(data)} символов)."


def all_tools():
    return [
        web_search,
        http_request,
        read_file,
        write_file,
        run_terminal_command,
        get_weather,
        crypto_price_tool,
        get_fiat_exchange_rates,
        generate_qr_code,
    ]
