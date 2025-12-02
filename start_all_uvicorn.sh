#!/usr/bin/env bash
set -euo pipefail

# Usage: SANDBOX_ORIGIN=https://<your-sandbox> ./scripts/start_all_uvicorn.sh

ROOT_DIR=$(cd "$(dirname "$0")/.." && pwd)
export SANDBOX_ORIGIN=${SANDBOX_ORIGIN:-}

start() {
  local dir="$1"; local port="$2"
  echo "Starting ${dir} on :${port}..."
  (
    cd "$ROOT_DIR/$dir"
    python -m uvicorn app:app --host 0.0.0.0 --port "$port" --env-file .env --log-level info &
    echo $! > ".uvicorn_${port}.pid"
  )
}

start pii_service      8000
start tox_service      8001
start jail_service     8002
start policy_service   8003
start ban_service      8004
start secrets_service  8005
start format_service   8006

echo "Launched. PIDs are stored as .uvicorn_<port>.pid in each service dir."
echo "Tip: export SANDBOX_ORIGIN to add your sandbox to CORS."

