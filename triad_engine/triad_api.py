#!/usr/bin/env python3
from flask import Flask, jsonify, request
from triad_core import ask, add_memory, analyze_triad, DB_PATH
import uuid
from triad_science import compare_dimensions, DimensionError
from triad_conflicts import candidate_conflicts, teach_with_conflict_check
import sqlite3

app = Flask(__name__)
app.config["JSON_AS_ASCII"] = False

@app.get('/ping')
def ping():
    with sqlite3.connect(DB_PATH) as con:
        count = con.execute('SELECT COUNT(*) FROM memory').fetchone()[0]
    return jsonify({'status':'ok','engine':'TRIAD-local','llm_required':False,'memory_records':count})

def attach_request_id(result, supplied_id=None):
    # Preserve a valid caller ID; generate one for direct TRIAD clients.
    try:
        request_id = str(uuid.UUID(str(supplied_id))) if supplied_id else str(uuid.uuid4())
    except (ValueError, TypeError, AttributeError):
        request_id = str(uuid.uuid4())
    result["request_id"] = request_id
    return result


@app.get('/ask')
def ask_get():
    result = ask(request.args.get('q',''))
    return jsonify(attach_request_id(result, request.args.get('request_id')))


@app.post('/ask')
def ask_post():
    data = request.get_json(silent=True) or {}
    result = ask(str(data.get('q','')))
    return jsonify(attach_request_id(result, data.get('request_id')))

@app.post('/triad')
def triad():
    data = request.get_json(silent=True) or {}
    try:
        values = data.get('values', [])
        if not isinstance(values, list):
            raise ValueError("values must be a list of three numbers")
        return jsonify(analyze_triad(values))
    except (ValueError, TypeError) as exc:
        return jsonify({'error': str(exc)}), 400

@app.post('/dimensions')
def dimensions():
    data = request.get_json(silent=True) or {}
    try:
        lhs, rhs, symbols = data.get('lhs', ''), data.get('rhs', ''), data.get('symbols', {})
        if not isinstance(symbols, dict):
            raise DimensionError("symbols must be an object mapping names to dimension vectors")
        return jsonify(compare_dimensions(lhs, rhs, symbols))
    except (DimensionError, ValueError, TypeError) as exc:
        return jsonify({'error': str(exc)}), 400

@app.post('/conflicts')
def conflicts():
    data = request.get_json(silent=True) or {}
    content = data.get('content', '')
    if not isinstance(content, str) or not content.strip():
        return jsonify({'error':'content must be a non-empty string'}), 400
    return jsonify({'candidates':candidate_conflicts(content), 'policy':'heuristic_candidates_only'})

@app.get('/memory')
def memory_stats():
    with sqlite3.connect(DB_PATH) as con:
        total = con.execute('SELECT COUNT(*) FROM memory').fetchone()[0]
        kinds = dict(con.execute('SELECT kind, COUNT(*) FROM memory GROUP BY kind').fetchall())
        size = DB_PATH.stat().st_size if DB_PATH.exists() else 0
    return jsonify({'records':total,'by_kind':kinds,'database_bytes':size,'storage':'local SQLite; grows as records are added; bounded by device storage'})

@app.post('/teach')
def teach():
    data = request.get_json(silent=True) or {}
    try:
        result = teach_with_conflict_check(str(data.get('content','')), str(data.get('kind','fact')), str(data.get('tags','')), float(data.get('confidence',1.0)), str(data.get('source','user')))
        return jsonify(result), 201
    except (ValueError, TypeError) as exc:
        return jsonify({'stored':False,'error':str(exc)}), 400

@app.get('/claims')
def claims_list():
    query = request.args.get('q', '').strip()
    if len(query) > 120:
        return jsonify({'error': 'q must be at most 120 characters'}), 400
    try:
        limit = int(request.args.get('limit', '10'))
    except ValueError:
        return jsonify({'error': 'limit must be an integer'}), 400
    if not 1 <= limit <= 20:
        return jsonify({'error': 'limit must be between 1 and 20'}), 400
    with sqlite3.connect(DB_PATH) as con:
        con.row_factory = sqlite3.Row
        if query:
            rows = con.execute(
                "SELECT id,content,kind,tags,confidence,source FROM memory "
                "WHERE instr(content, ?) > 0 OR instr(tags, ?) > 0 "
                "ORDER BY id DESC LIMIT ?", (query, query, limit)).fetchall()
        else:
            rows = con.execute(
                "SELECT id,content,kind,tags,confidence,source FROM memory ORDER BY id DESC LIMIT ?",
                (limit,)).fetchall()
    return jsonify({'claims': [dict(row) for row in rows], 'count': len(rows),
                    'search': query, 'matching': 'substring; not semantic search'})

