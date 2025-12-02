#!/usr/bin/env bash
set -euo pipefail

# Upload model artifacts to Azure Blob and print SAS URLs
#
# Usage (Azure AD login):
#   az login && az account set -s <SUBSCRIPTION_ID>
#   export ACCOUNT_NAME=<storage-account-name>
#   export CONTAINER=zgrid-models
#   scripts/upload_models_to_blob.sh \
#     --gliner-dir ./models/pii/gliner_small-v2.1 \
#     --jail-classifier-dir ./models/jailbreak/jailbreak-classifier \
#     --embed-dir ./models/jailbreak/all-MiniLM-L6-v2 \
#     --policy-gguf ./models/policy/llamaguard-7b-gguf/llamaguard-7b.Q4_K_M.gguf \
#     --gibberish-pkl ./models/gibberish/gibberish_model.pkl
#
# Optional:
#   export EXPIRY_DAYS=30
#   export AUTH_MODE=login   # or "key"
#   export ACCOUNT_KEY=...   # when AUTH_MODE=key

ACCOUNT_NAME=${ACCOUNT_NAME:-}
CONTAINER=${CONTAINER:-zgrid-models}
EXPIRY_DAYS=${EXPIRY_DAYS:-30}
AUTH_MODE=${AUTH_MODE:-login}

if [[ -z "$ACCOUNT_NAME" ]]; then
  echo "ERROR: ACCOUNT_NAME env is required" >&2
  exit 2
fi

function abspath() { python - "$1" << 'PY'
import os,sys
p=sys.argv[1]
print(os.path.abspath(p))
PY
}

# Inputs
GLINER_DIR=""
JAIL_CLASSIFIER_DIR=""
EMBED_DIR=""
POLICY_GGUF_FILE=""
GIBBERISH_PKL_FILE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --gliner-dir) GLINER_DIR=$(abspath "$2"); shift 2;;
    --jail-classifier-dir) JAIL_CLASSIFIER_DIR=$(abspath "$2"); shift 2;;
    --embed-dir) EMBED_DIR=$(abspath "$2"); shift 2;;
    --policy-gguf) POLICY_GGUF_FILE=$(abspath "$2"); shift 2;;
    --gibberish-pkl) GIBBERISH_PKL_FILE=$(abspath "$2"); shift 2;;
    *) echo "Unknown arg: $1" >&2; exit 2;;
  esac
done

ART_DIR=$(mktemp -d)
cleanup() { rm -rf "$ART_DIR"; }
trap cleanup EXIT

echo "[prep] Staging artifacts in $ART_DIR"

# Package directories as tar.gz where needed
GLINER_TGZ=""
if [[ -n "$GLINER_DIR" ]]; then
  base=$(basename "$GLINER_DIR")
  (cd "$(dirname "$GLINER_DIR")" && tar -czf "$ART_DIR/${base}.tar.gz" "$base")
  GLINER_TGZ="$ART_DIR/${base}.tar.gz"
fi

JAIL_TGZ=""
if [[ -n "$JAIL_CLASSIFIER_DIR" ]]; then
  base=$(basename "$JAIL_CLASSIFIER_DIR")
  (cd "$(dirname "$JAIL_CLASSIFIER_DIR")" && tar -czf "$ART_DIR/${base}.tar.gz" "$base")
  JAIL_TGZ="$ART_DIR/${base}.tar.gz"
fi

EMBED_TGZ=""
if [[ -n "$EMBED_DIR" ]]; then
  base=$(basename "$EMBED_DIR")
  (cd "$(dirname "$EMBED_DIR")" && tar -czf "$ART_DIR/${base}.tar.gz" "$base")
  EMBED_TGZ="$ART_DIR/${base}.tar.gz"
fi

POLICY_GGUF_NAME="$(basename "${POLICY_GGUF_FILE:-llamaguard-7b.Q4_K_M.gguf}")"
GIBBERISH_PKL_NAME="$(basename "${GIBBERISH_PKL_FILE:-gibberish_model.pkl}")"

