import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import uvicorn
from core import PikachuCore

BASE = Path(__file__).resolve().parent
core = PikachuCore()
app = FastAPI(title="Pikachu")

@app.get("/ping")
def ping():
    return {"status": "ok"}

@app.get("/ask")
def ask(q: str):
    return {"answer": core.think(q)}

@app.get("/ui", response_class=HTMLResponse)
def ui():
    return (BASE / "webui" / "index.html").read_text(encoding="utf-8")

if __name__ == "__main__":
    uvicorn.run(app, host=os.environ.get("AIDEN_BIND_HOST", "127.0.0.1"), port=int(os.environ.get("PIKACHU_PORT", "8001")))
