#!/data/data/com.termux/files/usr/bin/bash
set -u
ROOT="$HOME/AIDEN-CORE"
WOVPY="python"
PIKAPY="$HOME/venv_aiden/bin/python"
LOG="$ROOT/logs"
mkdir -p "$LOG"

pkill -f "$ROOT/servers/wov/api.py" 2>/dev/null || true
pkill -f "$ROOT/servers/pikachu/api.py" 2>/dev/null || true
sleep 1

echo "=== AIDEN SYSTEM START ==="

nohup "$WOVPY" "$ROOT/servers/wov/api.py" >"$LOG/wov.log" 2>&1 &
echo $! > "$LOG/wov.pid"

nohup "$PIKAPY" -m uvicorn api:app --app-dir "$ROOT/servers/pikachu" \
  --host 127.0.0.1 --port 8001 >"$LOG/pikachu.log" 2>&1 &
echo $! > "$LOG/pikachu.pid"

if [ -f "$ROOT/core/Symbiosis/launcher.py" ]; then
  nohup "$PIKAPY" "$ROOT/core/Symbiosis/launcher.py" >"$LOG/symbiosis.log" 2>&1 &
  echo $! > "$LOG/symbiosis.pid"
fi

sleep 3

echo
echo "========== STATUS =========="
kill -0 "$(cat "$LOG/wov.pid")" 2>/dev/null && echo "WOV / FLASK : ONLINE" || echo "WOV / FLASK : OFFLINE"
kill -0 "$(cat "$LOG/pikachu.pid")" 2>/dev/null && echo "PIKACHU      : ONLINE" || echo "PIKACHU      : OFFLINE"
[ -f "$ROOT/core/Symbiosis/launcher.py" ] && kill -0 "$(cat "$LOG/symbiosis.pid")" 2>/dev/null && echo "SYMBIOSIS    : ONLINE" || echo "SYMBIOSIS    : OFFLINE"
find "$ROOT/eyes" -type f 2>/dev/null | grep -q . && echo "EYES         : FOUND" || echo "EYES         : NOT_FOUND"
find "$ROOT/hands" -type f 2>/dev/null | grep -q . && echo "HANDS        : FOUND" || echo "HANDS        : NOT_FOUND"
echo
echo "WOV:      http://127.0.0.1:8000"
echo "PIKACHU:  http://127.0.0.1:8001"
echo "============================"
