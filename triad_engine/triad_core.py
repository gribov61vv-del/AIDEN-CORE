#!/usr/bin/env python3
"""TRIAD: lightweight, local, auditable reasoning + persistent memory.
No LLM, cloud calls, model downloads, or third-party packages required by core.
"""
from __future__ import annotations
import ast
import json
import math
import operator
import re
import sqlite3
import time
from pathlib import Path
from typing import Any

BASE = Path(__file__).resolve().parent
DB_PATH = BASE / "memory.sqlite3"

# Three independent passes: evidence, computation/logic, and consistency.
TOKEN_RE = re.compile(r"[a-zа-яёіїєґ0-9_]+", re.IGNORECASE)
STOP = set("и а но да в во на к ко с со по за из от до для при про это эта этот этаже как что где когда почему зачем ли или не нет да мы вы ты я он она они оно быть был была были есть будет уже ещё очень просто тогда именно можно нужно хочу сделай сделаем модель память алгоритм".split())

OPS = {
    ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
    ast.Div: operator.truediv, ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod, ast.Pow: operator.pow,
    ast.UAdd: operator.pos, ast.USub: operator.neg,
}

SEED = [
    ("Архитектурная цепочка проекта: источник — пользователь; буфер и координатор — Aiden; получатель — Жук. Это концепция архитектуры, а не подтверждённый физический механизм.", "project_fact", "aiden,zhuk,architecture", 1.0),
    ("Модель A «цифровой материк»: поле, локализация, восстановление, память, устойчивые X-состояния и неизвестный параметр Z. Рассматривать отдельно от модели B.", "project_model", "digital_continent,model_a", 1.0),
    ("Модель B: физическая гипотеза образования инвариантной массы при взаимодействии фотонов/частиц через энергию, импульс и инвариантную массу. Рассматривать независимо от модели A до отдельного обоснования связи.", "project_model", "mass,photons,model_b", 1.0),
    ("Тройная точка / тройной энергетический узел — исследовательская гипотеза проекта. Не объявлять доказанным физическим законом без измерений и математического вывода.", "hypothesis", "triple_point,energy,physics", 0.8),
    ("Память TRIAD хранится в локальной SQLite-базе и может расти по мере добавления записей; практический предел задаётся свободным диском, временем поиска и качеством отбора, поэтому бесконечной физически она не является.", "system_fact", "memory,sqlite,limits", 1.0),
    ("Правило: отделять факты, гипотезы, решения и вопросы. Не сливать разные модели без отдельного обоснования; указывать неопределённость.", "decision", "method,verification", 1.0),
]


def tokens(text: str) -> list[str]:
    return [t.lower() for t in TOKEN_RE.findall(text) if len(t) > 1 and t.lower() not in STOP]


def init_db() -> None:
    with sqlite3.connect(DB_PATH) as con:
        con.execute("PRAGMA journal_mode=WAL")
        con.execute("""CREATE TABLE IF NOT EXISTS memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            kind TEXT NOT NULL DEFAULT 'fact',
            tags TEXT NOT NULL DEFAULT '',
            confidence REAL NOT NULL DEFAULT 1.0,
            source TEXT NOT NULL DEFAULT 'local',
            created_at REAL NOT NULL
        )""")
        con.execute("CREATE INDEX IF NOT EXISTS idx_memory_kind ON memory(kind)")
        count = con.execute("SELECT COUNT(*) FROM memory").fetchone()[0]
        if count == 0:
            now = time.time()
            con.executemany(
                "INSERT INTO memory(content,kind,tags,confidence,source,created_at) VALUES(?,?,?,?,?,?)",
                [(c,k,t,conf,"seed/project_context",now) for c,k,t,conf in SEED],
            )
        con.commit()


def add_memory(content: str, kind: str = "fact", tags: str = "", confidence: float = 1.0, source: str = "user") -> dict[str, Any]:
    content = content.strip()
    if not content:
        raise ValueError("content cannot be empty")
    if kind not in {"fact", "hypothesis", "decision", "question", "project_fact", "project_model", "system_fact", "note"}:
        raise ValueError("unsupported kind")
    confidence = max(0.0, min(1.0, float(confidence)))
    with sqlite3.connect(DB_PATH) as con:
        cur = con.execute(
            "INSERT INTO memory(content,kind,tags,confidence,source,created_at) VALUES(?,?,?,?,?,?)",
            (content, kind, tags[:500], confidence, source[:200], time.time()),
        )
        mid = cur.lastrowid
        con.commit()
    return {"id": mid, "kind": kind, "confidence": confidence, "stored": True}


def search_memory(query: str, limit: int = 5) -> list[dict[str, Any]]:
    q = set(tokens(query))
    if not q:
        return []
    with sqlite3.connect(DB_PATH) as con:
        con.row_factory = sqlite3.Row
        rows = con.execute("SELECT * FROM memory ORDER BY id DESC LIMIT 5000").fetchall()
    scored = []
    for row in rows:
        words = set(tokens(row["content"] + " " + row["tags"].replace(",", " ")))
        if not words:
            continue
        overlap = len(q & words)
        if not overlap:
            continue
        # Lightweight lexical relevance with a small confidence adjustment.
        coverage = overlap / max(1, len(q))
        precision = overlap / max(1, len(words))
        score = (0.75 * coverage + 0.25 * math.sqrt(precision)) * (0.8 + 0.2 * row["confidence"])
        scored.append((score, row))
    scored.sort(key=lambda pair: (pair[0], pair[1]["id"]), reverse=True)
    return [{"id": r["id"], "content": r["content"], "kind": r["kind"], "tags": r["tags"],
             "confidence": r["confidence"], "source": r["source"], "score": round(s, 4)}
            for s, r in scored[:max(1, min(20, limit))]]


