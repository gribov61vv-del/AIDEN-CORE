#!/usr/bin/env python3
import os
import sys
import time
import signal
import subprocess
from pathlib import Path

BASE = Path(__file__).resolve().parent
PYTHON = sys.executable

WORKERS = [
    "aiden_integration.py",
    "bug_core.py",
    "bug_transformer_core.py",
    "support_core.py",
]

processes = {}


def stop_all(*args):
    for process in processes.values():
        if process.poll() is None:
            try:
                process.terminate()
            except Exception:
                pass

    time.sleep(1)

    for process in processes.values():
        if process.poll() is None:
            try:
                process.kill()
            except Exception:
                pass

    raise SystemExit(0)


def start(name):
    env = os.environ.copy()

    return subprocess.Popen(
        [PYTHON, str(BASE / name)],
        cwd=str(BASE),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )


def main():
    signal.signal(signal.SIGTERM, stop_all)
    signal.signal(signal.SIGINT, stop_all)

    print("[LAUNCHER] Symbiosis online.", flush=True)

    for name in WORKERS:
        processes[name] = start(name)

    while True:
        time.sleep(2)

        for name in WORKERS:
            p = processes[name]

            if p.poll() is not None:
                processes[name] = start(name)


if __name__ == "__main__":
    main()
