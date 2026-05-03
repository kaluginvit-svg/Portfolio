"""Safe arithmetic via AST — no eval()."""

from __future__ import annotations

import ast
import math
import operator
from typing import Any


_ALLOWED_BINOPS: dict[type[ast.operator], Any] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.FloorDiv: operator.floordiv,
}

_ALLOWED_UNARY: dict[type[ast.unaryop], Any] = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}

_ALLOWED_FUNCS = {
    "min": min,
    "max": max,
    "round": round,
    "abs": abs,
}


class SafeCalcError(ValueError):
    pass


def _eval_node(node: ast.AST) -> float | int:
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
            return node.value
        raise SafeCalcError("Only numeric constants are allowed")

    if isinstance(node, ast.BinOp):
        op = _ALLOWED_BINOPS.get(type(node.op))
        if op is None:
            raise SafeCalcError("Operator not allowed")
        left = _eval_node(node.left)
        right = _eval_node(node.right)
        if op is operator.truediv and right == 0:
            raise SafeCalcError("Division by zero")
        if op is operator.mod and right == 0:
            raise SafeCalcError("Modulo by zero")
        return op(left, right)

    if isinstance(node, ast.UnaryOp):
        op = _ALLOWED_UNARY.get(type(node.op))
        if op is None:
            raise SafeCalcError("Unary operator not allowed")
        return op(_eval_node(node.operand))

    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name):
            raise SafeCalcError("Only simple function calls are allowed")
        name = node.func.id
        if name not in _ALLOWED_FUNCS:
            raise SafeCalcError(f"Function '{name}' is not allowed")
        if node.keywords:
            raise SafeCalcError("Keyword arguments are not allowed")
        args = [_eval_node(a) for a in node.args]
        fn = _ALLOWED_FUNCS[name]
        return fn(*args)

    raise SafeCalcError("Expression contains disallowed syntax")


def safe_calculate(expression: str) -> float | int:
    expr = expression.strip()
    if not expr:
        raise SafeCalcError("Empty expression")

    try:
        tree = ast.parse(expr, mode="eval")
    except SyntaxError as e:
        raise SafeCalcError(f"Syntax error: {e}") from e

    if not isinstance(tree, ast.Expression):
        raise SafeCalcError("Invalid expression")

    result = _eval_node(tree.body)
    if isinstance(result, float):
        if math.isinf(result) or math.isnan(result):
            raise SafeCalcError("Result is not finite")
    return result
