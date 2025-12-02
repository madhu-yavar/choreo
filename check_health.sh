#!/usr/bin/env bash
set -euo pipefail

ports=(8000 8001 8002 8003 8004 8005 8006)
names=(PII TOX JAIL POLICY BAN SECRETS FORMAT)

for i in "${!ports[@]}"; do
  p=${ports[$i]}
  n=${names[$i]}
  printf "[%s] http://localhost:%s/health -> " "$n" "$p"
  if curl -sS --max-time 2 "http://localhost:${p}/health" > /tmp/health_${p}.json 2>/dev/null; then
    cat /tmp/health_${p}.json
  else
    echo "UNREACHABLE"
  fi
done

