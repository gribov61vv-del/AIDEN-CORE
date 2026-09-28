#!/usr/bin/env python3
import os
import sys
import json
import time
import subprocess
from pathlib import Path
from datetime import datetime

BASE = Path(__file__).resolve().parent

CMD = BASE / "commands.txt"
RESP = BASE / "responses.txt"
LOG = BASE / "aiden_log.txt"
PID = BASE / "aiden.pid"
HEART = BASE / "aiden.heartbeat"
STATE = BASE / "aiden_state.json"

MODEL = Path(
    os.environ["SYMBIOSIS_MODEL"]
).expanduser()

LLAMA = Path(
    os.environ["SYMBIOSIS_LLAMA"]
).expanduser()

SYSTEM = """Ты — Aiden, локальное интеллектуальное ядро Symbiosis.
Ты работаешь на локальной языковой модели.
Не заявляй о выполнении действий, которых не выполнял.
Отвечай по существу.
"""


def log(message):
    text = f"[{datetime.now()}] {message}"

    with open(LOG, "a", encoding="utf-8") as f:
        f.write(text + "\n")

    print("[AIDEN]", message, flush=True)


def ask(prompt):
    full_prompt = (
        SYSTEM
        + "\n\nПользователь:\n"
        + prompt
        + "\n\nAiden:\n"
    )

    result = subprocess.run(
        [
            str(LLAMA),
            "-m",
            str(MODEL),
            "-p",
            full_prompt,
            "-n",
            "512",
            "--temp",
            "0.7",
        ],
        capture_output=True,
        text=True,
        timeout=600,
    )

    if result.returncode != 0:
        raise RuntimeError(
            result.stderr.strip()
        )

    return result.stdout.strip()


def main():
    PID.write_text(
        str(os.getpid()),
        encoding="utf-8"
    )

    STATE.write_text(
        json.dumps(
            {
                "name": "Aiden",
                "mode": "local_llama_cpp",
                "model": str(MODEL),
                "engine": str(LLAMA),
                "api": False,
                "api_key": False,
                "started": datetime.now().isoformat(),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    log("Aiden online.")
    log("ENGINE: " + str(LLAMA))
    log("MODEL: " + str(MODEL))

    while True:
        HEART.write_text(
            datetime.now().isoformat(),
            encoding="utf-8"
        )

        try:
            if CMD.exists():
                commands = [
                    line.strip()
                    for line in CMD.read_text(
                        encoding="utf-8"
                    ).splitlines()
                    if line.strip()
                ]

                if commands:
                    for command in commands:
                        log("INPUT: " + command)

                        try:
                            answer = ask(command)
                        except Exception as exc:
                            answer = (
                                "[LOCAL INFERENCE ERROR] "
                                + str(exc)
                            )

                        with open(
                            RESP,
                            "a",
                            encoding="utf-8",
                        ) as f:
                            f.write(
                                f"[{datetime.now()}]\n"
                                f"USER: {command}\n"
                                f"AIDEN: {answer}\n\n"
                            )

                        log("OUTPUT WRITTEN")

                    CMD.write_text(
                        "",
                        encoding="utf-8"
                    )

        except Exception as exc:
            log("ERROR: " + str(exc))

        time.sleep(1)


if __name__ == "__main__":
    main()
