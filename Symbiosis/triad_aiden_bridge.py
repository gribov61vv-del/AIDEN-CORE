#!/usr/bin/env python3
"""Aiden command-queue bridge backed by local TRIAD; no LLM inference."""
import hashlib, json, os, sys, time, uuid
from pathlib import Path
from datetime import datetime

BASE = Path(__file__).resolve().parent
TRIAD = Path.home() / "AIDEN-CORE" / "triad_engine"
sys.path.insert(0, str(TRIAD))
from triad_core import ask

CMD = BASE / "commands.txt"
PENDING = BASE / "commands.processing.txt"
BATCH_ID = BASE / "commands.processing.id"
RESP = BASE / "responses.txt"
LOG = BASE / "aiden_log.txt"
PID = BASE / "aiden.pid"
HEART = BASE / "aiden.heartbeat"
STATE = BASE / "aiden_state.json"

def log(msg):
    with LOG.open("a", encoding="utf-8") as f:
        f.write(f"[{datetime.now().isoformat()}] {msg}\n")
    print("[AIDEN-TRIAD]", msg, flush=True)

def acquire_batch():
    if PENDING.exists():
        if not BATCH_ID.exists():
            BATCH_ID.write_text(uuid.uuid4().hex, encoding="utf-8")
        return [x.strip() for x in PENDING.read_text(encoding="utf-8").splitlines() if x.strip()]
    if not CMD.exists():
        return []
    try:
        if not CMD.read_text(encoding="utf-8").strip():
            return []
        os.replace(CMD, PENDING)
        BATCH_ID.write_text(uuid.uuid4().hex, encoding="utf-8")
    except FileNotFoundError:
        return []
    return [x.strip() for x in PENDING.read_text(encoding="utf-8").splitlines() if x.strip()]


def append_response_once(batch_id, index, command, answer, trace):
    """Append one durable response per command position in a recovered batch."""
    event_id = hashlib.sha256(f"{batch_id}:{index}".encode("utf-8")).hexdigest()[:24]
    marker = f"EVENT_ID: {event_id}"
    if RESP.exists():
        with RESP.open("r", encoding="utf-8") as existing:
            if any(line.strip() == marker for line in existing):
                return False
    with RESP.open("a", encoding="utf-8") as output:
        output.write(
            f"{marker}\n[{datetime.now().isoformat()}]\n"
            f"USER: {command}\nAIDEN: {answer}\n"
            f"TRIAD_CHECK: {trace}\n\n"
        )
    return True

def main():
    PID.write_text(str(os.getpid()), encoding="utf-8")
    STATE.write_text(json.dumps({
        "name": "Aiden", "mode": "TRIAD-local-no-LLM",
        "engine": str(TRIAD), "api": False, "api_key": False,
        "queue_recovery": True, "started": datetime.now().isoformat()
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    log("Aiden online using TRIAD; recoverable command queue enabled.")
    while True:
        HEART.write_text(datetime.now().isoformat(), encoding="utf-8")
        try:
            commands = acquire_batch()
            if commands:
                batch_id = BATCH_ID.read_text(encoding="utf-8").strip()
                for index, command in enumerate(commands):
                    log("INPUT: " + command)
                    result = ask(command)
                    answer = result.get("answer", "TRIAD returned no answer")
                    trace = json.dumps(result.get("trace", {}), ensure_ascii=False)
                    if append_response_once(batch_id, index, command, answer, trace):
                        log("OUTPUT WRITTEN (TRIAD)")
                    else:
                        log("DUPLICATE RESPONSE SKIPPED (recovered batch)")
                PENDING.unlink(missing_ok=True)
                BATCH_ID.unlink(missing_ok=True)
        except Exception as exc:
            log("ERROR (pending batch retained): " + repr(exc))
        time.sleep(1)

if __name__ == "__main__":
    main()
