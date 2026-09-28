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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
