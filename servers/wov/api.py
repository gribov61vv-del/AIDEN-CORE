#!/usr/bin/env python
from flask import Flask, request, jsonify
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import core

app = Flask(__name__)
app.json.ensure_ascii = False

@app.route("/ping")
def ping():
    return jsonify({"status":"ok"})

@app.route("/ask", methods=["GET", "POST"])
def ask():
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        q = str(data.get("message", data.get("q", "")))
    else:
        q = request.args.get("q", "")
    return jsonify({"answer": "WOV-CORE активирован: " + q})

@app.route("/ui")
def ui():
    with open("webui/index.html") as f:
        return f.read()

@app.route("/quote", methods=["GET", "POST"])
def quote():
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
    else:
        data = {}

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
            "total": round(material_sum + labor_sum, 2)
        })

    total = materials + labor

    return {
        "status": "ok",
        "service": "AIDEN WOV QUOTE",
        "items": result,
        "materials": round(materials, 2),
        "labor": round(labor, 2),
        "total": round(total, 2),
        "currency": data.get("currency", "UAH")
    }

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
