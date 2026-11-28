#!/usr/bin/env bash
set -euo pipefail

# Build the browser workspace before the public gateway starts.
npm run build

# Keep the engineering API private to the deployment process. The Node gateway
# forwards /api/* requests here and exposes only its own public port.
PYTHONPATH=./scripts:. python -m uvicorn bridgecad_api.main:app \
  --host 127.0.0.1 \
  --port 8000 &
PYTHON_PID=$!

cleanup() {
  kill "$PYTHON_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

npm start
