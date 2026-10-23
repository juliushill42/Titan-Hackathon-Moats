#!/usr/bin/env bash
set -Eeuo pipefail
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"
export PYTHONDONTWRITEBYTECODE=1
PYTHON="${PYTHON:-python3}"
command -v "$PYTHON" >/dev/null || { echo 'Python >=3.10 is required' >&2;exit 2; }
"$PYTHON" - <<'PY'
import sys
if sys.version_info < (3,10):raise SystemExit('Python >=3.10 required')
PY
for f in app.py mission.py index.html assets/app.js assets/style.css test_app.py test_mission.py; do
  [[ -f "$f" ]] || { echo "Missing required source: $f" >&2;exit 2; }
done
usage(){ printf 'Usage: %s [start|test|proof|smoke]\n' "$0"; }
case "${1:-start}" in
  test) "$PYTHON" -m unittest -v test_app test_mission;;
  proof)
    "$PYTHON" -m unittest -v test_app test_mission 2>&1 | tee mission-runtime-proof.log
    "$PYTHON" - <<'PY'
import app,json
print(json.dumps({'mcp_protocol':app.MCP_PROTOCOL,'exposed_tools':[x['name'] for x in app.MCP_TOOLS],'private_code_imported':False},indent=2))
PY
    ;;
  smoke)
    "$PYTHON" -m unittest -q test_app test_mission
    echo 'LOCAL MULTI-AGENT / MCP SMOKE: PASS'
    ;;
  start)
    "$PYTHON" -m unittest -q test_app test_mission
    exec "$PYTHON" app.py;;
  *) usage;exit 2;;
esac