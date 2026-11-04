# Phone runtime: AIDEN / WOV / TRIAD

This directory documents the Termux runtime layout used on the Motorola Edge 40 Neo.

## Service map

- WOV gateway: `127.0.0.1:8000`
- Pikachu API: `127.0.0.1:8001`
- TRIAD API: `127.0.0.1:8002`
- llama.cpp server: `127.0.0.1:8003`
- Symbiosis launcher: four worker processes

## Runtime source of truth

The live phone installation currently resides under `$HOME/AIDEN_FINAL_BUILD` and `$HOME/AIDEN-CORE`. This repository copy is a versioned source snapshot; it is not an installer and does not contain the local SQLite memory or the GGUF model.

## Start and health-check

```bash
bash "$HOME/AIDEN_FINAL_BUILD/bin/START_ALL.sh"
curl -fsS http://127.0.0.1:8000/ping
curl -fsS http://127.0.0.1:8001/ping
curl -fsS http://127.0.0.1:8002/ping
curl -fsS http://127.0.0.1:8003/health
bash "$HOME/AIDEN-CORE/triad_engine/verify.sh"
```

## Network binding

WOV and Pikachu default to loopback only. To deliberately expose them on a trusted LAN, set `AIDEN_BIND_HOST=0.0.0.0` before launching. Do not expose these development APIs to untrusted networks without authentication and firewall rules.

## Boot

- `termux-boot/00_symbiosis` is the primary entrypoint.
- `bin/symbiosis_autostart.sh` invokes the unified `START_ALL.sh`.
- `termux-boot/10_triad_engine` is only a delayed recovery guard; it waits 30 seconds before checking TRIAD to avoid racing the primary launcher.

## Excluded runtime data

No `.db`, `.sqlite*`, `.gguf`, virtual environment, log, PID, cache, backup, token, or credential files belong in this source snapshot.
