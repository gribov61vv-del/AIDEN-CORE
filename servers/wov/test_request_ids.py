#!/usr/bin/env python3
"""Concurrent UUID correlation smoke test for the local WOV -> TRIAD API."""
import concurrent.futures
import json
import urllib.request

BASE = "http://127.0.0.1:8000"
CASES = [
    ("/ask", "19+23"),
    ("/ask", "7*8"),
    ("/ask", "144/12"),
    ("/ask", "2**8"),
    ("/think", "19+23"),
    ("/think", "7*8"),
    ("/think", "144/12"),
    ("/think", "2**8"),
]


def call(case):
    path, question = case
    payload = json.dumps({"message": question}).encode("utf-8")
    req = urllib.request.Request(
        BASE + path,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=20) as response:
        result = json.loads(response.read().decode("utf-8"))
    triad_id = (result.get("triad") or {}).get("request_id")
    request_id = result.get("request_id") or triad_id
    return path, question, request_id, triad_id, result.get("answer")


def main():
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(call, CASES))
    ids = [item[2] for item in results]
    assert all(ids), "a response did not include request_id"
    assert len(set(ids)) == len(ids), "duplicate request IDs"
    assert all(item[2] == item[3] for item in results), "WOV/TRIAD ID mismatch"
    for item in results:
        print(f"{item[0]} {item[1]} -> {item[4]} [{item[2]}]")
    print("PASS: 8 concurrent requests; unique IDs; WOV/TRIAD correlation intact")


if __name__ == "__main__":
    main()
