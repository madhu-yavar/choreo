#!/usr/bin/env bash
set -euo pipefail

ORIGIN=${1:-${SANDBOX_ORIGIN:-}}
if [[ -z "$ORIGIN" ]]; then
  echo "Usage: SANDBOX_ORIGIN=https://<your-sandbox> $0 (or pass origin as arg)" >&2
  exit 1
fi

ports=(8000 8001 8002 8003 8004 8005 8006)
names=(PII TOX JAIL POLICY BAN SECRETS FORMAT)
path_by_port() {
  case "$1" in
    8000|8001|8002|8003|8004|8005|8006) echo "/validate" ;;
    *) echo "/validate" ;;
  esac
}

for i in "${!ports[@]}"; do
  p=${ports[$i]}
  n=${names[$i]}
  path=$(path_by_port "$p")
  echo "[${n}] Preflight to http://localhost:${p}${path} from Origin: ${ORIGIN}"
  curl -i -X OPTIONS "http://localhost:${p}${path}" \
    -H "Origin: ${ORIGIN}" \
    -H "Access-Control-Request-Method: POST" \
    -H "Access-Control-Request-Headers: content-type,x-api-key" \
    --max-time 3 || true
  echo ""
done

