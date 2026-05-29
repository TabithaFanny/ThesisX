#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WEB_DIR="$ROOT_DIR/thesisx-web"
WEB_SMOKE_PID=""

if [[ -x "$ROOT_DIR/.venv/bin/python" ]]; then
  PYTHON_BIN="$ROOT_DIR/.venv/bin/python"
elif [[ -x "$ROOT_DIR/venv312/bin/python" ]]; then
  PYTHON_BIN="$ROOT_DIR/venv312/bin/python"
else
  PYTHON_BIN="python3"
fi

cleanup() {
  if [[ -n "$WEB_SMOKE_PID" ]] && kill -0 "$WEB_SMOKE_PID" 2>/dev/null; then
    kill "$WEB_SMOKE_PID" 2>/dev/null || true
    wait "$WEB_SMOKE_PID" 2>/dev/null || true
  fi
}

trap cleanup EXIT

echo "[1/3] Python tests"
"$PYTHON_BIN" -m pytest "$ROOT_DIR/tests" -x -q --override-ini="addopts="

echo "[2/3] Web lint"
cd "$WEB_DIR"
npm run lint

echo "[3/3] Web build"
rm -rf "$WEB_DIR/.next"
npm run build

echo "[4/4] Web route smoke"
WEB_SMOKE_PORT=""
for candidate in 3100 3101 3102 3103; do
  if ! lsof -iTCP:"$candidate" -sTCP:LISTEN -n -P >/dev/null 2>&1; then
    WEB_SMOKE_PORT="$candidate"
    break
  fi
done

if [[ -z "$WEB_SMOKE_PORT" ]]; then
  echo "No free port found for web smoke test." >&2
  exit 1
fi

npm run start -- --hostname 127.0.0.1 --port "$WEB_SMOKE_PORT" >/tmp/thesisx-web-smoke.log 2>&1 &
WEB_SMOKE_PID=$!

for _ in {1..40}; do
  if curl -fsS "http://127.0.0.1:$WEB_SMOKE_PORT/" >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

curl -fsS "http://127.0.0.1:$WEB_SMOKE_PORT/" >/dev/null
curl -fsS "http://127.0.0.1:$WEB_SMOKE_PORT/projects" >/dev/null
curl -fsS "http://127.0.0.1:$WEB_SMOKE_PORT/literature" >/dev/null
curl -fsS "http://127.0.0.1:$WEB_SMOKE_PORT/quality" >/dev/null
curl -fsS "http://127.0.0.1:$WEB_SMOKE_PORT/knowledge" >/dev/null
curl -fsS "http://127.0.0.1:$WEB_SMOKE_PORT/pipeline" >/dev/null
curl -fsS "http://127.0.0.1:$WEB_SMOKE_PORT/writing" >/dev/null

echo "All checks passed."
