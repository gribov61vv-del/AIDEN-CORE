#!/usr/bin/env python3
import math,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from zhulkor_rrem import Params,State,derivative,run

class RREMTests(unittest.TestCase):
    def test_zero_state_zero_input(self):
        self.assertEqual(derivative(0.0,State(),Params()),State())
    def test_finite_reference_run(self):
        rows=run(Params(duration=0.05))
        self.assertEqual(len(rows),5001)
        self.assertTrue(all(math.isfinite(v) for row in rows for v in row))
        self.assertGreaterEqual(min(r[5] for r in rows),0)
    def test_step_halving_converges(self):
        coarse=run(Params(dt=1e-5,duration=0.02))[-1]
        fine=run(Params(dt=5e-6,duration=0.02))[-1]
        for i in (1,2,3,4): self.assertLess(abs(coarse[i]-fine[i]),2e-5)
    def test_memory_accumulates(self):
        self.assertGreater(run(Params(duration=0.02))[-1][3],0)
    def test_resolution_guard(self):
        with self.assertRaises(ValueError): run(Params(dt=1e-3,duration=0.01))
    def test_energy_diagnostic_nonnegative(self):
        self.assertTrue(all(row[5]>=0 for row in run(Params(duration=0.02))))

if __name__=="__main__": unittest.main(verbosity=2)
