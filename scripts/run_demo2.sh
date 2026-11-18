#!/usr/bin/env bash
# Rebbi Demo Day v2 on macOS or Linux (Windows: scripts/autopilot2.ps1). Same Python autopilot underneath.
#   bash scripts/run_demo2.sh eglis 4-6
# Needs: .venv with `pip install -e ".[test]"`, the claude CLI on PATH, .env with CLAUDE_CODE_OAUTH_TOKEN.
# Stop with Ctrl+C; run the same command to resume.
set -u
MACHINE="${1:-eglis}"; REPEATS="${2:-4-6}"; LANES="${LANES:-3}"
cd "$(dirname "$0")/.."
PY=".venv/bin/python"; [ -x "$PY" ] || PY=python3
if command -v caffeinate >/dev/null; then   # macOS: stay awake while the autopilot runs
  exec caffeinate -dimsu "$PY" -m rebbi.demo2 autopilot --machine "$MACHINE" --repeats "$REPEATS" --lanes "$LANES"
fi
exec "$PY" -m rebbi.demo2 autopilot --machine "$MACHINE" --repeats "$REPEATS" --lanes "$LANES"
