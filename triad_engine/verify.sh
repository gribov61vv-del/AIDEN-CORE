#!/data/data/com.termux/files/usr/bin/bash
set -eu
cd "$HOME/AIDEN-CORE/triad_engine"
python -m py_compile triad_core.py triad_science.py triad_conflicts.py triad_api.py test_triad.py test_science.py test_conflicts.py test_evidence.py
python test_triad.py
python test_science.py
python test_conflicts.py
python test_evidence.py
curl -fsS --max-time 3 http://127.0.0.1:8002/ping
printf '\nTRIAD verification: ALL CHECKS PASSED\n'