echo "[blob] Ensuring container $CONTAINER exists"
if [[ "$AUTH_MODE" == "key" ]]; then
  az storage container create -n "$CONTAINER" --account-name "$ACCOUNT_NAME" --account-key "${ACCOUNT_KEY:?ACCOUNT_KEY required for key auth}" >/dev/null
else
  az storage container create -n "$CONTAINER" --account-name "$ACCOUNT_NAME" --auth-mode login >/dev/null
fi

function upload() {
  local src="$1"; local name="$2"
  if [[ -z "$src" || ! -f "$src" ]]; then return; fi
  echo "[blob] Uploading $name"
  if [[ "$AUTH_MODE" == "key" ]]; then
    az storage blob upload --account-name "$ACCOUNT_NAME" --account-key "${ACCOUNT_KEY:?}" -c "$CONTAINER" -f "$src" -n "$name" --overwrite >/dev/null
  else
    az storage blob upload --account-name "$ACCOUNT_NAME" --auth-mode login -c "$CONTAINER" -f "$src" -n "$name" --overwrite >/dev/null
  fi
}

upload "$GLINER_TGZ" "$(basename "$GLINER_TGZ")"
upload "$JAIL_TGZ" "$(basename "$JAIL_TGZ")"
upload "$EMBED_TGZ" "$(basename "$EMBED_TGZ")"
upload "$POLICY_GGUF_FILE" "$POLICY_GGUF_NAME"
upload "$GIBBERISH_PKL_FILE" "$GIBBERISH_PKL_NAME"

# Compute expiry
EXPIRY=$(python - <<PY
from datetime import datetime, timedelta
import os
days=int(os.getenv('EXPIRY_DAYS','30'))
print((datetime.utcnow()+timedelta(days=days)).strftime('%Y-%m-%dT%H:%MZ'))
PY
)

function sas() {
  local name="$1"; [[ -z "$name" ]] && return
  if [[ "$AUTH_MODE" == "key" ]]; then
    az storage blob generate-sas --account-name "$ACCOUNT_NAME" --account-key "${ACCOUNT_KEY:?}" \
      --container-name "$CONTAINER" --name "$name" --permissions r --expiry "$EXPIRY" --https-only -o tsv
  else
    az storage blob generate-sas --account-name "$ACCOUNT_NAME" --as-user \
      --container-name "$CONTAINER" --name "$name" --permissions r --expiry "$EXPIRY" --https-only -o tsv
  fi
}

BASE_URL="https://${ACCOUNT_NAME}.blob.core.windows.net/${CONTAINER}"

echo "\nSAS URLs (read-only, expire ${EXPIRY}):"
if [[ -n "$GLINER_TGZ" ]]; then
  b="$(basename "$GLINER_TGZ")"; t="$(sas "$b")"; echo "PII_GLINER_ARCHIVE_URL=${BASE_URL}/${b}?${t}"
fi
if [[ -n "$JAIL_TGZ" ]]; then
  b="$(basename "$JAIL_TGZ")"; t="$(sas "$b")"; echo "JAIL_MODEL_ARCHIVE_URL=${BASE_URL}/${b}?${t}"
fi
if [[ -n "$EMBED_TGZ" ]]; then
  b="$(basename "$EMBED_TGZ")"; t="$(sas "$b")"; echo "SIM_MODEL_ARCHIVE_URL=${BASE_URL}/${b}?${t}"
fi
if [[ -n "$POLICY_GGUF_FILE" ]]; then
  b="$POLICY_GGUF_NAME"; t="$(sas "$b")"; echo "POLICY_GGUF_URL=${BASE_URL}/${b}?${t}"
fi
if [[ -n "$GIBBERISH_PKL_FILE" ]]; then
  b="$GIBBERISH_PKL_NAME"; t="$(sas "$b")"; echo "GIBBERISH_MODEL_URL=${BASE_URL}/${b}?${t}"
fi

echo "\nDone. Copy the URLs into compose/Helm or Key Vault."

