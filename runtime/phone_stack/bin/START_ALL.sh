#!/data/data/com.termux/files/usr/bin/bash
set -u
ROOT="/data/data/com.termux/files/home/AIDEN_FINAL_BUILD"
PY_WOV="$ROOT/wov/venv/bin/python"
PY="$ROOT/../venv_aiden/bin/python"
LOG="$ROOT/logs"
SYMBIOSIS_LLAMA="$HOME/llama.cpp/build/bin/llama-cli"
SYMBIOSIS_MODEL="$HOME/llama.cpp/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"
export SYMBIOSIS_LLAMA SYMBIOSIS_MODEL
mkdir -p "$LOG"

# === UNIFIED LOCAL STACK: TRIAD + AIDEN LLM ===
# Start dependencies first; leave existing Symbiosis workers untouched.
TRIAD_PING="http://127.0.0.1:8002/ping"
LLAMA_HEALTH="http://127.0.0.1:8003/health"
TRIAD_START="$HOME/AIDEN-CORE/triad_engine/start.sh"
LLAMA_SERVER="$HOME/llama.cpp/build/bin/llama-server"
LLAMA_MODEL="$HOME/llama.cpp/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"

# TRIAD: its own start script is idempotent and records its PID.
if ! curl -fsS --max-time 2 "$TRIAD_PING" >/dev/null 2>&1; then
  if [ -x "$TRIAD_START" ]; then
    bash "$TRIAD_START" >>"$LOG/triad.log" 2>&1 || echo "[BOOT] TRIAD start returned non-zero" >>"$LOG/triad.log"
  else
    echo "[BOOT] TRIAD start script missing: $TRIAD_START" >>"$LOG/triad.log"
  fi
fi

# Local inference server: health check first, then exact port-specific process check.
if ! curl -fsS --max-time 2 "$LLAMA_HEALTH" >/dev/null 2>&1; then
  if ! pgrep -f '[l]lama-server.*--port 8003' >/dev/null 2>&1; then
    if [ -x "$LLAMA_SERVER" ] && [ -f "$LLAMA_MODEL" ]; then
      nohup "$LLAMA_SERVER" -m "$LLAMA_MODEL" --host 127.0.0.1 --port 8003 -t 4 -tb 4 -c 1024 --no-ui >"$LOG/llama-server.log" 2>&1 &
      echo $! >"$LOG/llama-server.pid"
      echo "[BOOT] local Aiden LLM launch requested: PID $(cat "$LOG/llama-server.pid")" >>"$LOG/llama-server.log"
    else
      echo "[BOOT] llama-server binary or model missing; local inference not started" >>"$LOG/llama-server.log"
    fi
  fi
fi

# Give dependencies a short bounded readiness window before WOV starts.
for _ in $(seq 1 25); do
  TRIAD_OK=0
  LLAMA_OK=0
  curl -fsS --max-time 1 "$TRIAD_PING" >/dev/null 2>&1 && TRIAD_OK=1 || true
  curl -fsS --max-time 1 "$LLAMA_HEALTH" >/dev/null 2>&1 && LLAMA_OK=1 || true
  [ "$TRIAD_OK" -eq 1 ] && [ "$LLAMA_OK" -eq 1 ] && break
  sleep 1
done
echo "[BOOT] dependencies: TRIAD=$([ "$TRIAD_OK" -eq 1 ] && echo ONLINE || echo OFFLINE), AIDEN_LLM=$([ "$LLAMA_OK" -eq 1 ] && echo ONLINE || echo OFFLINE)" >>"$LOG/boot_stack.log"
# === END UNIFIED LOCAL STACK ===

echo "[AIDEN] START Thu Sep 10 12:02:12 EEST 2026"

# WOV / Flask :8000
if [ -f "$ROOT/wov/api.py" ]; then
  # Prefer the live endpoint; the running process uses "api.py" as argv,
  # so matching the source-file path with pgrep alone can launch a duplicate.
  if ! curl -fsS --max-time 2 http://127.0.0.1:8000/ping >/dev/null 2>&1; then
    if ! pgrep -f "$ROOT/wov/venv/bin/python api.py" >/dev/null 2>&1; then
      nohup "$PY_WOV" "$ROOT/wov/api.py" >"$LOG/wov.log" 2>&1 &
      echo $! >"$LOG/wov.pid"
    fi
  fi
fi

# PIKACHU / FastAPI :8001
if [ -f "$ROOT/pikachu/api.py" ]; then
  if ! pgrep -f "$ROOT/pikachu/api.py" >/dev/null 2>&1; then
    nohup env PIKACHU_PORT=8001 "$PY" "$ROOT/pikachu/api.py" >"$LOG/pikachu.log" 2>&1 &
    echo $! >"$LOG/pikachu.pid"
  fi
fi

# SYMBIOSIS / AIDEN
if [ -f "$ROOT/symbiosis/launcher.py" ]; then
  if ! pgrep -f "$ROOT/symbiosis/launcher.py" >/dev/null 2>&1; then
    nohup "$PY" "$ROOT/symbiosis/launcher.py" >"$LOG/symbiosis.log" 2>&1 &
    echo $! >"$LOG/symbiosis.pid"
  fi
fi

sleep 3

echo
echo "========== AIDEN SYSTEM =========="
echo "PYTHON: $PY"
echo
printf "WOV/FLASK   : "; curl -fsS --max-time 2 http://127.0.0.1:8000/ping >/dev/null 2>&1 && echo ONLINE || echo OFFLINE
printf "PIKACHU     : "; pgrep -f "$ROOT/pikachu/api.py" >/dev/null && echo ONLINE || echo OFFLINE
printf "SYMBIOSIS   : "; pgrep -f "$ROOT/symbiosis/launcher.py" >/dev/null && echo ONLINE || echo OFFLINE
echo
echo "WOV       http://127.0.0.1:8000"
echo "PIKACHU   http://127.0.0.1:8001"
echo "SYMBIOSIS $ROOT/symbiosis"
echo "=================================="
