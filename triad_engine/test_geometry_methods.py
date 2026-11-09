#!/usr/bin/env python3
import math
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from geometry_methods import GeometryInputError, classical_mds, smacof_fit

class GeometryMethodTests(unittest.TestCase):
    def setUp(self):
        self.nodes = ["A", "B", "C", "D", "E"]
        self.points = [(0,0,0),(2,0,0),(0,3,0),(0,0,4),(2,3,4)]
        self.matrix = [[math.dist(a,b) for b in self.points] for a in self.points]
        self.edges = [{"a": self.nodes[i], "b": self.nodes[j], "distance": self.matrix[i][j]}
                      for i in range(len(self.nodes)) for j in range(i+1,len(self.nodes))]

    def test_classical_mds_reconstructs_complete_3d_distances(self):
        result = classical_mds(self.nodes, self.matrix, 3)
        self.assertEqual(result["status"], "fitted")
        coords = [result["coordinates"][n] for n in self.nodes]
        errors = [abs(math.dist(coords[i],coords[j])-self.matrix[i][j])
                  for i in range(5) for j in range(i+1,5)]
        self.assertLess(max(errors), 1e-6)

    def test_smacof_reduces_stress(self):
        result = smacof_fit(self.nodes, self.edges, 3, 300)
        self.assertLess(result["weighted_mean_squared_distance_error"], 1e-7)
        history = result["stress_history"]
        self.assertTrue(all(history[i+1] <= history[i] + 1e-9 for i in range(len(history)-1)))

    def test_smacof_accepts_sparse_connected_graph(self):
        sparse = [self.edges[i] for i in (0,1,2,4,6,7,8)]
        result = smacof_fit(self.nodes, sparse, 3, 100)
        self.assertEqual(result["status"], "fitted")

    def test_smacof_rejects_disconnected_graph(self):
        with self.assertRaises(GeometryInputError):
            smacof_fit(["A","B","C"], [{"a":"A","b":"B","distance":1}], 2)

    def test_mds_rejects_asymmetric_matrix(self):
        bad = [row[:] for row in self.matrix]
        bad[0][1] += 1
        with self.assertRaises(GeometryInputError):
            classical_mds(self.nodes, bad, 3)

if __name__ == "__main__":
    unittest.main(verbosity=2)
