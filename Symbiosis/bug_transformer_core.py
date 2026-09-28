#!/usr/bin/env python3
import os
import time
import json
from pathlib import Path
from datetime import datetime

BASE = Path(__file__).resolve().parent

PID = BASE / "bug_transformer.pid"
HEART = BASE / "bug_transformer.heartbeat"
LOG = BASE / "bug_transformer_log.txt"
STATE = BASE / "bug_transformer_state.json"
CMD = BASE / "transformer_commands.txt"


def log(msg):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now()}] {msg}\n")
    print("[TRANSFORMER]", msg, flush=True)


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

    state.setdefault("name", "Bug Transformer")
    state.setdefault("mode", "mirror")
    state.setdefault("flux", 0.5)

    log("Transformer online.")

    while True:
        HEART.write_text(
            datetime.now().isoformat(),
            encoding="utf-8",
        )

        try:
            if state["mode"] == "mirror":
                state["flux"] += (
                    0.5 - float(state["flux"])
                ) * 0.15

            if CMD.exists():
                commands = [
                    x.strip()
                    for x in CMD.read_text(
                        encoding="utf-8"
                    ).splitlines()
                    if x.strip()
                ]

                for command in commands:
                    if command.lower() == "invert":
                        state["flux"] = (
                            1.0 - float(state["flux"])
                        )

                    elif command.lower().startswith(
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
