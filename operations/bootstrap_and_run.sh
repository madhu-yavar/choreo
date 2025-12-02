#!/usr/bin/env bash
set -euo pipefail

echo "[bootstrap] removing stale Python caches"
find /app -type d -name '__pycache__' -prune -exec rm -rf {} + 2>/dev/null || true
find /app -type f -name '*.pyc' -delete 2>/dev/null || true

echo "[bootstrap] starting enhanced PII service"
exec python -m pii_service.app