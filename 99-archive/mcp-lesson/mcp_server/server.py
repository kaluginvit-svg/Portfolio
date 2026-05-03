"""
MCP-сервер product-mcp: каталог товаров (SQLite) и безопасный калькулятор.

Запуск из каталога mcp_server:

  python server.py
      → транспорт stdio (Cursor, Claude Desktop, mcp inspector через stdio)

  python server.py --http
      → Streamable HTTP (для Telegram-бота). URL по умолчанию: http://127.0.0.1:8765/mcp
      Переменные окружения: MCP_HOST, MCP_PORT
"""

from __future__ import annotations

import argparse
import os

from mcp_factory import create_mcp_app


def main() -> None:
    parser = argparse.ArgumentParser(description="product-mcp")
    parser.add_argument(
        "--http",
        action="store_true",
        help="Запуск через Streamable HTTP (uvicorn), а не stdio",
    )
    args = parser.parse_args()

    host = os.environ.get("MCP_HOST", "127.0.0.1")
    port = int(os.environ.get("MCP_PORT", "8765"))

    mcp = create_mcp_app(streamable_http=args.http, host=host, port=port)

    if args.http:
        mcp.run(transport="streamable-http")
    else:
        mcp.run()


if __name__ == "__main__":
    main()
