"""
Курс USD к RUB с официального ежедневного XML ЦБ РФ (cbr.ru).
Берётся курс на последнюю доступную дату публикации (выходные → последний рабочий день).
"""

from __future__ import annotations

import logging
import time
import xml.etree.ElementTree as ET
from datetime import date, timedelta
from decimal import Decimal
from typing import Final

import httpx

logger = logging.getLogger(__name__)

CBR_DAILY_XML: Final[str] = "https://www.cbr.ru/scripts/XML_daily.asp"
# Кэш: (unix_ts, курс за 1 USD, дата из ValCurs Date DD.MM.YYYY или None)
_cache: tuple[float, Decimal, str | None] | None = None
_CACHE_TTL_SEC: Final[int] = 3600
# Сколько дней назад опрашивать (выходные и праздники)
_MAX_LOOKBACK_DAYS: Final[int] = 14


def _decode_xml_body(raw: bytes) -> str:
    for encoding in ("windows-1251", "utf-8"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def _parse_usd_from_xml(text: str) -> tuple[Decimal, str | None]:
    """
    Парсит курс USD и дату сверки из атрибута Date у ValCurs (формат DD.MM.YYYY).
    """
    root = ET.fromstring(text)
    rate_date = root.get("Date")

    for valute in root.findall("Valute"):
        code_el = valute.find("CharCode")
        if code_el is None or (code_el.text or "").strip() != "USD":
            continue
        value_el = valute.find("Value")
        nominal_el = valute.find("Nominal")
        if value_el is None or not (value_el.text or "").strip():
            raise ValueError("CBR: не найдено значение курса USD")
        value = Decimal(value_el.text.replace(",", "."))
        nominal = int(nominal_el.text) if nominal_el is not None and nominal_el.text else 1
        rate = value / Decimal(nominal)
        return rate, rate_date

    raise ValueError("CBR: в выгрузке нет валюты USD")


async def _fetch_usd_for_calendar_date(d: date) -> tuple[Decimal, str | None]:
    """Запрос курса за конкретный календарный день (date_req=DD/MM/YYYY)."""
    params = {"date_req": d.strftime("%d/%m/%Y")}
    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
        r = await client.get(CBR_DAILY_XML, params=params)
        r.raise_for_status()
        if not r.content or len(r.content) < 50:
            raise ValueError("CBR: пустой ответ")
    text = _decode_xml_body(r.content)
    return _parse_usd_from_xml(text)


async def _fetch_usd_latest_no_date_param() -> tuple[Decimal, str | None]:
    """Запрос без date_req — у ЦБ это обычно последняя опубликованная ежедневная выгрузка."""
    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
        r = await client.get(CBR_DAILY_XML)
        r.raise_for_status()
        if not r.content or len(r.content) < 50:
            raise ValueError("CBR: пустой ответ")
    text = _decode_xml_body(r.content)
    return _parse_usd_from_xml(text)


async def get_usd_rub_rate_with_date() -> tuple[Decimal, str | None]:
    """
    Курс USD и дата сверки из XML ЦБ (атрибут Date у ValCurs, формат DD.MM.YYYY).
    """
    global _cache
    now = time.time()
    if _cache is not None and now - _cache[0] < _CACHE_TTL_SEC:
        _, rate, d = _cache
        logger.debug("CBR: кэш %s ₽/USD, дата %s", rate, d)
        return rate, d

    # 1) Последняя опубликованная выгрузка (без date_req).
    try:
        rate, rate_date = await _fetch_usd_latest_no_date_param()
        _cache = (now, rate, rate_date)
        logger.info(
            "CBR: курс USD = %s ₽/$ (дата в XML: %s; источник: последняя выгрузка)",
            rate,
            rate_date or "—",
        )
        return rate, rate_date
    except Exception as e:
        logger.debug("CBR: запрос без date_req не подошёл: %s", e)

    today = date.today()
    last_error: Exception | None = None

    for i in range(_MAX_LOOKBACK_DAYS):
        d = today - timedelta(days=i)
        try:
            rate, rate_date = await _fetch_usd_for_calendar_date(d)
            _cache = (now, rate, rate_date)
            logger.info(
                "CBR: курс USD = %s ₽/$ (дата в XML: %s; запрошен день %s)",
                rate,
                rate_date or "—",
                d.isoformat(),
            )
            return rate, rate_date
        except Exception as e:
            last_error = e
            logger.debug("CBR: нет данных на %s: %s", d.isoformat(), e)
            continue

    raise ValueError(
        f"CBR: не удалось получить курс USD за {_MAX_LOOKBACK_DAYS} дней. "
        f"Последняя ошибка: {last_error}"
    ) from last_error


async def get_usd_rub_rate() -> Decimal:
    """Только курс (руб./$); дата — в get_usd_rub_rate_with_date."""
    rate, _ = await get_usd_rub_rate_with_date()
    return rate
