#!/data/data/com.termux/files/usr/bin/bash
set -u

ROOT="/data/data/com.termux/files/home/AIDEN_SYSTEM"
PY="/data/data/com.termux/files/home/venv_aiden/bin/python"
LOG="$ROOT/logs"

mkdir -p "$LOG"

echo "=== AIDEN CENTRAL START ==="

# WOV
if [ -f "$ROOT/servers/wov/api.py" ]; then
  nohup "$PY" "$ROOT/servers/wov/api.py"     >"$LOG/wov.log" 2>&1 &
  echo $! > "$LOG/wov.pid"
fi

# PIKACHU
if [ -f "$ROOT/servers/pikachu/api.py" ] &&
   "$PY" -c "import fastapi,uvicorn" >/dev/null 2>&1; then
  nohup "$PY" -m uvicorn api:app     --app-dir "$ROOT/servers/pikachu"     --host 127.0.0.1 --port 8001     >"$LOG/pikachu.log" 2>&1 &
  echo $! > "$LOG/pikachu.pid"
fi

# SYMBIOSIS
if [ -f "$ROOT/core/Symbiosis/launcher.py" ]; then
  nohup "$PY" "$ROOT/core/Symbiosis/launcher.py"     >"$LOG/symbiosis.log" 2>&1 &
  echo $! > "$LOG/symbiosis.pid"
fi

sleep 4

echo
echo "========== CENTRAL STATUS =========="

printf "WOV       : "
curl -fsS --max-time 3 http://127.0.0.1:8000/ping >/dev/null 2>&1   && echo ONLINE || echo OFFLINE

printf "PIKACHU   : "
curl -fsS --max-time 3 http://127.0.0.1:8001/ping >/dev/null 2>&1   && echo ONLINE || echo OFFLINE

printf "SYMBIOSIS : "
if [ -f "$LOG/symbiosis.pid" ] &&
   kill -0 "$(cat "$LOG/symbiosis.pid")" 2>/dev/null; then
  echo ONLINE
else
  echo OFFLINE
fi

printf "EYES      : "
find "$ROOT/eyes" -type f 2>/dev/null | grep -q .   && echo FOUND || echo NOT_FOUND

printf "HANDS     : "
find "$ROOT/hands" -type f 2>/dev/null | grep -q .   && echo FOUND || echo NOT_FOUND

echo
echo "MANIFEST: $ROOT/SYSTEM_MANIFEST.txt"
echo "===================================="
