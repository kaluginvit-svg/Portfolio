#!/usr/bin/env python3
"""
PyTrends MCP Server
MCP сервер для работы с Google Trends через библиотеку PyTrends
"""

import asyncio
import json
import sys
from typing import Any, Optional
from datetime import datetime, timedelta

try:
    from mcp.server.fastmcp import FastMCP
    from mcp.types import Tool, TextContent
except ImportError:
    print("Error: mcp library not installed. Run: pip install mcp", file=sys.stderr)
    sys.exit(1)

try:
    from pytrends.request import TrendReq
except ImportError:
    print("Error: pytrends library not installed. Run: pip install pytrends", file=sys.stderr)
    sys.exit(1)

# Инициализация MCP сервера
mcp = FastMCP("PyTrends MCP Server")

# Кэш экземпляров PyTrends по ключу (hl, tz)
_pytrends_instances: dict = {}


def get_pytrends(hl: str = 'en-US', tz: int = 360) -> TrendReq:
    """Получить или создать экземпляр PyTrends с User-Agent"""
    cache_key = (hl, tz)
    
    if cache_key not in _pytrends_instances:
        # Настройки User-Agent для избежания блокировок Google
        requests_args = {
            "headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                              "AppleWebKit/537.36 (KHTML, like Gecko) "
                              "Chrome/123.0.0.0 Safari/537.36"
            }
        }
        
        _pytrends_instances[cache_key] = TrendReq(
            hl=hl,
            tz=tz,
            retries=3,
            backoff_factor=0.5,
            requests_args=requests_args,
        )
    
    return _pytrends_instances[cache_key]


@mcp.tool()
def interest_over_time(
    keywords: str,
    timeframe: str = 'today 5-y',
    geo: str = '',
    hl: str = 'en-US',
    tz: int = 360
) -> str:
    """
    Получить данные о популярности ключевых слов за период времени.
    
    Args:
        keywords: Ключевые слова через запятую (например: "python, javascript")
        timeframe: Период времени (например: 'today 5-y', 'today 12-m', 'today 3-m', 'today 1-m', 'now 7-d', 'now 1-d')
        geo: Географический регион (пустая строка = весь мир, 'US' = США, 'RU' = Россия)
        hl: Язык интерфейса (например: 'en-US', 'ru-RU')
        tz: Часовой пояс в минутах от UTC (360 = UTC-6)
    
    Returns:
        JSON строка с данными о популярности по времени
    """
    try:
        pytrends = get_pytrends(hl=hl, tz=tz)
        kw_list = [kw.strip() for kw in keywords.split(',')]
        
        pytrends.build_payload(kw_list=kw_list, timeframe=timeframe, geo=geo)
        df = pytrends.interest_over_time()
        
        if df.empty:
            return json.dumps({"error": "No data available", "keywords": kw_list})
        
        # Конвертируем DataFrame в словарь
        result = {
            "keywords": kw_list,
            "timeframe": timeframe,
            "geo": geo if geo else "worldwide",
            "data": df.to_dict(orient='index')
        }
        
        return json.dumps(result, default=str, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "type": type(e).__name__})


@mcp.tool()
def interest_by_region(
    keywords: str,
    resolution: str = 'COUNTRY',
    timeframe: str = 'today 5-y',
    geo: str = '',
    hl: str = 'en-US',
    tz: int = 360
) -> str:
    """
    Получить данные о популярности по регионам.
    
    Args:
        keywords: Ключевые слова через запятую
        resolution: Разрешение ('COUNTRY', 'REGION', 'CITY', 'DMA', 'METRO')
        timeframe: Период времени
        geo: Географический регион
        hl: Язык интерфейса
        tz: Часовой пояс в минутах
    
    Returns:
        JSON строка с данными о популярности по регионам
    """
    try:
        pytrends = get_pytrends(hl=hl, tz=tz)
        kw_list = [kw.strip() for kw in keywords.split(',')]
        
        pytrends.build_payload(kw_list=kw_list, timeframe=timeframe, geo=geo)
        df = pytrends.interest_by_region(resolution=resolution, inc_low_vol=True, inc_geo_code=False)
        
        if df.empty:
            return json.dumps({"error": "No data available", "keywords": kw_list})
        
        result = {
            "keywords": kw_list,
            "resolution": resolution,
            "timeframe": timeframe,
            "geo": geo if geo else "worldwide",
            "data": df.to_dict(orient='index')
        }
        
        return json.dumps(result, default=str, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "type": type(e).__name__})