def safe_calculate(expression: str) -> dict[str, Any] | None:
    expr = expression.strip().replace("×", "*").replace("÷", "/").replace("−", "-").replace(",", ".")
    if len(expr) > 160 or not re.fullmatch(r"[0-9eE.+*/%() \-]+", expr):
        return None
    try:
        tree = ast.parse(expr, mode="eval")
        nodes = list(ast.walk(tree))
        if len(nodes) > 80:
            return None
        def visit(node):
            if isinstance(node, ast.Expression): return visit(node.body)
            if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
                if abs(node.value) > 1e100: raise ValueError("number too large")
                return node.value
            if isinstance(node, ast.BinOp) and type(node.op) in OPS:
                a, b = visit(node.left), visit(node.right)
                if isinstance(node.op, ast.Pow) and (abs(b) > 100 or abs(a) > 1e50): raise ValueError("power limit")
                result = OPS[type(node.op)](a, b)
                if not math.isfinite(float(result)) or abs(result) > 1e100: raise ValueError("result out of bounds")
                return result
            if isinstance(node, ast.UnaryOp) and type(node.op) in OPS:
                return OPS[type(node.op)](visit(node.operand))
            raise ValueError("unsupported expression")
        value = visit(tree)
        return {"expression": expr, "result": value, "exact": isinstance(value, int) or float(value).is_integer()}
    except (SyntaxError, ValueError, ZeroDivisionError, OverflowError, TypeError):
        return None


def triple_check(query: str, memories: list[dict[str, Any]], calculation: dict[str, Any] | None) -> dict[str, Any]:
    evidence = "found" if memories else "not_found"
    logic = "computed" if calculation is not None else "no_safe_calculation"
    cautions = []
    if not memories and calculation is None:
        cautions.append("No supporting memory or safely parseable arithmetic expression; do not invent an answer.")
    if any(m["kind"] == "hypothesis" for m in memories):
        cautions.append("Retrieved material includes a hypothesis; it is not established fact.")
    if any(m["kind"] == "project_model" for m in memories) and ("модель" in query.lower() or "model" in query.lower()):
        cautions.append("Project models are kept separate unless a link is independently justified.")
    return {"point_1_evidence": evidence, "point_2_logic": logic, "point_3_check": "caution" if cautions else "passed", "cautions": cautions}


def analyze_triad(values: list[float]) -> dict[str, Any]:
    """Generic mathematical analysis of three channels; not a physics claim."""
    if len(values) != 3:
        raise ValueError("exactly three numeric values are required")
    xs = [float(v) for v in values]
    if not all(math.isfinite(v) and abs(v) <= 1e100 for v in xs):
        raise ValueError("values must be finite and within numeric bounds")
    mean = sum(xs) / 3.0
    variance = sum((v - mean) ** 2 for v in xs) / 3.0
    std = math.sqrt(variance)
    scale = abs(mean)
    balance = 1.0 / (1.0 + std / (scale if scale > 1e-12 else 1.0))
    total = sum(xs)
    shares = [v / total for v in xs] if abs(total) > 1e-12 else None
    return {
        "model": "TRIAD-3 generic state vector",
        "values": xs, "mean": mean, "variance_population": variance,
        "standard_deviation": std, "balance_index_0_to_1": balance,
        "normalized_shares": shares,
        "interpretation": "mathematical description of three inputs only; physical meaning must be supplied and experimentally validated"
    }


def ask(query: str) -> dict[str, Any]:
    query = query.strip()
    if not query:
        return {"answer": "Пустой запрос. Напиши вопрос или выражение.", "trace": triple_check(query, [], None), "memories": []}
    calculation = safe_calculate(query)
    memories = search_memory(query, 5)
    trace = triple_check(query, memories, calculation)
    if calculation is not None:
        answer = f"{calculation['expression']} = {calculation['result']}"
        if memories:
            answer += "\nСвязанные записи памяти приложены отдельно; они не меняют результат вычисления."
    elif memories:
        lines = [f"[{m['kind']} | уверенность {m['confidence']:.2f} | совпадение {m['score']:.2f}] {m['content']}" for m in memories[:3]]
        answer = "Нашёл опорные записи в локальной памяти:\n" + "\n".join(lines)
        answer += "\nЭто извлечение по совпадению терминов, не доказательство истинности записи."
    else:
        answer = "Пока нет надёжной опоры в локальной памяти и запрос не распознан как безопасное арифметическое выражение. Не буду выдумывать ответ. Можно добавить проверенный факт через /teach или сформулировать задачу точнее."
    return {"answer": answer, "trace": trace, "calculation": calculation, "memories": memories}

init_db()
