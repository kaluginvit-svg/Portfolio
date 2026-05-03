#!/usr/bin/env python3
"""product-mcp: stdio MCP server for financial data tools."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import DB_PATH, ensure_data_directories, setup_logging
from db import init_database
from seed import seed_if_empty

setup_logging()
logger = logging.getLogger("product-mcp")

ensure_data_directories()
init_database(DB_PATH)
seed_if_empty()

from mcp.server.fastmcp import FastMCP

from tools import register_all

mcp = FastMCP("product-mcp")
register_all(mcp)

if __name__ == "__main__":
    logger.info("Starting product-mcp (stdio); database=%s", DB_PATH)
    mcp.run()
