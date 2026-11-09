#!/usr/bin/env python3
"""Independent distance-geometry baselines: classical MDS and SMACOF.

Pure Python, standard library only. This is a research/benchmark module,
not a protein folding model.
"""
from __future__ import annotations
import math
from typing import Any
from structure_inference import GeometryInputError, _finite_number


def _validate(nodes: list[str], constraints: list[dict[str, Any]], dimensions: int):
    if not isinstance(nodes, list) or not 2 <= len(nodes) <= 150:
        raise GeometryInputError("nodes must contain 2..150 IDs")
    if any(not isinstance(x, str) or not x.strip() for x in nodes) or len(set(nodes)) != len(nodes):
        raise GeometryInputError("node IDs must be unique non-empty strings")
    if dimensions not in (2, 3):
        raise GeometryInputError("dimensions must be 2 or 3")
    index = {name: i for i, name in enumerate(nodes)}
    edges, seen = [], set()
    for item in constraints:
        a, b = item.get("a"), item.get("b")
        if a not in index or b not in index or a == b:
            raise GeometryInputError("invalid edge endpoints")
        key = frozenset((a, b))
        if key in seen:
            raise GeometryInputError("duplicate undirected edge")
        seen.add(key)
        d = _finite_number(item.get("distance"), "distance", positive=True)
        w = _finite_number(item.get("weight", 1.0), "weight", positive=True)
        edges.append((index[a], index[b], d, w))
    if not edges:
        raise GeometryInputError("at least one edge is required")
    adjacency = [set() for _ in nodes]
    for i, j, _, _ in edges:
        adjacency[i].add(j); adjacency[j].add(i)
    reached, stack = set(), [0]
    while stack:
        i = stack.pop()
        if i in reached: continue
        reached.add(i); stack.extend(adjacency[i] - reached)
    if len(reached) != len(nodes):
        raise GeometryInputError("constraint graph must be connected")
    return edges


def _initial(n: int, dimensions: int):
    golden = math.pi * (3.0 - math.sqrt(5.0))
    result = []
    for i in range(n):
        angle = i * golden
        radius = 1.0 + 0.07 * i
        p = [radius * math.cos(angle), radius * math.sin(angle)]
        if dimensions == 3:
            p.append(0.37 * math.sin(angle * 0.73) + 0.11 * i)
        result.append(p)
    _center(result)
    return result


def _center(x):
    n, d = len(x), len(x[0])
    means = [sum(p[k] for p in x) / n for k in range(d)]
    for p in x:
        for k in range(d): p[k] -= means[k]


def _stress(x, edges):
    total = sum(w for _, _, _, w in edges)
    value = sum(w * (math.dist(x[i], x[j]) - d) ** 2 for i, j, d, w in edges)
    return value / total


def _solve_linear(a, b):
    """Gaussian elimination with partial pivoting; small dense systems only."""
    n = len(b)
    m = [list(a[i]) + [b[i]] for i in range(n)]
    for col in range(n):
        pivot = max(range(col, n), key=lambda r: abs(m[r][col]))
        if abs(m[pivot][col]) < 1e-12:
            raise GeometryInputError("singular graph Laplacian; check graph connectivity")
        m[col], m[pivot] = m[pivot], m[col]
        scale = m[col][col]
        for k in range(col, n + 1): m[col][k] /= scale
        for row in range(n):
            if row == col: continue
            factor = m[row][col]
            if factor:
                for k in range(col, n + 1): m[row][k] -= factor * m[col][k]
    return [m[i][n] for i in range(n)]


def smacof_fit(nodes: list[str], constraints: list[dict[str, Any]], dimensions: int = 3, iterations: int = 500):
    """Weighted SMACOF majorization for arbitrary connected sparse graphs."""
    edges = _validate(nodes, constraints, dimensions)
    if isinstance(iterations, bool) or not isinstance(iterations, int) or not 1 <= iterations <= 5000:
        raise GeometryInputError("iterations must be in 1..5000")
    n = len(nodes)
    # V is the weighted graph Laplacian. Anchor final node to remove translation.
    v = [[0.0] * n for _ in range(n)]
    for i, j, _, w in edges:
        v[i][i] += w; v[j][j] += w
        v[i][j] -= w; v[j][i] -= w
    reduced = [row[:n-1] for row in v[:n-1]]
    x = _initial(n, dimensions)
    history = [_stress(x, edges)]
    for _ in range(iterations):
        bmat = [[0.0] * n for _ in range(n)]
        for i, j, target, weight in edges:
            actual = math.dist(x[i], x[j])
            if actual < 1e-12: actual = 1e-12
            value = -weight * target / actual
            bmat[i][j] += value; bmat[j][i] += value
            bmat[i][i] -= value; bmat[j][j] -= value
        new = [[0.0] * dimensions for _ in range(n)]
        for k in range(dimensions):
            rhs = [sum(bmat[i][j] * x[j][k] for j in range(n)) for i in range(n-1)]
            solved = _solve_linear(reduced, rhs)
            for i in range(n-1): new[i][k] = solved[i]
            new[n-1][k] = 0.0
        _center(new)
        value = _stress(new, edges)
        # Numerical roundoff can cause tiny increases; reject material increases.
        if value > history[-1] + 1e-9:
            break
        x = new
        history.append(value)
        if abs(history[-2] - history[-1]) < 1e-12:
            break
    residuals = []
    for i, j, target, weight in edges:
        fitted = math.dist(x[i], x[j])
        residuals.append({"a": nodes[i], "b": nodes[j], "target_distance": target,
                          "fitted_distance": fitted, "residual": fitted-target, "weight": weight})
    return {"status": "fitted", "algorithm": "weighted_smacof", "dimensions": dimensions,
            "iterations_completed": len(history)-1,
            "coordinates": {nodes[i]: [round(v, 9) for v in x[i]] for i in range(n)},
            "weighted_mean_squared_distance_error": history[-1],
            "stress_history": history, "edge_residuals": residuals,
            "limitations": "Sparse distance geometry may be non-unique; stress is fit error, not predictive confidence."}


