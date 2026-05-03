"""Safe calculator: tool + direct utils."""

from __future__ import annotations

import pytest

from utils.safe_calc import SafeCalcError, safe_calculate


@pytest.mark.parametrize(
    "expr,expected",
    [
        ("2 + 2", 4),
        ("10 / 2", 5.0),
        ("min(3, 2+5)", 3),
        ("max(10, 20, 5)", 20),
        ("abs(-4)", 4),
    ],
)
def test_safe_calculate_allowed(expr, expected, mcp_env):
    assert safe_calculate(expr) == expected
    raw = mcp_env.dispatch("calculate", {"expression": expr})
    assert raw["success"] is True
    assert raw["result"]["error"] is None
    assert raw["result"]["result"] == expected


@pytest.mark.parametrize(
    "expr",
    [
        '__import__("os")',
        "open(\"x\")",
        "lambda x: x",
        "[].__class__",
    ],
)
def test_safe_calculate_blocks_unsafe(expr, mcp_env):
    with pytest.raises(SafeCalcError):
        safe_calculate(expr)
    raw = mcp_env.dispatch("calculate", {"expression": expr})
    assert raw["success"] is True
    assert raw["result"]["error"] is not None
    assert raw["result"]["result"] is None


def test_calculate_invalid_syntax_returns_error(mcp_env):
    raw = mcp_env.dispatch("calculate", {"expression": "invalid!!!@@@"})
    assert raw["success"] is True
    assert raw["result"]["error"] is not None
