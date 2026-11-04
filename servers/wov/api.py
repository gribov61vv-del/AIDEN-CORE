from pathlib import Path
import os
import sys
import json
import time
import uuid
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from flask import Flask, request, jsonify

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
import core

TRIAD_URL = "http://127.0.0.1:8002"
TRIAD_TIMEOUT = 4
AIDEN_URL = "http://127.0.0.1:8003"
AIDEN_TIMEOUT = 90

app = Flask(__name__)
app.json.ensure_ascii = False
app.json.mimetype = "application/json; charset=utf-8"


def new_request_id():
    return str(uuid.uuid4())


def is_mostly_cyrillic(text):
    letters = [ch for ch in str(text) if ch.isalpha()]
    if not letters:
        return False
    cyrillic = sum(0x0400 <= ord(ch) <= 0x04FF for ch in letters)
    return cyrillic / len(letters) >= 0.25


def triad_request(path, payload=None, request_id=None):
    if payload is not None and request_id:
        payload = dict(payload)
        payload["request_id"] = request_id
    data = None
    headers = {}
    method = "GET"
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json; charset=utf-8"
        method = "POST"
    req = Request(TRIAD_URL + path, data=data, headers=headers, method=method)
    with urlopen(req, timeout=TRIAD_TIMEOUT) as response:
        return json.loads(response.read().decode("utf-8"))


