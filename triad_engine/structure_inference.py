#!/usr/bin/env python3
"""TRIAD-GEO: deterministic, auditable distance-geometry research prototype.

This is NOT AlphaFold and does NOT predict protein structures. It demonstrates
one narrow transferable idea: infer a geometric configuration from pairwise
relations, then iteratively reduce weighted geometric inconsistency.
Standard-library only; no network, model weights, or third-party packages.
"""
from __future__ import annotations
import math
from typing import Any, Iterable

_EPS = 1e-12
_MAX_NODES = 500
_MAX_EDGES = 20_000

class GeometryInputError(ValueError):
    """Raised when the graph or its distance constraints are invalid."""

def _finite_number(value: Any, name: str, *, positive: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise GeometryInputError(f"{name} must be a number")
    result = float(value)
    if not math.isfinite(result) or abs(result) > 1e9:
        raise GeometryInputError(f"{name} must be finite and within bounds")
    if positive and result <= 0:
        raise GeometryInputError(f"{name} must be greater than zero")
    return result

def triangle_inequality_audit(node_ids: list[str], constraints: Iterable[dict[str, Any]], tolerance: float = 1e-9) -> list[dict[str, Any]]:
    """Report violated triangle inequalities where all three edges are known."""
    pairs: dict[frozenset[str], float] = {}
    for edge in constraints:
        a, b = edge["a"], edge["b"]
        pairs[frozenset((a, b))] = float(edge["distance"])
    violations = []
    for i, a in enumerate(node_ids):
        for j in range(i + 1, len(node_ids)):
            b = node_ids[j]
            for c in node_ids[j + 1:]:
                ab = pairs.get(frozenset((a, b)))
                ac = pairs.get(frozenset((a, c)))
                bc = pairs.get(frozenset((b, c)))
                if ab is None or ac is None or bc is None:
                    continue
                sides = sorted((ab, ac, bc))
                if sides[0] + sides[1] + tolerance < sides[2]:
                    violations.append({"nodes": [a, b, c], "side_lengths": {"ab": ab, "ac": ac, "bc": bc}, "violation": sides[2] - sides[0] - sides[1]})
    return violations

def infer_geometry(node_ids: list[str], distance_constraints: list[dict[str, Any]], dimensions: int = 3, iterations: int = 4000, learning_rate: float = 0.01) -> dict[str, Any]:
    """Fit coordinates to weighted pairwise distances using gradient descent.

    Each constraint has: {"a": node_id, "b": node_id, "distance": positive_float, "weight": positive_float?}
    Coordinates are only defined up to translation, rotation and reflection.
    Sparse constraints may admit many different geometries.
    """
    if not isinstance(node_ids, list) or not 2 <= len(node_ids) <= _MAX_NODES:
        raise GeometryInputError(f"node_ids must contain 2..{_MAX_NODES} nodes")
    if any(not isinstance(x, str) or not x.strip() or len(x) > 100 for x in node_ids):
        raise GeometryInputError("each node ID must be a non-empty string up to 100 chars")
    if len(set(node_ids)) != len(node_ids):
        raise GeometryInputError("node IDs must be unique")
    if dimensions not in (2, 3):
        raise GeometryInputError("dimensions must be 2 or 3")
    if isinstance(iterations, bool) or not isinstance(iterations, int) or not 1 <= iterations <= 20_000:
        raise GeometryInputError("iterations must be an integer in 1..20000")
    lr = _finite_number(learning_rate, "learning_rate", positive=True)
    if lr > 0.1:
        raise GeometryInputError("learning_rate must not exceed 0.1")
    if not isinstance(distance_constraints, list) or not 1 <= len(distance_constraints) <= _MAX_EDGES:
        raise GeometryInputError(f"distance_constraints must contain 1..{_MAX_EDGES} edges")
    known = set(node_ids)
    edges = []
    seen = set()
    adjacency = {node: set() for node in node_ids}
    normalized = []
    for item in distance_constraints:
        if not isinstance(item, dict):
            raise GeometryInputError("each distance constraint must be an object")
        a, b = item.get("a"), item.get("b")
        if a not in known or b not in known:
            raise GeometryInputError("constraint references an unknown node")
        if a == b:
            raise GeometryInputError("self-distance constraints are not allowed")
        key = frozenset((a, b))
        if key in seen:
            raise GeometryInputError("duplicate undirected edge")
        seen.add(key)
        distance = _finite_number(item.get("distance"), "distance", positive=True)
        weight = _finite_number(item.get("weight", 1.0), "weight", positive=True)
        ia, ib = node_ids.index(a), node_ids.index(b)
        edges.append((ia, ib, distance, weight))
        adjacency[a].add(b)
        adjacency[b].add(a)
        normalized.append({"a": a, "b": b, "distance": distance, "weight": weight})
    visited, stack = set(), [node_ids[0]]
    while stack:
        node = stack.pop()
        if node in visited:
            continue
        visited.add(node)
        stack.extend(adjacency[node] - visited)
    if len(visited) != len(node_ids):
        raise GeometryInputError("distance-constraint graph must be connected")
    violations = triangle_inequality_audit(node_ids, normalized)
    if violations:
        return {"status": "inconsistent_constraints", "coordinates": None, "triangle_inequality_violations": violations, "message": "Known edge lengths violate a triangle inequality; no geometry was fitted."}
    n = len(node_ids)
    golden = math.pi * (3.0 - math.sqrt(5.0))
    coords = []
    for i in range(n):
        angle = i * golden
        radius = 1.0 + 0.07 * i
        point = [radius * math.cos(angle), radius * math.sin(angle)]
        if dimensions == 3:
            point.append(0.37 * math.sin(angle * 0.73) + 0.11 * i)
        coords.append(point)
    weight_sum = sum(edge[3] for edge in edges)
    initial_stress, stress = None, math.inf
    for step in range(iterations):
        gradients = [[0.0] * dimensions for _ in range(n)]
        stress_sum = 0.0
        for ia, ib, target, weight in edges:
            delta = [coords[ia][k] - coords[ib][k] for k in range(dimensions)]
            current = math.sqrt(sum(v * v for v in delta))
            if current < _EPS:
                delta[0], current = 1e-6, 1e-6
            error = current - target
            stress_sum += weight * error * error
            factor = 2.0 * weight * error / current
            for k in range(dimensions):
                component = factor * delta[k]
                gradients[ia][k] += component
                gradients[ib][k] -= component
        stress = stress_sum / weight_sum
        if initial_stress is None:
            initial_stress = stress
        rate = lr / (1.0 + step / 600.0)
        for i in range(n):
            for k in range(dimensions):
                coords[i][k] -= rate * gradients[i][k] / weight_sum
        means = [sum(coords[i][k] for i in range(n)) / n for k in range(dimensions)]
        for i in range(n):
            for k in range(dimensions):
                coords[i][k] -= means[k]
    residuals, final_sum = [], 0.0
    for ia, ib, target, weight in edges:
        actual = math.dist(coords[ia], coords[ib])
        error = actual - target
        final_sum += weight * error * error
        residuals.append({"a": node_ids[ia], "b": node_ids[ib], "target_distance": target, "fitted_distance": actual, "residual": error, "weight": weight})
    return {
        "status": "fitted",
        "algorithm": "weighted_pairwise_distance_gradient_descent",
        "dimensions": dimensions,
        "iterations": iterations,
        "coordinates": {node_ids[i]: [round(v, 9) for v in coords[i]] for i in range(n)},
        "weighted_mean_squared_distance_error": final_sum / weight_sum,
        "initial_weighted_mean_squared_distance_error": initial_stress,
        "edge_residuals": residuals,
        "triangle_inequality_violations": [],
        "identifiability": "Coordinates are defined only up to rigid transformations; sparse constraints may be underdetermined. A low residual is not proof of a unique or true structure.",
        "scientific_boundary": "Educational distance-geometry solver only. It has no protein sequence model, MSA, learned parameters, Evoformer, templates, physical energy model, or experimental validation; it is not AlphaFold and cannot predict protein folds."
    }
