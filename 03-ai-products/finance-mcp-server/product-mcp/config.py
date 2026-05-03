"""Application configuration from environment and paths."""

from __future__ import annotations

import logging
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"
IMPORTS_DIR = DATA_DIR / "imports"
EXPORTS_DIR = DATA_DIR / "exports"

DB_PATH = Path(os.getenv("PRODUCT_MCP_DB_PATH", str(DATA_DIR / "product_mcp.db"))).resolve()

LOG_LEVEL = os.getenv("PRODUCT_MCP_LOG_LEVEL", "INFO").upper()

VALID_FINANCIAL_STATEMENT_TYPES = frozenset(
    {"pnl", "cashflow", "balance", "ap", "ar", "payments", "kpi"}
)
VALID_IMPORT_STATEMENT_TYPES = VALID_FINANCIAL_STATEMENT_TYPES | {"budget"}


def setup_logging() -> None:
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL, logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )


def ensure_data_directories() -> None:
    IMPORTS_DIR.mkdir(parents=True, exist_ok=True)
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