def aiden_request(message, request_id=None):
    payload = {
        "model": "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf",
        "messages": [
            {"role": "system", "content": "Ты — Aiden, локальный помощник Symbiosis. Отвечай по-русски, кратко и по существу. Не утверждай, что проверил факты или выполнил действия, если этого не было."},
            {"role": "user", "content": message},
        ],
        "temperature": 0.2,
        "max_tokens": 96,
        "stream": False,
    }
    if request_id:
        payload["user"] = request_id
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = Request(
        AIDEN_URL + "/v1/chat/completions",
        data=data,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    with urlopen(req, timeout=AIDEN_TIMEOUT) as response:
        result = json.loads(response.read().decode("utf-8"))
    choices = result.get("choices") or []
    if not choices:
        raise ValueError("Локальная модель вернула пустой список choices")
    answer = choices[0].get("message", {}).get("content", "").strip()
    if not answer:
        raise ValueError("Локальная модель вернула пустой ответ")
    return answer, result.get("timings", {})


@app.route("/ping")
def ping():
    try:
        triad = triad_request("/ping")
        return jsonify({
            "status": "ok",
            "service": "WOV-AIDEN-GATEWAY",
            "triad": "online",
            "memory_records": triad.get("memory_records"),
        })
    except (URLError, HTTPError, TimeoutError, ValueError) as exc:
        return jsonify({
            "status": "degraded",
            "service": "WOV-AIDEN-GATEWAY",
            "triad": "offline",
            "error": str(exc),
        }), 503


@app.route("/ask", methods=["GET", "POST"])
def ask():
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        q = str(data.get("message", data.get("q", "")))
    else:
        q = request.args.get("q", "")

    if not q.strip():
        return jsonify({"error": "Пустой запрос", "engine": "TRIAD-local"}), 400

    request_id = new_request_id()
    try:
        result = triad_request("/ask", {"q": q}, request_id=request_id)
        if result.get("request_id") != request_id:
            raise ValueError("TRIAD request_id mismatch")
        return jsonify({
            "request_id": request_id,
            "answer": result.get("answer", "TRIAD вернул пустой ответ"),
            "engine": "TRIAD-local",
            "triad": result,
        })
    except (URLError, HTTPError, TimeoutError, ValueError) as exc:
        return jsonify({
            "error": "Локальный TRIAD недоступен; фиктивный ответ не подставлен.",
            "details": str(exc),
            "engine": "WOV-CORE",
        }), 503


@app.route("/think", methods=["GET", "POST"])
def think():
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        q = str(data.get("message", data.get("q", "")))
    else:
        q = request.args.get("q", "")

    if not q.strip():
        return jsonify({"error": "Пустой запрос", "engine": "TRIAD+TinyLlama"}), 400

    request_id = new_request_id()
    try:
        triad = triad_request("/ask", {"q": q.strip()}, request_id=request_id)
        if triad.get("request_id") != request_id:
            raise ValueError("TRIAD request_id mismatch")
        calculation = triad.get("calculation") or {}
        if calculation.get("exact") is True:
            return jsonify({
                "status": "ok",
                "request_id": request_id,
                "answer": triad.get("answer", str(calculation.get("result"))),
                "engine": "TRIAD-exact",
                "triad": triad,
                "experimental": False,
                "answer_verified": True,
                "model_skipped": "TRIAD returned an exact calculation.",
            })
        # TinyLlama has a 1024-token context. Keep the input compact and
        # reserve room for the generated answer to avoid HTTP 400 overflow.
        triad_summary = {
            "answer": str(triad.get("answer", ""))[:320],
            "calculation": triad.get("calculation"),
            "trace": triad.get("trace"),
        }
        context = (
            "Вопрос: " + q.strip()[:240]
            + "\nФакты TRIAD: "
            + json.dumps(triad_summary, ensure_ascii=False, separators=(",", ":"))
            + "\nОтветь по-русски, кратко, только по фактам TRIAD. "
            + "Не выдумывай."
        )
        answer, timings = aiden_request(context, request_id=request_id)
        model_fallback = None
        engine = "TRIAD+TinyLlama-local"
        if not is_mostly_cyrillic(answer):
            answer = triad.get("answer") or "TinyLlama вернула ответ не на русском; исходный ответ TRIAD отсутствует."
            engine = "TRIAD-fallback"
            model_fallback = "TinyLlama ответила не по-русски; возвращён исходный результат TRIAD."
        return jsonify({
            "status": "ok",
            "request_id": request_id,
            "answer": answer,
            "engine": engine,
            "triad": triad,
            "experimental": True,
            "answer_verified": False,
            "model_fallback": model_fallback,
            "timings": timings,
        })
    except (URLError, HTTPError, TimeoutError, ValueError, KeyError) as exc:
        return jsonify({
            "status": "error",
            "error": "Составной запрос TRIAD + Aiden не выполнен.",
            "details": str(exc)[:240],
            "engine": "TRIAD+TinyLlama-local",
        }), 503


@app.route("/aiden", methods=["GET", "POST"])
def aiden_chat():
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        q = str(data.get("message", data.get("q", "")))
    else:
        q = request.args.get("q", "")

    if not q.strip():
        return jsonify({"error": "Пустой запрос", "engine": "TinyLlama-local"}), 400

    request_id = new_request_id()
    try:
        answer, timings = aiden_request(q.strip(), request_id=request_id)
        return jsonify({
            "status": "ok",
            "request_id": request_id,
            "answer": answer,
            "engine": "TinyLlama-local",
            "experimental": True,
            "verified_by_triad": False,
            "timings": timings,
        })
    except (URLError, HTTPError, TimeoutError, ValueError, KeyError) as exc:
        return jsonify({
            "status": "error",
            "error": "Локальная модель Aiden недоступна или вернула некорректный ответ.",
            "details": str(exc)[:240],
            "engine": "TinyLlama-local",
        }), 503


def probe_service(url):
    try:
        req = Request(url, method="GET")
        with urlopen(req, timeout=1.5) as response:
            return {"status": "online", "http": response.status}
    except Exception as exc:
        return {"status": "offline", "error": str(exc)[:160]}


def heartbeat_status(path):
    item = Path(path)
    if not item.exists():
        return {"status": "missing"}
    age = max(0.0, time.time() - item.stat().st_mtime)
    return {
        "status": "online" if age <= 30 else "stale",
        "age_seconds": round(age, 1),
    }


@app.route("/system")
def system_status():
    root = Path.home() / "AIDEN_FINAL_BUILD" / "symbiosis"
    services = {
        "triad": probe_service(TRIAD_URL + "/ping"),
        "pikachu": probe_service("http://127.0.0.1:8001/ping"),
        "aiden_llm": probe_service(AIDEN_URL + "/health"),
    }
    workers = {
        "aiden": heartbeat_status(root / "aiden.heartbeat"),
        "bug_core": heartbeat_status(root / "bug_core.heartbeat"),
        "bug_transformer": heartbeat_status(root / "bug_transformer.heartbeat"),
        "support": heartbeat_status(root / "support.heartbeat"),
    }
    local_state = {}
    state_file = root / "aiden_state.json"
    if state_file.exists():
        try:
            state = json.loads(state_file.read_text(encoding="utf-8"))
            local_state = {
                "mode": state.get("mode"),
                "api": state.get("api"),
                "api_key_configured": bool(state.get("api_key")),
                "model_exists": Path(state.get("model", "")).is_file(),
                "engine_exists": Path(state.get("engine", "")).is_file(),
            }
        except Exception as exc:
            local_state = {"error": str(exc)[:160]}

    all_statuses = [v["status"] for v in services.values()] + [v["status"] for v in workers.values()]
    overall = "ok" if all(s == "online" for s in all_statuses) else "degraded"
    return jsonify({
        "status": overall,
        "gateway": "WOV-AIDEN",
        "services": services,
        "symbiosis_workers": workers,
        "local_inference": local_state,
    })


@app.route("/ui")
def ui():
    return (BASE / "webui" / "index.html").read_text(encoding="utf-8")


@app.route("/quote", methods=["GET", "POST"])
def quote():
    data = request.get_json(silent=True) or {} if request.method == "POST" else {}
    items = data.get("items", [])
    if not isinstance(items, list):
        return {"error": "items должен быть списком"}, 400
    result = []
    materials = 0.0
    labor = 0.0
    for item in items:
        name = str(item.get("name", "Работа"))
        qty = float(item.get("qty", 1))
        material_price = float(item.get("material_price", 0))
        labor_price = float(item.get("labor_price", 0))
        material_sum = qty * material_price
        labor_sum = qty * labor_price
        materials += material_sum
        labor += labor_sum
        result.append({
            "name": name,
            "qty": qty,
            "material": round(material_sum, 2),
            "labor": round(labor_sum, 2),
            "total": round(material_sum + labor_sum, 2),
        })
    return {
        "status": "ok",
        "service": "AIDEN WOV QUOTE",
        "items": result,
        "materials": round(materials, 2),
        "labor": round(labor, 2),
        "total": round(materials + labor, 2),
        "currency": data.get("currency", "UAH"),
    }


if __name__ == "__main__":
    app.run(host=os.environ.get("AIDEN_BIND_HOST", "127.0.0.1"), port=8000)