@mcp.tool()
def related_topics(
    keywords: str,
    timeframe: str = 'today 5-y',
    geo: str = '',
    hl: str = 'en-US',
    tz: int = 360
) -> str:
    """
    Получить связанные темы для ключевых слов.
    
    Args:
        keywords: Ключевое слово (одно)
        timeframe: Период времени
        geo: Географический регион
        hl: Язык интерфейса
        tz: Часовой пояс в минутах
    
    Returns:
        JSON строка со связанными темами
    """
    try:
        pytrends = get_pytrends(hl=hl, tz=tz)
        keyword = keywords.split(',')[0].strip()
        
        pytrends.build_payload(kw_list=[keyword], timeframe=timeframe, geo=geo)
        df = pytrends.related_topics()
        
        result = {
            "keyword": keyword,
            "timeframe": timeframe,
            "geo": geo if geo else "worldwide",
            "related_topics": {}
        }
        
        if df and not df.empty:
            for kw in df:
                if df[kw] is not None and 'rising' in df[kw]:
                    result["related_topics"][kw] = {
                        "rising": df[kw]['rising'].to_dict(orient='records') if not df[kw]['rising'].empty else [],
                        "top": df[kw]['top'].to_dict(orient='records') if not df[kw]['top'].empty else []
                    }
        
        return json.dumps(result, default=str, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "type": type(e).__name__})


@mcp.tool()
def related_queries(
    keywords: str,
    timeframe: str = 'today 5-y',
    geo: str = '',
    hl: str = 'en-US',
    tz: int = 360
) -> str:
    """
    Получить связанные запросы для ключевых слов.
    
    Args:
        keywords: Ключевое слово (одно)
        timeframe: Период времени
        geo: Географический регион
        hl: Язык интерфейса
        tz: Часовой пояс в минутах
    
    Returns:
        JSON строка со связанными запросами
    """
    try:
        pytrends = get_pytrends(hl=hl, tz=tz)
        keyword = keywords.split(',')[0].strip()
        
        pytrends.build_payload(kw_list=[keyword], timeframe=timeframe, geo=geo)
        df = pytrends.related_queries()
        
        result = {
            "keyword": keyword,
            "timeframe": timeframe,
            "geo": geo if geo else "worldwide",
            "related_queries": {}
        }
        
        if df and not df.empty:
            for kw in df:
                if df[kw] is not None and 'rising' in df[kw]:
                    result["related_queries"][kw] = {
                        "rising": df[kw]['rising'].to_dict(orient='records') if not df[kw]['rising'].empty else [],
                        "top": df[kw]['top'].to_dict(orient='records') if not df[kw]['top'].empty else []
                    }
        
        return json.dumps(result, default=str, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "type": type(e).__name__})


@mcp.tool()
def trending_searches(
    pn: str = 'united_states',
    hl: str = 'en-US'
) -> str:
    """
    Получить текущие трендовые поисковые запросы.
    
    Args:
        pn: Название страны/региона (например: 'united_states', 'russia')
        hl: Язык интерфейса
    
    Returns:
        JSON строка с трендовыми запросами
    """
    try:
        pytrends = get_pytrends(hl=hl, tz=360)
        df = pytrends.trending_searches(pn=pn)
        
        if df.empty:
            return json.dumps({"error": "No trending data available", "pn": pn})
        
        result = {
            "region": pn,
            "trending_searches": df[0].tolist() if len(df.columns) > 0 else []
        }
        
        return json.dumps(result, default=str, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "type": type(e).__name__})


@mcp.tool()
def top_charts(
    date: str = '',
    hl: str = 'en-US',
    tz: int = 360,
    geo: str = 'US'
) -> str:
    """
    Получить топ чарты Google Trends.
    
    Args:
        date: Дата в формате YYYYMM (например: '202401' для января 2024). Пустая строка = текущий год
        hl: Язык интерфейса
        tz: Часовой пояс в минутах
        geo: Географический регион (код страны)
    
    Returns:
        JSON строка с топ чартами
    """
    try:
        pytrends = get_pytrends(hl=hl, tz=tz)
        
        if not date:
            # Используем текущий год и месяц
            now = datetime.now()
            date = now.strftime('%Y%m')
        
        df = pytrends.top_charts(date=date, hl=hl, tz=tz, geo=geo)
        
        if df.empty:
            return json.dumps({"error": "No chart data available", "date": date, "geo": geo})
        
        result = {
            "date": date,
            "geo": geo,
            "charts": df.to_dict(orient='records')
        }
        
        return json.dumps(result, default=str, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "type": type(e).__name__})


@mcp.tool()
def suggestions(
    keyword: str,
    hl: str = 'en-US'
) -> str:
    """
    Получить предложения ключевых слов (автодополнение).
    
    Args:
        keyword: Ключевое слово для поиска предложений
        hl: Язык интерфейса
    
    Returns:
        JSON строка с предложениями
    """
    try:
        pytrends = get_pytrends(hl=hl, tz=360)
        suggestions = pytrends.suggestions(keyword)
        
        result = {
            "keyword": keyword,
            "suggestions": suggestions if suggestions else []
        }
        
        return json.dumps(result, default=str, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "type": type(e).__name__})


if __name__ == "__main__":
    # Запуск MCP сервера через stdio (стандартный способ для MCP)
    mcp.run()
