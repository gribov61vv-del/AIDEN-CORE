# TRIAD-GEO method comparison

This research extension adds two independent classical baselines:
- **Classical metric MDS**: reconstructs coordinates from a complete distance matrix using double centering and a Jacobi symmetric eigensolver.
- **SMACOF**: weighted majorization for connected sparse distance graphs, with stress history to check monotonic convergence.

The existing weighted gradient-descent fitter remains unchanged. All methods are standard-library Python and isolated from the live TRIAD API and SQLite memory.

## Tests

    cd ~/AIDEN-CORE/triad_engine
    python -m unittest -v test_structure_inference.py test_geometry_methods.py

## Reproducible benchmark

    python benchmark_geometry.py

The benchmark uses a fixed synthetic 3D point set and reports:
- complete exact distances;
- complete distances with deterministic bounded noise;
- incomplete sparse distances with deterministic noise.

Stress is a fit-error measure, not a calibrated confidence score. Sparse distance geometry can be non-unique. Classical MDS requires a complete distance matrix. A method comparison is not evidence that any method predicts protein folds.


## Benchmark snapshot (Termux, Python standard library)

Synthetic benchmark: 8 known 3D points, 28 complete pair distances or 24 sparse edges. Noise is deterministic and bounded at approximately 2.5%; results are reproducible.

| Dataset | Gradient descent stress | SMACOF stress | Classical MDS diagnostic |
|---|---:|---:|---:|
| Complete, exact | 0.0612342 | 4.17e-12 | negative eigenvalue mass 5.18e-15 |
| Complete, noisy | 0.0690087 | 0.00098195 | negative eigenvalue mass 0.74179 |
| Sparse, noisy | 0.233549 | 0.0708323 | not applicable (incomplete matrix) |

Interpretation: SMACOF achieved the lowest weighted distance stress on these three synthetic cases. Classical MDS nearly exactly reconstructed the exact complete-distance geometry; the noisy complete matrix produced substantial negative eigenvalue mass, a warning that the observed distances are not exactly Euclidean in the requested embedding. The gradient-descent prototype is a weaker baseline here and should not be treated as a production optimizer.

A strict triangle-inequality rejection remains the default for the original fitter. For explicitly noisy observations, callers may set `reject_triangle_violations=False` to retain violations as diagnostics and fit a least-squares geometry instead. This does not make inconsistent observations physically true; it prevents measurement noise from being mistaken for a logical impossibility.

These are small synthetic tests, not a benchmark of protein structures, and the numeric results must not be generalized to biological prediction.
