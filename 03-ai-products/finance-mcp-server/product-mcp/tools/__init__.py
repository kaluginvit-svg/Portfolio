"""Register all MCP tools and Python dispatch handlers."""

from __future__ import annotations

from typing import Any

import registry as registry_mod
from tools import (
    contract_tools,
    finance_tools,
    health_tools,
    import_tools,
    investment_tools,
    report_tools,
    utility_tools,
)


def register_all(mcp: Any) -> None:
    reg = registry_mod
    health_tools.register(mcp, reg)
    import_tools.register(mcp, reg)
    finance_tools.register(mcp, reg)
    report_tools.register(mcp, reg)
    contract_tools.register(mcp, reg)
    investment_tools.register(mcp, reg)
    utility_tools.register(mcp, reg)
