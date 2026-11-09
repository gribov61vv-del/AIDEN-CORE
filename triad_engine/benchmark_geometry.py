#!/usr/bin/env python3
"""Reproducible synthetic benchmark: complete/noisy/sparse distance graphs."""
import math
from geometry_methods import classical_mds, smacof_fit
from structure_inference import infer_geometry

NAMES = [f"N{i}" for i in range(8)]
TRUTH = [
    (0.0,0.0,0.0),(2.0,0.1,0.0),(0.2,2.8,0.1),(0.0,0.2,3.7),
    (2.1,2.6,3.2),(3.0,-1.0,1.2),(-1.0,1.0,2.0),(1.3,1.4,-1.0)
]

def dataset(noisy=False, sparse=False):
    edges = []
    for i in range(len(TRUTH)):
        for j in range(i+1,len(TRUTH)):
            d = math.dist(TRUTH[i], TRUTH[j])
            if noisy:
                d *= 1.0 + 0.025 * math.sin((i+1)*13 + (j+1)*7)
            if sparse and ((i*3+j*5) % 4 == 0):
                continue
            edges.append({"a":NAMES[i],"b":NAMES[j],"distance":d})
    return edges

def report(label, edges, noisy=False, include_mds=False):
    print(f"\n[{label}] edges={len(edges)} nodes={len(NAMES)}")
    gd = infer_geometry(NAMES, edges, 3, 20000, 0.01,
                        reject_triangle_violations=not noisy)
    if gd["status"] == "fitted":
        print(f"{'gradient_descent':18s} stress={gd['weighted_mean_squared_distance_error']:.10g}")
        if gd.get("triangle_inequality_violations"):
            print(f"  triangle violations reported={len(gd['triangle_inequality_violations'])}")
    else:
        print(f"{'gradient_descent':18s} status={gd['status']} violations={len(gd.get('triangle_inequality_violations', []))}")
    sm = smacof_fit(NAMES, edges, 3, 500)
    print(f"{'SMACOF':18s} stress={sm['weighted_mean_squared_distance_error']:.10g} iterations={sm['iterations_completed']}")
    if include_mds:
        complete = [[0.0]*len(NAMES) for _ in NAMES]
        for e in edges:
            i,j=NAMES.index(e["a"]),NAMES.index(e["b"])
            complete[i][j]=complete[j][i]=e["distance"]
        mds=classical_mds(NAMES,complete,3)
        print(f"{'classical_MDS':18s} negative_eigen_mass={mds['negative_eigenvalue_mass']:.8g}")

if __name__ == "__main__":
    report("complete_exact", dataset(), include_mds=True)
    report("complete_noisy", dataset(noisy=True), noisy=True, include_mds=True)
    report("sparse_noisy", dataset(noisy=True,sparse=True), noisy=True)
