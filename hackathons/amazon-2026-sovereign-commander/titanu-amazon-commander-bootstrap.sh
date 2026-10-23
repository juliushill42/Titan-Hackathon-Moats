#!/usr/bin/env bash
set -Eeuo pipefail
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"
export PYTHONDONTWRITEBYTECODE=1
if ! command -v python3 >/dev/null 2>&1; then echo 'python3 required (>=3.10)' >&2;exit 1;fi
python3 - <<'PY'
import sys
assert sys.version_info >= (3,10), 'Python 3.10 or newer required'
PY
case "${1:-start}" in
  test) python3 -m unittest -v test_app;;
  proof) python3 -m unittest -v test_app; echo 'STATIC PROOF: Python tests passed';;
  start) python3 -m unittest -q test_app; exec python3 app.py;;
  *) echo 'Usage: ./titanu-amazon-commander-bootstrap.sh [start|test|proof]' >&2;exit 2;;
esac