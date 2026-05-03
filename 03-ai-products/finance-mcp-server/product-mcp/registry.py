"""Tool registry and JSON-schema introspection for orchestration layers."""

from __future__ import annotations

import json
from typing import Any, Callable

from schemas import tool_bundles

ToolHandler = Callable[..., Any]

_REGISTRY: dict[str, ToolHandler] = {}


def register_handler(name: str, fn: ToolHandler) -> None:
    _REGISTRY[name] = fn


def get_handler(name: str) -> ToolHandler | None:
    return _REGISTRY.get(name)


def list_tool_names() -> list[str]:
    return sorted(_REGISTRY.keys())


def tool_definitions() -> list[dict[str, Any]]:
    return [b.model_dump() for b in tool_bundles()]


def introspection_json() -> str:
    return json.dumps({"tools": tool_definitions()}, ensure_ascii=False, indent=2)


def dispatch(name: str, arguments: dict[str, Any] | None = None) -> Any:
    fn = get_handler(name)
    if fn is None:
        return {"success": False, "error": f"Unknown tool: {name}", "data": {}}
    args = arguments or {}
    try:
        return {"success": True, "result": fn(**args)}
    except TypeError as e:
        return {"success": False, "error": f"Invalid arguments for {name}: {e}", "data": {}}
    except Exception as e:
        return {"success": False, "error": str(e), "data": {}}
