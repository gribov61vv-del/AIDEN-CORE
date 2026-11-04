#!/data/data/com.termux/files/usr/bin/bash
set -eu
BASE="$HOME/AIDEN-CORE/triad_engine"
LOG="$HOME/AIDEN-CORE/logs/triad_engine.log"
PIDFILE="$HOME/AIDEN-CORE/logs/triad_engine.pid"
mkdir -p "$(dirname "$LOG")"
if curl -fsS --max-time 1 http://127.0.0.1:8002/ping >/dev/null 2>&1; then
  echo "TRIAD already online"
  exit 0
fi
nohup python "$BASE/triad_api.py" >>"$LOG" 2>&1 &
echo $! > "$PIDFILE"
echo "TRIAD started: PID $(cat "$PIDFILE")"
