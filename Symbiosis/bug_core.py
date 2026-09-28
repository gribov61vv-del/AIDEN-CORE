#!/usr/bin/env python3
import os
import time
import json
from pathlib import Path
from datetime import datetime

BASE = Path(__file__).resolve().parent

PID = BASE / "bug_core.pid"
HEART = BASE / "bug_core.heartbeat"
LOG = BASE / "bug_core_log.txt"
STATE = BASE / "bug_core_state.json"
CMD = BASE / "core_commands.txt"


def log(msg):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now()}] {msg}\n")
    print("[BUG_CORE]", msg, flush=True)


def main():
    PID.write_text(str(os.getpid()), encoding="utf-8")

    if STATE.exists():
        try:
            state = json.loads(
                STATE.read_text(encoding="utf-8")
            )
        except Exception:
            state = {}
    else:
        state = {}

    state.setdefault("name", "Bug Core")
    state.setdefault("mode", "stabilize")
    state.setdefault(
        "energy",
        {"EM": 1.0, "GR": 1.0, "Q": 1.0},
    )

    log("Bug Core online.")

    while True:
        HEART.write_text(
            datetime.now().isoformat(),
            encoding="utf-8",
        )

        try:
            if state["mode"] == "stabilize":
                e = state["energy"]
                avg = (
                    e["EM"] + e["GR"] + e["Q"]
                ) / 3.0

                for key in ("EM", "GR", "Q"):
                    e[key] += (
                        avg - e[key]
                    ) * 0.2

            if CMD.exists():
                commands = [
                    x.strip()
                    for x in CMD.read_text(
                        encoding="utf-8"
                    ).splitlines()
                    if x.strip()
                ]

                for command in commands:
                    if command.lower().startswith(
                        "setmode "
                    ):
                        state["mode"] = (
                            command.split(
                                " ", 1
                            )[1].strip()
                        )

                CMD.write_text(
                    "",
                    encoding="utf-8",
                )

            STATE.write_text(
                json.dumps(
                    state,
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )

        except Exception as exc:
            log("ERROR: " + str(exc))

        time.sleep(2)


if __name__ == "__main__":
    main()
