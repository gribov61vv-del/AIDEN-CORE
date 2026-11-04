#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from triad_science import compare_dimensions, dimension_of, DimensionError

D = {
    "m": {"L": 1},
    "s": {"T": 1},
    "kg": {"M": 1},
    "v": {"L": 1, "T": -1},
    "a": {"L": 1, "T": -2},
    "F": {"M": 1, "L": 1, "T": -2},
}

def check(condition, message):
    if not condition:
        raise AssertionError(message)

def main():
    # v = distance / time
    r = compare_dimensions("v", "m/s", D)
    check(r["dimensionally_consistent"], "velocity dimensions should match")
    # F = m*a
    r = compare_dimensions("F", "kg*a", D)
    check(r["dimensionally_consistent"], "force dimensions should match")
    # Wrong: v = distance * time
    r = compare_dimensions("v", "m*s", D)
    check(not r["dimensionally_consistent"], "wrong velocity dimensions should fail")
    # Addition of unlike dimensions must fail during parsing
    try:
        dimension_of("m+s", D)
        raise AssertionError("adding length and time should fail")
    except DimensionError:
        pass
    # Unknown symbols rejected
    try:
        dimension_of("m+unknown", D)
        raise AssertionError("unknown symbol should fail")
    except DimensionError:
        pass
    # Calls / attributes / arbitrary Python rejected
    for bad in ("__import__('os')", "m.real", "m[0]"):
        try:
            dimension_of(bad, D)
            raise AssertionError(f"unsafe expression accepted: {bad}")
        except DimensionError:
            pass
    print("TRIAD science tests: PASS (6 checks)")

if __name__ == "__main__":
    main()
