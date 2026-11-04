#!/usr/bin/env python3
import sqlite3, tempfile
from pathlib import Path
import triad_conflicts

def main():
    with tempfile.TemporaryDirectory() as td:
        db = Path(td) / "memory.sqlite3"
        with sqlite3.connect(db) as con:
            con.execute("""CREATE TABLE memory (
                id INTEGER PRIMARY KEY, content TEXT NOT NULL, kind TEXT NOT NULL,
                tags TEXT NOT NULL, confidence REAL NOT NULL, source TEXT NOT NULL,
                created_at REAL NOT NULL)""")
            con.execute("INSERT INTO memory VALUES(1,?,?,?,?,?,?)", (
                "The sensor is active", "fact", "sensor active", 1.0, "test", 0.0))
            con.execute("INSERT INTO memory VALUES(2,?,?,?,?,?,?)", (
                "The sensor is not active", "fact", "sensor active", 1.0, "test", 0.0))
        old = triad_conflicts.DB_PATH
        triad_conflicts.DB_PATH = db
        try:
            hits = triad_conflicts.candidate_conflicts("The sensor is active")
            assert hits, "expected a candidate from overlapping memory"
            assert all(x["status"] == "candidate_conflict_requires_review" for x in hits)
            assert any(x["negation_contrast"] for x in hits), "expected negation contrast"
            print("TRIAD conflict tests: PASS (candidate detection, cautious labeling)")
        finally:
            triad_conflicts.DB_PATH = old

def test_evidence_endpoints():
    # Exercise the API against an isolated temporary DB, never production memory.
    import triad_api
    with tempfile.TemporaryDirectory() as td:
        db = Path(td) / "test_memory.sqlite3"
        with sqlite3.connect(db) as con:
            con.execute("""CREATE TABLE memory (
                id INTEGER PRIMARY KEY, content TEXT NOT NULL, kind TEXT NOT NULL,
                tags TEXT NOT NULL, confidence REAL NOT NULL, source TEXT NOT NULL,
                created_at REAL NOT NULL)""")
            con.execute("INSERT INTO memory VALUES(1,?,?,?,?,?,?)",
                        ("Test claim", "hypothesis", "test", 0.5, "test-suite", 0.0))
        old_db = triad_api.DB_PATH
        triad_api.DB_PATH = db
        triad_api.app.config["TESTING"] = True
        try:
            client = triad_api.app.test_client()
            r = client.get("/claims")
            assert r.status_code == 200 and r.get_json()["claims"][0]["id"] == 1
            r = client.get("/claims?q=Test%20claim")
            assert r.status_code == 200 and r.get_json()["count"] == 1
            r = client.get("/claims?limit=99")
            assert r.status_code == 400
            r = client.post("/evidence", json={
                "claim_id": 1, "relation": "supports",
                "evidence_type": "measurement", "statement": "Test measurement",
                "source": "test-fixture", "confidence": 0.75})
            assert r.status_code == 201, (r.status_code, r.get_json())
            evidence_id = r.get_json()["id"]
            r = client.get("/evidence/1")
            body = r.get_json()
            assert r.status_code == 200 and body["claim"]["content"] == "Test claim"
            assert len(body["evidence"]) == 1 and body["evidence"][0]["id"] == evidence_id
            assert body["relation_counts"]["supports"] == 1
            r = client.post("/evidence", json={
                "claim_id": 1, "relation": "invented",
                "statement": "Bad relation", "source": "test"})
            assert r.status_code == 400, (r.status_code, r.get_json())
            r = client.post("/evidence", json={
                "claim_id": 999, "relation": "supports",
                "statement": "Orphan", "source": "test"})
            assert r.status_code == 400, (r.status_code, r.get_json())
            with sqlite3.connect(db) as con:
                count = con.execute("SELECT COUNT(*) FROM claim_evidence").fetchone()[0]
            assert count == 1, f"expected one valid evidence row, got {count}"
        finally:
            triad_api.DB_PATH = old_db
    print("TRIAD evidence tests: PASS (append, retrieval, validation, isolated DB)")

if __name__ == "__main__":
    main()
    test_evidence_endpoints()
