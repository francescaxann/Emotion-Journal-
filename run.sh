#!/usr/bin/env bash
set -euo pipefail

# Simple project runner. Creates .venv if missing and runs the app.
ROOT="$(cd "$(dirname "$0")" && pwd)"
VENV="$ROOT/.venv"
PY="$VENV/bin/python"

if [ ! -d "$VENV" ]; then
  echo "Creating virtualenv at $VENV"
  python3 -m venv "$VENV"
fi

echo "Activating venv and installing requirements (if any)"
source "$VENV/bin/activate"
pip install -r "$ROOT/requirements.txt"

PORT=${PORT:-5001}
echo "Starting app on port $PORT (logs -> flask.log)"
nohup "$PY" -c "import app; app.app.run(port=$PORT, debug=False, use_reloader=False)" > "$ROOT/flask.log" 2>&1 &
echo $!
