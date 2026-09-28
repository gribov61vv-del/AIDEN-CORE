#!/usr/bin/env python3
import os
import time
from pathlib import Path
from datetime import datetime

BASE = Path(__file__).resolve().parent

PID = BASE / "support.pid"
HEART = BASE / "support.heartbeat"
LOG = BASE / "support_log.txt"
LOCAL = BASE / "local_control.txt"
COMMANDS = BASE / "commands.txt"


def log(msg):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now()}] {msg}\n")
    print("[SUPPORT]", msg, flush=True)


def main():
    PID.write_text(str(os.getpid()), encoding="utf-8")
    log("Support Core online.")

    while True:
        HEART.write_text(
            datetime.now().isoformat(),
            encoding="utf-8",
        )

        try:
            if LOCAL.exists():
                commands = [
                    x.strip()
                    for x in LOCAL.read_text(
                        encoding="utf-8"
                    ).splitlines()
                    if x.strip()
                ]

                if commands:
                    with open(
                        COMMANDS,
                        "a",
                        encoding="utf-8",
                    ) as f:
                        for command in commands:
                            f.write(command + "\n")
                            log(
                                "FORWARD: "
                                + command
                            )

                    LOCAL.write_text(
                        "",
                        encoding="utf-8",
                    )

        except Exception as exc:
            log("ERROR: " + str(exc))

        time.sleep(1)


if __name__ == "__main__":
    main()
