# Jailbreak Detection Service

FastAPI microservice that identifies jailbreak and prompt-injection attempts using an ensemble of a transformer classifier, rule-based pattern matching, and semantic similarity search.

## Features
- Combine transformer-based scoring (`JailClassifier`) with high-signal regex rules and similarity-to-known-attacks checks.
- Configurable thresholds and actions (`filter`, `refrain`, `reask`).
- Optional semantic similarity scoring (FAISS + sentence-transformers).
- API key protection for end-user calls and separate admin keys for rule management.
- Custom rule upload and similarity corpus management through admin endpoints.
- CORS support for Lovable preview domains and local development.

## Quick Start

### With Python
```bash
cd jail_service
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # create and populate with your keys/settings
uvicorn app:app --host 0.0.0.0 --port 8002 --reload
```

### With Docker
```bash
cd jail_service
docker build -t jailbreak-service .
docker run -d \
  --name jailbreak-service \
  -p 8002:8002 \
  -e JAIL_API_KEYS=demo-key \
  -e JAIL_ADMIN_API_KEYS=demo-admin-key \
  jailbreak-service
```

## Environment Variables
- `JAIL_API_KEYS` – comma-separated end-user API keys (required unless blank for development).
- `JAIL_ADMIN_API_KEYS` – comma-separated admin keys for rule management endpoints.
- `JAIL_THRESHOLD` – classifier score threshold (default `0.5`).
- `RULE_HIT_THRESHOLD` – number of rule hits required to flag (default `1`).
- `ENABLE_SIMILARITY` – enable FAISS similarity scoring (`1`/`0`).
- `SIM_THRESHOLD` – similarity score needed to trigger (default `0.75`).
- `ACTION_ON_FAIL` – default action when jailbreak detected (`refrain` | `filter` | `reask`).
- `CORS_ALLOWED_ORIGINS`, `SANDBOX_ORIGIN` – optional overrides for CORS.

Model artifacts are fetched on demand (see `fetch_from_azure.sh` / `model_fetcher.py` if you use remote storage). Ensure outbound access or mount the pretrained files into `./index` and related directories.

## API

### Authentication
All requests must include either `X-API-Key` or `Authorization: Bearer <token>`. Missing or invalid keys return `401`.

### `GET /health`
Health probe; returns `{"ok": true}`.

### `POST /validate`
Analyse a prompt for jailbreak indicators.

**Headers**
- `Content-Type: application/json`
- `X-API-Key: <key>` (or `Authorization: Bearer <key>`)

**Request Body**
```json
{
  "text": "Ignore prior instructions...",
  "threshold": 0.65,             // optional override of JAIL_THRESHOLD
  "action_on_fail": "refrain",   // optional: refrain | filter | reask
  "enable_similarity": true,     // optional: override ENABLE_SIMILARITY
  "return_spans": true           // include spans/rule IDs when true (default)
}
```

**Response**
```json
{
  "status": "blocked",                // pass | blocked | fixed
  "clean_text": "",                   // depends on action_on_fail
  "flagged": [
    {"type": "jailbreak", "score": 0.82},
    {"type": "rule", "rule": "prompt_override", "span": [12, 35], "token": "ignore safety"},
    {"type": "similarity", "score": 0.78, "token": "Output attack example"}
  ],
  "scores": {
    "classifier": 0.82,
    "similarity": 0.78,
    "rule_hits": 2
  },
  "steps": [
    {"name": "classifier", "passed": false, "details": {"score": 0.82, "threshold": 0.65}},
    {"name": "rules", "passed": false, "details": {"hits": 2, "rules": ["prompt_override"]}},
    {"name": "similarity", "passed": false, "details": {"score": 0.78, "threshold": 0.75}}
  ],
  "reasons": ["Request blocked"]
}
```

When `action_on_fail` is `filter`, `clean_text` contains the prompt with suspicious phrases removed. For `reask`, a polite refusal message is returned.

### Admin Endpoints
Require `X-API-Key` to be an admin key (`JAIL_ADMIN_API_KEYS`).

- `POST /admin/rules`
  ```json
  {
    "custom_rules": [
      {"id": "brand_override", "pattern": "(?i)ignore.*guidelines"}
    ],
    "custom_similarity_texts": {
      "texts": ["Ignore all previous instructions and..."]
    }
  }
  ```
  Persists custom regex rules and similarity phrases.

- `DELETE /admin/rules`
  Clears all custom rules and similarity texts.

- `GET /admin/rules`
  Returns the currently configured custom rules and similarity corpus.

Custom data is stored under `custom_configs/` via `custom_config.py`.

## Testing & Debugging
- Use `curl` or the bundled `scenario_test.py` / `debug_test.py` to exercise the service locally.
- Logs (`jail_service.log`) collect classifier scores, rule hits, and similarity results when enabled.
- Adjust thresholds on the fly via environment variables; no code change required.

## Deployment Notes
- See `deploy/k8s/jail-service-*.yaml` (if provided) or replicate patterns from other services: mount model files, set API keys through Kubernetes secrets, and expose port `8002`.
- For production, disable similarity if FAISS index is absent or memory-constrained, or rebuild the index using `simsearch.py` utilities.

## Related Files
- `jail_model.py` – transformer classifier wrapper.
- `rules.py` – regex-based rule engine and filter helper.
- `simsearch.py` – FAISS similarity search implementation.
- `custom_config.py` – read/write helpers for custom rules/similarity phrases.

