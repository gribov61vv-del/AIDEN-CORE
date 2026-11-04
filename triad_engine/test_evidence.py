#!/usr/bin/env python3
"""Isolated API tests for the append-only evidence ledger."""
import sqlite3
import tempfile
from pathlib import Path
import triad_api

def main():
    with tempfile.TemporaryDirectory() as td:
        db = Path(td) / "test_memory.sqlite3"
        with sqlite3.connect(db) as con:
            con.execute("""CREATE TABLE memory (
                id INTEGER PRIMARY KEY, content TEXT NOT NULL, kind TEXT NOT NULL,
                tags TEXT NOT NULL, confidence REAL NOT NULL, source TEXT NOT NULL,
                created_at REAL NOT NULL)""")
            con.execute("INSERT INTO memory VALUES(1,?,?,?,?,?,?)",
                        ("Example claim", "hypothesis", "test", 0.7, "unit-test", 0.0))
        old = triad_api.DB_PATH
        triad_api.DB_PATH = db
        client = triad_api.app.test_client()
        try:
            good = client.post("/evidence", json={
                "claim_id": 1, "relation": "supports",
                "evidence_type": "measurement", "statement": "Reading was 12.4",
                "source": "meter log, sample A", "confidence": 0.9})
            assert good.status_code == 201, good.get_json()
            eid = good.get_json()["id"]
            bad_id = client.post("/evidence", json={
                "claim_id": 999, "relation": "supports",
                "statement": "should not store", "source": "test"})
            assert bad_id.status_code == 400, bad_id.get_json()
            bad_rel = client.post("/evidence", json={
                "claim_id": 1, "relation": "proves", "statement": "x", "source": "test"})
            assert bad_rel.status_code == 400, bad_rel.get_json()
            bad_conf = client.post("/evidence", json={
                "claim_id": 1, "relation": "weakens", "statement": "x",
                "source": "test", "confidence": 2})
            assert bad_conf.status_code == 400, bad_conf.get_json()
            long_statement = client.post("/evidence", json={
                "claim_id": 1, "relation": "observes",
                "statement": "x" * 5001, "source": "test"})
            assert long_statement.status_code == 400, long_statement.get_json()
            long_source = client.post("/evidence", json={
                "claim_id": 1, "relation": "observes",
                "statement": "valid", "source": "s" * 1001})
            assert long_source.status_code == 400, long_source.get_json()
            duplicate = client.post("/evidence", json={
                "claim_id": 1, "relation": "supports",
                "evidence_type": "measurement", "statement": "Reading was 12.4",
                "source": "meter log, sample A", "confidence": 0.9})
            assert duplicate.status_code == 201, duplicate.get_json()
            assert duplicate.get_json()["id"] != eid, "duplicates remain separate append-only entries"
            listing = client.get("/evidence/1")
            assert listing.status_code == 200, listing.get_json()
            data = listing.get_json()
            assert data["claim"]["content"] == "Example claim"
            assert len(data["evidence"]) == 2
            assert data["evidence"][0]["id"] == eid
            assert data["evidence"][1]["id"] == duplicate.get_json()["id"]
            assert data["relation_counts"]["supports"] == 2
            assert data["pagination"] == {"page": 1, "per_page": 50, "total": 2, "has_more": False}
            assert data["assessment"] == "unreviewed_evidence_map"
            page_two = client.get("/evidence/1?page=2&per_page=1")
            assert page_two.status_code == 200, page_two.get_json()
            assert len(page_two.get_json()["evidence"]) == 1
            assert page_two.get_json()["pagination"]["has_more"] is False
            bad_page = client.get("/evidence/1?per_page=101")
            assert bad_page.status_code == 400
            with sqlite3.connect(db) as con:
                assert con.execute("SELECT COUNT(*) FROM memory").fetchone()[0] == 1
                assert con.execute("SELECT COUNT(*) FROM claim_evidence").fetchone()[0] == 2
            missing = client.get("/evidence/999")
            assert missing.status_code == 404
            print("TRIAD evidence tests: PASS (append-only storage, validation, retrieval)")
        finally:
            triad_api.DB_PATH = old

if __name__ == "__main__":
    main()
