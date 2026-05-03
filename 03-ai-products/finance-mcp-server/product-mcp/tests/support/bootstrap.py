"""
Isolate product-mcp for tests / scenario runner: DB path, data dirs, tool registration.

Uses direct assignment (no pytest) so scripts/run_scenarios.py can reuse the same logic.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import config
import db
import services.reporting_service as reporting_service


def configure_isolated_paths(base_dir: Path, db_filename: str = "test_mcp.db") -> Path:
    """
    Point config/db/reporting at base_dir (tmp). Creates data/imports and data/exports.
    Returns resolved DB path.
    """
    base_dir = base_dir.resolve()
    db_path = (base_dir / db_filename).resolve()
    data = base_dir / "data"
    imports_dir = data / "imports"
    exports_dir = data / "exports"
    data.mkdir(parents=True, exist_ok=True)
    imports_dir.mkdir(parents=True, exist_ok=True)
    exports_dir.mkdir(parents=True, exist_ok=True)

    config.DB_PATH = db_path
    db.DB_PATH = db_path
    config.DATA_DIR = data
    config.IMPORTS_DIR = imports_dir
    config.EXPORTS_DIR = exports_dir
    reporting_service.EXPORTS_DIR = exports_dir
    return db_path


def init_database_and_seed(db_path: Path | None = None) -> None:
    path = db_path or config.DB_PATH
    db.init_database(path)
    import seed

    seed.seed_if_empty()


def register_all_tools() -> None:
    from mcp.server.fastmcp import FastMCP
    from tools import register_all

    register_all(FastMCP("test-harness"))


def full_bootstrap(base_dir: Path, db_filename: str = "test_mcp.db") -> dict[str, Any]:
    """
    Configure paths, init DB + seed, register MCP tools.
    Returns dict with paths for scenarios.
    """
    db_path = configure_isolated_paths(base_dir, db_filename)
    init_database_and_seed(db_path)
    register_all_tools()
    import registry

    return {
        "base_dir": base_dir.resolve(),
        "db_path": db_path,
        "imports_dir": config.IMPORTS_DIR,
        "exports_dir": config.EXPORTS_DIR,
        "dispatch": lambda tool, payload=None: registry.dispatch(tool, payload or {}),
    }