def _jacobi_eigen_symmetric(matrix, max_sweeps=100):
    """Jacobi eigensolver for a real symmetric matrix; returns values/vectors."""
    n = len(matrix)
    a = [row[:] for row in matrix]
    v = [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]
    for _ in range(max_sweeps * n * n):
        p, q, largest = 0, 1, 0.0
        for i in range(n):
            for j in range(i+1, n):
                if abs(a[i][j]) > largest:
                    p, q, largest = i, j, abs(a[i][j])
        if largest < 1e-12: break
        tau = (a[q][q] - a[p][p]) / (2.0 * a[p][q])
        t = (1.0 if tau >= 0 else -1.0) / (abs(tau) + math.sqrt(1.0 + tau*tau))
        c = 1.0 / math.sqrt(1.0 + t*t); s = t*c
        app, aqq, apq = a[p][p], a[q][q], a[p][q]
        a[p][p] = app - t*apq; a[q][q] = aqq + t*apq
        a[p][q] = a[q][p] = 0.0
        for k in range(n):
            if k not in (p, q):
                akp, akq = a[k][p], a[k][q]
                a[k][p] = a[p][k] = c*akp - s*akq
                a[k][q] = a[q][k] = s*akp + c*akq
            vkp, vkq = v[k][p], v[k][q]
            v[k][p] = c*vkp - s*vkq
            v[k][q] = s*vkp + c*vkq
    order = sorted(range(n), key=lambda i: a[i][i], reverse=True)
    return [a[i][i] for i in order], [[v[row][i] for i in order] for row in range(n)]


def classical_mds(nodes: list[str], distance_matrix: list[list[float]], dimensions: int = 3):
    """Classical metric MDS for a complete, symmetric distance matrix."""
    n = len(nodes)
    if not 2 <= n <= 150 or len(set(nodes)) != n:
        raise GeometryInputError("nodes must be 2..150 unique IDs")
    if dimensions not in (2, 3):
        raise GeometryInputError("dimensions must be 2 or 3")
    if len(distance_matrix) != n or any(len(row) != n for row in distance_matrix):
        raise GeometryInputError("distance matrix must be square and match nodes")
    d2 = [[0.0]*n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            d = _finite_number(distance_matrix[i][j], "distance")
            if d < 0 or (i == j and abs(d) > 1e-9):
                raise GeometryInputError("distances must be nonnegative with zero diagonal")
            if abs(d - float(distance_matrix[j][i])) > 1e-8:
                raise GeometryInputError("distance matrix must be symmetric")
            d2[i][j] = d*d
    row_mean = [sum(row)/n for row in d2]
    grand = sum(row_mean)/n
    gram = [[-0.5*(d2[i][j]-row_mean[i]-row_mean[j]+grand) for j in range(n)] for i in range(n)]
    eigenvalues, eigenvectors = _jacobi_eigen_symmetric(gram)
    coords = [[0.0]*dimensions for _ in range(n)]
    for k in range(dimensions):
        eig = max(0.0, eigenvalues[k])
        for i in range(n): coords[i][k] = eigenvectors[i][k]*math.sqrt(eig)
    _center(coords)
    return {"status": "fitted", "algorithm": "classical_mds",
            "coordinates": {nodes[i]: [round(v, 9) for v in coords[i]] for i in range(n)},
            "eigenvalues": eigenvalues, "negative_eigenvalue_mass": sum(-v for v in eigenvalues if v < 0),
            "limitations": "Requires a complete distance matrix; negative eigenvalues indicate non-Euclidean distances/noise. Coordinates are defined up to rigid transformations."}