def init_evidence_table():
    with sqlite3.connect(DB_PATH) as con:
        con.execute("""CREATE TABLE IF NOT EXISTS claim_evidence (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            claim_id INTEGER NOT NULL,
            relation TEXT NOT NULL,
            evidence_type TEXT NOT NULL,
            statement TEXT NOT NULL,
            source TEXT NOT NULL,
            confidence REAL NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )""")
        con.execute("CREATE INDEX IF NOT EXISTS idx_claim_evidence_claim ON claim_evidence(claim_id, id)")
        con.commit()

@app.post('/evidence')
def evidence_add():
    data = request.get_json(silent=True) or {}
    try:
        claim_id = int(data.get('claim_id', 0))
        relation = str(data.get('relation', '')).strip().lower()
        etype = str(data.get('evidence_type', 'other')).strip().lower()
        statement = str(data.get('statement', '')).strip()
        source = str(data.get('source', '')).strip()
        confidence = float(data.get('confidence', 0.5))
        if relation not in {'supports', 'weakens', 'qualifies', 'observes'}:
            raise ValueError("relation must be supports, weakens, qualifies, or observes")
        if etype not in {'observation', 'measurement', 'calculation', 'document', 'interpretation', 'other'}:
            raise ValueError("unsupported evidence_type")
        if not statement or len(statement) > 5000 or not source or len(source) > 1000:
            raise ValueError("statement/source empty or too long")
        if not 0 <= confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")
        init_evidence_table()
        with sqlite3.connect(DB_PATH) as con:
            if not con.execute('SELECT 1 FROM memory WHERE id=?', (claim_id,)).fetchone():
                raise ValueError("claim_id does not exist in memory")
            cur = con.execute('INSERT INTO claim_evidence(claim_id,relation,evidence_type,statement,source,confidence) VALUES(?,?,?,?,?,?)',
                              (claim_id, relation, etype, statement, source, confidence))
            evidence_id = cur.lastrowid
            con.commit()
        return jsonify({'stored': True, 'id': evidence_id, 'claim_id': claim_id,
                        'relation': relation, 'evidence_type': etype,
                        'policy': 'append_only_no_automatic_truth_verdict'}), 201
    except (ValueError, TypeError) as exc:
        return jsonify({'stored': False, 'error': str(exc)}), 400

@app.get('/evidence/<int:claim_id>')
def evidence_list(claim_id):
    try:
        page = int(request.args.get('page', '1'))
        per_page = int(request.args.get('per_page', '50'))
        if page < 1 or per_page < 1 or per_page > 100:
            raise ValueError("page must be >= 1 and per_page must be between 1 and 100")
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 400
    init_evidence_table()
    offset = (page - 1) * per_page
    with sqlite3.connect(DB_PATH) as con:
        con.row_factory = sqlite3.Row
        claim = con.execute('SELECT id,content,kind,tags,confidence,source FROM memory WHERE id=?', (claim_id,)).fetchone()
        if claim is None:
            return jsonify({'error': 'claim_id does not exist in memory'}), 404
        total = con.execute('SELECT COUNT(*) FROM claim_evidence WHERE claim_id=?', (claim_id,)).fetchone()[0]
        count_rows = con.execute('SELECT relation, COUNT(*) AS n FROM claim_evidence WHERE claim_id=? GROUP BY relation', (claim_id,)).fetchall()
        rows = con.execute('SELECT id,relation,evidence_type,statement,source,confidence,created_at FROM claim_evidence WHERE claim_id=? ORDER BY id LIMIT ? OFFSET ?', (claim_id, per_page, offset)).fetchall()
    items = [dict(row) for row in rows]
    counts = {r: 0 for r in ('supports','weakens','qualifies','observes')}
    counts.update({row['relation']: row['n'] for row in count_rows if row['relation'] in counts})
    return jsonify({'claim': dict(claim), 'evidence': items, 'relation_counts': counts,
                    'pagination': {'page': page, 'per_page': per_page, 'total': total,
                                   'has_more': offset + len(items) < total},
                    'assessment': 'unreviewed_evidence_map',
                    'warning': 'Counts and confidence are not proof; inspect source quality and context.'})

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8002, threaded=True)
