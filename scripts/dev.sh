#!/usr/bin/env bash
set -euo pipefail

# Resolve repo root
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

# Load .env if present
if [ -f .env ]; then
	# shellcheck disable=SC2046
	export $(grep -v '^#' .env | xargs -I {} echo {}) || true
fi

# Defaults
EXPO_PUBLIC_BACKEND_URL="${EXPO_PUBLIC_BACKEND_URL:-http://localhost:8000}"
EXPO_PUBLIC_BACKEND_API_KEY="${EXPO_PUBLIC_BACKEND_API_KEY:-}" 

# Ensure Python venv
if [ ! -d .venv ]; then
	python3 -m venv .venv
fi
# Activate venv
# shellcheck disable=SC1091
source .venv/bin/activate

# Install backend deps if first run (or if FORCE_BACKEND_INSTALL set)
if [ ! -d .venv_installed ] || [ "${FORCE_BACKEND_INSTALL:-}" = "1" ]; then
	python3 -m pip install --upgrade pip
	python3 -m pip install -r requirements.txt
	mkdir -p .venv_installed
fi

# Start backend
BACKEND_HOST="0.0.0.0"
BACKEND_PORT="8000"
export PYTHONPATH="$REPO_ROOT"

# Kill existing uvicorn on port if running
if lsof -i TCP:"$BACKEND_PORT" -sTCP:LISTEN -t >/dev/null 2>&1; then
	kill -9 $(lsof -i TCP:"$BACKEND_PORT" -sTCP:LISTEN -t) || true
fi

python3 -m uvicorn run:app --host "$BACKEND_HOST" --port "$BACKEND_PORT" --reload &
BACKEND_PID=$!

echo "Backend started (pid: $BACKEND_PID) at http://localhost:$BACKEND_PORT"

# Ensure cleanup
cleanup() {
	if kill -0 "$BACKEND_PID" >/dev/null 2>&1; then
		kill "$BACKEND_PID" || true
		wait "$BACKEND_PID" 2>/dev/null || true
	fi
}
trap cleanup EXIT INT TERM

# Start frontend
pushd "$REPO_ROOT/tegus-frontend" >/dev/null

# Export backend env for Expo
export EXPO_PUBLIC_BACKEND_URL
export EXPO_PUBLIC_BACKEND_API_KEY

# Install frontend deps if missing
if [ ! -d node_modules ]; then
	npm install --silent
fi

# Run Expo web by default; pass MODE=native to run native bundler
MODE="${MODE:-web}"
if [ "$MODE" = "native" ]; then
	npm run start -- --non-interactive
else
	npm run web -- --non-interactive
fi

popd >/dev/null 