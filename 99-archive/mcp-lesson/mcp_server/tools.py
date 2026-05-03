"""Логика инструментов MCP: товары и безопасный калькулятор."""

from __future__ import annotations

import ast
import json
import operator
from typing import Any

from db import get_connection

_ALLOWED_BINOPS: dict[type[ast.operator], Any] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
}


def _eval_ast(node: ast.AST) -> float:
    if isinstance(node, ast.Expression):
        return _eval_ast(node.body)
    if isinstance(node, ast.Constant):
        if isinstance(node.value, bool):
            raise ValueError("Логические значения не допускаются")
        if isinstance(node.value, (int, float)):
            return float(node.value)
        raise ValueError("Допускаются только числа")
    if isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type not in _ALLOWED_BINOPS:
            raise ValueError(f"Операция не разрешена: {op_type.__name__}")
        fn = _ALLOWED_BINOPS[op_type]
        return float(fn(_eval_ast(node.left), _eval_ast(node.right)))
    if isinstance(node, ast.UnaryOp):
        if isinstance(node.op, ast.USub):
            return float(-_eval_ast(node.operand))
        if isinstance(node.op, ast.UAdd):
            return float(+_eval_ast(node.operand))
        raise ValueError("Недопустимый унарный оператор")
    raise ValueError("Недопустимое выражение")


def safe_calculate(expression: str) -> float:
    """
    Вычисляет арифметическое выражение без eval(): только числа, +, -, *, /, ** и скобки.
    """
    expr = expression.strip()
    if not expr:
        raise ValueError("Пустое выражение")
    tree = ast.parse(expr, mode="eval")
    return _eval_ast(tree)


def row_to_dict(row: Any) -> dict[str, Any]:
    return {"id": row["id"], "name": row["name"], "category": row["category"], "price": row["price"]}


def list_products() -> str:
    with get_connection() as conn:
        cur = conn.execute(
            "SELECT id, name, category, price FROM products ORDER BY id"
        )
        items = [row_to_dict(r) for r in cur.fetchall()]
    return json.dumps(items, ensure_ascii=False, indent=2)


def find_product(name: str) -> str:
    needle = name.strip()
    if not needle:
        return json.dumps([], ensure_ascii=False)
    pattern = f"%{needle}%"
    with get_connection() as conn:
        cur = conn.execute(
            """
            SELECT id, name, category, price FROM products
            WHERE name LIKE ? COLLATE NOCASE
            ORDER BY id
            """,
            (pattern,),
        )
        items = [row_to_dict(r) for r in cur.fetchall()]
    return json.dumps(items, ensure_ascii=False, indent=2)


def add_product(name: str, category: str, price: float) -> str:
    n, c = name.strip(), category.strip()
    if not n or not c:
        raise ValueError("Имя и категория не могут быть пустыми")
    try:
        p = float(price)
    except (TypeError, ValueError) as e:
        raise ValueError("Некорректная цена") from e
    if p < 0:
        raise ValueError("Цена не может быть отрицательной")
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO products (name, category, price) VALUES (?, ?, ?)",
            (n, c, p),
        )
        new_id = cur.lastrowid
        conn.commit()
    return json.dumps(
        {"id": new_id, "name": n, "category": c, "price": p},
        ensure_ascii=False,
        indent=2,
    )


def calculate_tool(expression: str) -> str:
    result = safe_calculate(expression)
    return json.dumps(
        {"expression": expression.strip(), "result": result},
        ensure_ascii=False,
        indent=2,
    )
