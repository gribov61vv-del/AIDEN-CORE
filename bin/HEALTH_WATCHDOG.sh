#!/data/data/com.termux/files/usr/bin/bash
# AIDEN local-stack health watchdog. Starts missing services through the
# existing idempotent owner; never kills or duplicates a live process.
set -u

ROOT="$HOME/AIDEN_FINAL_BUILD"
START="$ROOT/bin/START_ALL.sh"
LOG="$ROOT/logs/health_watchdog.log"
LOCK="$ROOT/logs/health_watchdog.lock"
mkdir -p "$ROOT/logs"

exec 9>"$LOCK"
if ! flock -n 9; then
  exit 0
fi

log() { echo "[$(date '+%F %T')] $*" >> "$LOG"; }

check_service() {
  local name="$1" url="$2" pattern="$3"
  if curl -fsS --max-time 3 "$url" >/dev/null 2>&1; then
    return 0
  fi
  if pgrep -f "$pattern" >/dev/null 2>&1; then
    log "$name endpoint unhealthy but process exists; no duplicate or forced kill"
    return 1
  fi
  log "$name process missing; recovery requested"
  return 2
}

run_check() {
  local recover=0 rc
  check_service WOV "http://127.0.0.1:8000/ping" '[w]ov/api.py' || { rc=$?; [ "$rc" -eq 2 ] && recover=1; }
  check_service PIKACHU "http://127.0.0.1:8001/ping" '[p]ikachu/api.py' || { rc=$?; [ "$rc" -eq 2 ] && recover=1; }
  check_service TRIAD "http://127.0.0.1:8002/ping" '[t]riad_api.py' || { rc=$?; [ "$rc" -eq 2 ] && recover=1; }
  check_service LLAMA "http://127.0.0.1:8003/health" '[l]lama-server.*--port 8003' || { rc=$?; [ "$rc" -eq 2 ] && recover=1; }
  if ! pgrep -f '[s]ymbiosis/launcher.py' >/dev/null 2>&1; then
    log "SYMBIOSIS launcher missing; recovery requested"
    recover=1
  fi

  if [ "$recover" -eq 1 ]; then
    log "Calling unified START_ALL.sh for missing process recovery"
    bash "$START" >> "$LOG" 2>&1 || log "START_ALL.sh returned non-zero"
    sleep 8
    for item in "WOV|http://127.0.0.1:8000/ping" "PIKACHU|http://127.0.0.1:8001/ping" "TRIAD|http://127.0.0.1:8002/ping" "LLAMA|http://127.0.0.1:8003/health"; do
      name="${item%%|*}"
      url="${item#*|}"
      if curl -fsS --max-time 2 "$url" >/dev/null 2>&1; then
        log "$name recovered/online"
      else
        log "$name still offline after recovery attempt"
      fi
    done
  fi
}

if [ "${1:-}" = "--check-once" ]; then
  run_check
  exit 0
fi

log "watchdog started"
while true; do
  run_check
  sleep 60
done
