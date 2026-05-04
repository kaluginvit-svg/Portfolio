"""
Единая сборка FastMCP (product-mcp): инструменты + настройки для stdio или Streamable HTTP.
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

import db
from tools import add_product as add_product_impl
from tools import calculate_tool
from tools import find_product as find_product_impl
from tools import list_products as list_products_impl

db.init_database()


def create_mcp_app(*, streamable_http: bool, host: str = "127.0.0.1", port: int = 8765) -> FastMCP:
    """
    streamable_http=True — json_response + stateless_http (рекомендация SDK для HTTP).
    """
    kwargs: dict = {
        "name": "product-mcp",
        "host": host,
        "port": port,
    }
    if streamable_http:
        kwargs["json_response"] = True
        kwargs["stateless_http"] = True

    mcp = FastMCP(**kwargs)

    @mcp.tool()
    def list_products() -> str:
        """Возвращает полный список товаров из каталога (JSON-массив с id, name, category, price)."""
        return list_products_impl()

    @mcp.tool()
    def find_product(name: str) -> str:
        """Ищет товары по подстроке в названии (без учёта регистра). Возвращает JSON-массив совпадений."""
        return find_product_impl(name)

    @mcp.tool()
    def add_product(name: str, category: str, price: float) -> str:
        """Добавляет новый товар. Возвращает JSON с созданной записью."""
        return add_product_impl(name, category, price)

    @mcp.tool()
    def calculate(expression: str) -> str:
        """
        Безопасный калькулятор: только числа и операции +, -, *, /, ** и скобки.
        eval() не используется. Возвращает JSON с полями expression и result.
        """
        return calculate_tool(expression)

    return mcp
