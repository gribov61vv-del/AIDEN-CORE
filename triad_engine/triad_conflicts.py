#!/usr/bin/env python3
"""Conservative candidate-conflict detection for TRIAD memory; never decides truth."""
from __future__ import annotations
import re
import sqlite3
from triad_core import DB_PATH, add_memory

NEGATIONS = {"не", "нет", "никогда", "невозможно", "ложно", "отсутствует", "отсутствуют", "not", "no", "never", "false", "absent"}
WORD_RE = re.compile(r"[a-zа-яёіїєґ0-9_]+", re.IGNORECASE)

def _words(s: str) -> set[str]:
    return {x.lower() for x in WORD_RE.findall(s) if len(x) > 1}

def candidate_conflicts(content: str, limit: int = 8) -> list[dict]:
    query = _words(content)
    if not query:
        return []
    results = []
    with sqlite3.connect(DB_PATH) as con:
        con.row_factory = sqlite3.Row
        rows = con.execute("SELECT id,content,kind,tags,confidence,source FROM memory ORDER BY id DESC LIMIT 5000").fetchall()
    for row in rows:
        other = _words(row["content"] + " " + row["tags"].replace(",", " "))
        shared = (query - NEGATIONS) & (other - NEGATIONS)
        base_a, base_b = query - NEGATIONS, other - NEGATIONS
        if not shared or not base_a or not base_b:
            continue
        neg_a, neg_b = bool(query & NEGATIONS), bool(other & NEGATIONS)
        overlap = len(shared) / max(1, len(base_a | base_b))
        if overlap >= 0.18 and (neg_a != neg_b or overlap >= 0.55):
            results.append({
                "memory_id": row["id"], "kind": row["kind"], "candidate": row["content"],
                "similarity_jaccard": round(overlap, 3), "negation_contrast": neg_a != neg_b,
                "status": "candidate_conflict_requires_review",
                "warning": "Heuristic only. Similar wording or negation does not establish a logical contradiction."
            })
        if len(results) >= max(1, min(20, limit)):
            break
    return results

def teach_with_conflict_check(content: str, kind: str = "fact", tags: str = "",
                              confidence: float = 1.0, source: str = "user") -> dict:
    candidates = candidate_conflicts(content)
    stored = add_memory(content, kind, tags, confidence, source)
    stored["candidate_conflicts"] = candidates
    stored["conflict_policy"] = "append_only_preserve_both"
    return stored
