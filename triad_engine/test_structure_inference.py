#!/usr/bin/env python3
"""Regression tests for the standard-library TRIAD-GEO prototype."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from structure_inference import GeometryInputError, infer_geometry, triangle_inequality_audit

class GeometryTests(unittest.TestCase):
    def test_three_four_five_triangle_fits(self):
        result = infer_geometry(["A", "B", "C"], [
            {"a": "A", "b": "B", "distance": 3},
            {"a": "B", "b": "C", "distance": 4},
            {"a": "A", "b": "C", "distance": 5},
        ], dimensions=2, iterations=5000)
        self.assertEqual(result["status"], "fitted")
        self.assertLess(result["weighted_mean_squared_distance_error"], 1e-8)
        self.assertEqual(result["triangle_inequality_violations"], [])

    def test_impossible_triangle_is_rejected(self):
        constraints = [{"a": "A", "b": "B", "distance": 1}, {"a": "B", "b": "C", "distance": 1}, {"a": "A", "b": "C", "distance": 3}]
        audit = triangle_inequality_audit(["A", "B", "C"], constraints)
        self.assertEqual(len(audit), 1)
        result = infer_geometry(["A", "B", "C"], constraints)
        self.assertEqual(result["status"], "inconsistent_constraints")
        self.assertIsNone(result["coordinates"])

    def test_disconnected_graph_rejected(self):
        with self.assertRaises(GeometryInputError):
            infer_geometry(["A", "B", "C"], [{"a": "A", "b": "B", "distance": 1}])

    def test_duplicate_edges_rejected(self):
        with self.assertRaises(GeometryInputError):
            infer_geometry(["A", "B"], [{"a": "A", "b": "B", "distance": 1}, {"a": "B", "b": "A", "distance": 1}])

    def test_invalid_numeric_input_rejected(self):
        with self.assertRaises(GeometryInputError):
            infer_geometry(["A", "B"], [{"a": "A", "b": "B", "distance": float("nan")}])

    def test_weighted_fit_returns_residuals(self):
        result = infer_geometry(["A", "B", "C"], [
            {"a": "A", "b": "B", "distance": 2, "weight": 10},
            {"a": "B", "b": "C", "distance": 2, "weight": 1},
            {"a": "A", "b": "C", "distance": 3, "weight": 1},
        ], dimensions=2, iterations=3000)
        self.assertEqual(result["status"], "fitted")
        self.assertEqual(len(result["edge_residuals"]), 3)

if __name__ == "__main__":
    unittest.main(verbosity=2)
