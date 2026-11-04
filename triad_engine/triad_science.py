#!/usr/bin/env python3
"""Auditable dimensional analysis for TRIAD. Consistency is necessary, not sufficient, for a valid equation."""
from __future__ import annotations
import ast
import math
import re
from typing import Any

_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

class DimensionError(ValueError):
    pass

def _clean_dim(raw: Any) -> dict[str, float]:
    if not isinstance(raw, dict):
        raise DimensionError("each symbol dimension must be an object such as {'M':1,'L':1,'T':-2}")
    out = {}
    for key, value in raw.items():
        if not isinstance(key, str) or not _NAME.fullmatch(key):
            raise DimensionError("dimension base names must be identifiers")
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
            raise DimensionError("dimension exponents must be finite numbers")
        if abs(float(value)) > 100:
            raise DimensionError("dimension exponent out of bounds")
        if abs(float(value)) > 1e-12:
            out[key] = float(value)
    return out

def _combine(a: dict[str, float], b: dict[str, float], sign: float = 1.0) -> dict[str, float]:
    result = dict(a)
    for key, value in b.items():
        result[key] = result.get(key, 0.0) + sign * value
        if abs(result[key]) < 1e-12:
            result.pop(key)
    return result

def _scale(a: dict[str, float], factor: float) -> dict[str, float]:
    return {k: v * factor for k, v in a.items() if abs(v * factor) >= 1e-12}

def dimension_of(expression: str, symbols: dict[str, Any]) -> dict[str, float]:
    if not isinstance(expression, str) or not expression.strip() or len(expression) > 240:
        raise DimensionError("expression must be a non-empty string up to 240 characters")
    expr = expression.strip().replace("×", "*").replace("·", "*").replace("÷", "/").replace("^", "**").replace("−", "-")
    try:
        tree = ast.parse(expr, mode="eval")
    except SyntaxError as exc:
        raise DimensionError("invalid expression syntax") from exc
    if len(list(ast.walk(tree))) > 100:
        raise DimensionError("expression is too complex")
    clean_symbols = {}
    for name, dim in symbols.items():
        if not isinstance(name, str) or not _NAME.fullmatch(name):
            raise DimensionError("symbol names must be identifiers")
        clean_symbols[name] = _clean_dim(dim)

    def visit(node):
        if isinstance(node, ast.Expression):
            return visit(node.body)
        if isinstance(node, ast.Name):
            if node.id not in clean_symbols:
                raise DimensionError(f"unknown symbol: {node.id}")
            return dict(clean_symbols[node.id])
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
            if not math.isfinite(float(node.value)):
                raise DimensionError("non-finite constant")
            return {}
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            return visit(node.operand)
        if isinstance(node, ast.BinOp):
            left = visit(node.left)
            if isinstance(node.op, ast.Add) or isinstance(node.op, ast.Sub):
                right = visit(node.right)
                if left != right:
                    raise DimensionError("addition/subtraction requires matching dimensions")
                return left
            if isinstance(node.op, ast.Mult):
                return _combine(left, visit(node.right), 1.0)
            if isinstance(node.op, ast.Div):
                return _combine(left, visit(node.right), -1.0)
            if isinstance(node.op, ast.Pow):
                if not isinstance(node.right, ast.Constant) or isinstance(node.right.value, bool) or not isinstance(node.right.value, (int, float)):
                    raise DimensionError("power must be a numeric constant")
                power = float(node.right.value)
                if not math.isfinite(power) or abs(power) > 20:
                    raise DimensionError("power out of bounds")
                return _scale(left, power)
        raise DimensionError("unsupported expression element")
    return visit(tree)

def compare_dimensions(lhs: str, rhs: str, symbols: dict[str, Any]) -> dict[str, Any]:
    left = dimension_of(lhs, symbols)
    right = dimension_of(rhs, symbols)
    keys = sorted(set(left) | set(right))
    consistent = all(abs(left.get(k, 0.0) - right.get(k, 0.0)) < 1e-9 for k in keys)
    return {
        "lhs": lhs, "rhs": rhs,
        "lhs_dimensions": {k: left[k] for k in sorted(left)},
        "rhs_dimensions": {k: right[k] for k in sorted(right)},
        "dimensionally_consistent": consistent,
        "difference_lhs_minus_rhs": {k: left.get(k, 0.0) - right.get(k, 0.0) for k in keys if abs(left.get(k, 0.0) - right.get(k, 0.0)) >= 1e-9},
        "limitation": "dimensional consistency is necessary but not sufficient to prove an equation physically correct"
    }
