#!/data/data/com.termux/files/usr/bin/bash
set -u

ROOT="$HOME/SYMBIOSIS"
LOG="$ROOT/logs/autostart.log"

mkdir -p "$ROOT/logs" "$ROOT/state"

echo "[$(date '+%F %T')] SYMBIOSIS boot start" >> "$LOG"

command -v termux-wake-lock >/dev/null 2>&1 && termux-wake-lock >>"$LOG" 2>&1 || true

CANDIDATES=(
 "$ROOT/start_aiden_full.sh"
 "$ROOT/start_aiden.sh"
 "$ROOT/start_assistant.sh"
 "$ROOT/start_flask.sh"
 "$ROOT/start_aizen.py"
 "$ROOT/install_and_launch_symbiosis.py"
)

FOUND=0

for f in "${CANDIDATES[@]}"; do
    if [ -f "$f" ]; then
        echo "[$(date '+%F %T')] Found: $f" >> "$LOG"
        FOUND=1

        case "$f" in
            *.sh)
                bash "$f" >>"$LOG" 2>&1 &
                ;;
            *.py)
                if command -v python >/dev/null 2>&1; then
                    python "$f" >>"$LOG" 2>&1 &
                else
                    echo "Python not installed" >>"$LOG"
                fi
                ;;
        esac

        break
    fi
done

if [ "$FOUND" -eq 0 ]; then
    echo "[$(date '+%F %T')] No AIDEN entry point found." >> "$LOG"
    echo "Heartbeat mode." >> "$LOG"
fi

date +%s > "$ROOT/state/last_boot"

echo "[$(date '+%F %T')] SYMBIOSIS boot finished" >> "$LOG"
