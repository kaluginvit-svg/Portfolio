"""
Клиент MCP по Streamable HTTP: список инструментов и вызов tools/call.

Используется официальный SDK (`mcp` + `httpx`).
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamable_http_client
from mcp.types import CallToolResult, TextContent, Tool


def call_tool_result_to_text(result: CallToolResult) -> str:
    """Собирает текст из блоков ответа инструмента."""
    parts: list[str] = []
    for block in result.content:
        if isinstance(block, TextContent):
            parts.append(block.text)
    if parts:
        return "\n".join(parts)
    if result.structuredContent is not None:
        return json.dumps(result.structuredContent, ensure_ascii=False, indent=2)
    return ""


def mcp_tools_to_openai_functions(tools: list[Tool]) -> list[dict[str, Any]]:
    """Конвертация объявлений MCP в формат function-calling OpenAI Chat Completions."""
    out: list[dict[str, Any]] = []
    for t in tools:
        schema = dict(t.inputSchema) if t.inputSchema else {}
        if schema.get("type") != "object":
            schema = {
                "type": "object",
                "properties": schema.get("properties", {}),
                "required": schema.get("required", []),
            }
        desc = (t.description or "").strip() or f"MCP-инструмент {t.name}"
        out.append(
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": desc,
                    "parameters": schema,
                },
            }
        )
    return out


@asynccontextmanager
async def mcp_client_session(mcp_url: str) -> AsyncIterator[ClientSession]:
    """Одна инициализированная MCP-сессия на блок `async with` (несколько call_tool подряд)."""
    async with streamable_http_client(mcp_url) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            yield session


async def list_mcp_tools(mcp_url: str) -> tuple[list[Tool], list[dict[str, Any]]]:
    """Список инструментов с сервера и конвертация в OpenAI tools (отдельное подключение)."""
    async with mcp_client_session(mcp_url) as session:
        listed = await session.list_tools()
        oai = mcp_tools_to_openai_functions(listed.tools)
        return listed.tools, oai


async def call_mcp_tool(mcp_url: str, name: str, arguments: dict[str, Any] | None) -> str:
    """Один вызов инструмента в отдельной сессии (удобно для отладки)."""
    async with mcp_client_session(mcp_url) as session:
        result = await session.call_tool(name, arguments or {})
        if result.isError:
            return f"Ошибка инструмента {name}: {call_tool_result_to_text(result) or 'неизвестная ошибка'}"
        return call_tool_result_to_text(result)
