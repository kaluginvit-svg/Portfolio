"""Pytest fixtures: isolated DB, dirs, registered tools."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

import config
import db
import services.reporting_service as reporting_service


@pytest.fixture
def fixtures_dir() -> Path:
    return Path(__file__).resolve().parent / "fixtures"


@pytest.fixture
def mcp_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Any:
    """
    Fresh SQLite DB under tmp_path, seeded data, all tools registered.
    Patches config/db/reporting_service export dir for isolation.
    """
    base = tmp_path
    db_path = base / "pytest_mcp.db"
    data = base / "data"
    imp = data / "imports"
    exp = data / "exports"
    data.mkdir(parents=True, exist_ok=True)
    imp.mkdir(parents=True, exist_ok=True)
    exp.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(config, "DB_PATH", db_path)
    monkeypatch.setattr(db, "DB_PATH", db_path)
    monkeypatch.setattr(config, "DATA_DIR", data)
    monkeypatch.setattr(config, "IMPORTS_DIR", imp)
    monkeypatch.setattr(config, "EXPORTS_DIR", exp)
    monkeypatch.setattr(reporting_service, "EXPORTS_DIR", exp)

    db.init_database(db_path)
    import seed

    seed.seed_if_empty()

    from mcp.server.fastmcp import FastMCP
    from tools import register_all

    register_all(FastMCP("pytest"))

    import registry

    class Env:
        @staticmethod
        def dispatch(tool: str, payload: dict[str, Any] | None = None) -> Any:
            return registry.dispatch(tool, payload or {})

    env = Env()
    env.tmp_path = base
    env.db_path = db_path
    env.imports_dir = imp
    env.exports_dir = exp
    return env
