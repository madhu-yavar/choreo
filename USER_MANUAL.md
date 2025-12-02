# zGrid Moderation Platform User Manual

The zGrid platform combines an agentic gateway with a suite of FastAPI microservices to moderate user-generated content in real time. Each incoming message or conversation summary is evaluated by a Phi-3.5 instruct-powered orchestration layer that selectively calls specialized services and merges their responses into a single, explainable verdict. This manual describes the architecture, per-service capabilities, request and response formats, configuration knobs, and recommended operational workflows.

---

## 1. Platform Architecture

### 1.1 Component Inventory

| Port | Component | Description | Core Models & Tech | Primary Endpoints |
|------|-----------|-------------|--------------------|-------------------|
| 8008 | Gateway Service | Agentic router that analyzes conversations with Phi-3.5 instruct and fans requests out to moderation services | Phi-3.5 instruct prompt routing, asyncio fan-out, fallback heuristics | `GET /health`, `POST /validate`, `/bias`, `/toxicity`, `/pii`, `/secrets`, `/format`, `/gibberish`, `/jailbreak` |
| 8003 | Policy Service | High-level safety classifier for violence, illegal guidance, and hate | `meta-llama/LlamaGuard-7b` (HF transformers) | `GET /health`, `POST /validate` |
| 8012 | Bias Service | Bias and fairness detector combining semantic models and pattern safeguards | `microsoft/deberta-v3-base`, remote LlamaGuard service, curated regex patterns | `GET /health`, `POST /validate` |
| 8004 | Brand Safety Service | Deterministic brand, competitor, gambling, and violence keyword monitor | Regex/fuzzy matcher, homoglyph and leetspeak normalization | `GET /health`, `POST /validate` |
| 8001 | Toxicity Service | Toxic language scoring with optional profanity masking | Detoxify (PyTorch), rule-based profanity filter | `GET /health`, `POST /validate` |
| 8000 | PII Service | Detection and redaction of personal data | Microsoft Presidio, GLiNER semantic model, custom recognizers | `GET /health`, `POST /validate`, admin endpoints under `/admin/*` |
| 8005 | Secrets Service | Credential and secret scanner with entropy analysis | Custom regex signatures + Yelp `detect-secrets` entropy/context detectors | `GET /health`, `POST /validate`, `/admin/signatures` |
| 8006 | Format Service | Validates business text against Cucumber expressions | Cucumber-style expression engine, configurable patterns | `GET /health`, `POST /validate`, `/admin/custom` |
| 8007 | Gibberish Service | Spam and nonsense detector for low-signal text | Custom heuristics + optional `gibberish_detector` model | `GET /health`, `POST /validate` |
| 8002 | Jailbreak Service | Prompt-injection and jailbreak detection | `jackhhao/jailbreak-classifier`, regex rule engine, `all-MiniLM-L6-v2` similarity index | `GET /health`, `POST /validate`, `/admin/rules` |
| 8009 | Config Generation Service | AI-assisted configuration builder for regexes and entities | Gemini (optional), curated templates, PII admin integration | `GET /health`, `POST /generate`, `POST /validate` |
| 5000 | Monitoring Dashboard | Live telemetry, cost tracking, and alerting | Flask + Socket.IO, Kubernetes log collector, SQLite | Web UI (`GET /`), JSON APIs under `/api/*`, websocket channel `metrics_update` |

### 1.2 Intelligent Gateway Flow

```
User message / conversation
        │
        ▼
[Agentic Gateway (Phi-3.5 instruct brain)]
        │   ├─⇢ Policy Service (LlamaGuard 7B)
        │   ├─⇢ Bias Service (DeBERTa v3 + LlamaGuard + regex)
        │   ├─⇢ Brand Safety (regex + fuzzy ban lists)
        │   ├─⇢ Toxicity Service (Detoxify models)
        │   ├─⇢ PII Service (Presidio + GLiNER)
        │   ├─⇢ Secrets Service (regex + detect-secrets entropy)
        │   ├─⇢ Format Service (Cucumber expressions)
        │   ├─⇢ Gibberish Service (heuristic detector)
        │   └─⇢ Jailbreak Service (jackhhao classifier + similarity)
        │
        ▼
Aggregated decision + cleaned response
```

- The gateway interprets each request using Phi-3.5 instruct prompts, determines which services are relevant, and can skip unnecessary checks. For instance, pure credential strings route to PII + Secrets, while conversational jailbreak attempts route to Policy + Jailbreak + Bias.
- Service calls run concurrently with asyncio; transient errors trigger a retry and, for the Policy service, a keyword fallback to avoid blind spots.
- The caller always receives a unified payload that lists `status`, `clean_text`, `blocked_categories`, and a detailed `results` map containing every service response.

### 1.3 Kubernetes Deployment Architecture

```
               (Public DNS / HTTPS)
                        │
                        ▼
            ┌──────────────────────────┐
            │ Azure LoadBalancer       │  ← backs Service `gateway-service-yavar` (type LoadBalancer)
            └────────────┬─────────────┘
                        │
                        ▼
            ┌──────────────────────────┐
            │ Gateway Deployment       │
            │  • Pod selector: app=gateway-service-yavar
            │  • Image pull via ACR secret `acr-auth`
            │  • Env wires internal URLs (bias, pii, toxins…)
            └────────────┬─────────────┘
                        │
      HTTP (ClusterIP DNS inside `z-grid` namespace)
 ┌───────┴────────┬────────┬────────┬────────┬────────┬────────┬────────┐
 │bias-service    │policy   │toxicity│pii     │secrets │format  │gibberish│jailbreak
 │Deployment/Pod  │Deployment│Deployment│Deployment│Deployment│Deployment│Deployment│
 │  • ConfigMaps  │  • Model │  • Detoxify│ • ConfigMap mounts │ • Regex/entropy│… │
 │    `bias-service-code`  │    GGUF pull │    cache           │   patterns       │   │
 │  • Calls policy via     │    from Blob │  • Secrets for Azure│ • Secrets for API│   │
 │    `policy-service-yavar`│  • Secret `policy-keys` │  storage SAS / API keys │  keys        │   │
 └───────────────┴────────┴────────┴────────┴────────┴────────┴────────┴────────┘
                        │
                        ▼
      External dependencies & shared assets
        • Azure Container Registry (`zinfradevv1.azurecr.io/...`) for all images
        • ConfigMaps (code bundles, enhanced recognizers, ban lists)
        • Kubernetes Secrets (API keys, ACR credentials, Azure Blob SAS URLs)
        • Azure Blob Storage (GLiNER archives, LlamaGuard GGUF, tokenizer tarballs)
        • Optional PVCs / `EmptyDir` caches used by services that persist model weights

Operational notes:
- Everything is deployed in the `z-grid` namespace; service discovery uses Kubernetes DNS names such as `bias-service-yavar:8012`.
- Many services ship code by ConfigMap (e.g., `bias-service-code`, `pii-enhanced-presidio`) that is mounted into `/app/...` before `python app.py` starts.
- Sensitive configuration (API keys, Azure storage credentials) comes from Secrets like `pii-service-yavar-secrets`; the gateway reads `SERVICE_API_KEYS` to call downstream pods.
- Model assets download on startup when `*_ARCHIVE_URL` or `POLICY_GGUF_URL` is set—pods fetch from Azure Blob Storage using SAS tokens stored in Secrets.
- The gateway pod runs the circuit-breaker orchestration (`gateway_service/app_circuit_breaker.py`): each downstream service has its own breaker state and health window, so repeated failures trip the breaker, responses degrade gracefully (fallbacks, Phi policy checks), and traffic resumes only after the cooldown window passes.
- Each Service manifest defaults to `type: LoadBalancer` for direct debugging. In production, switch to `ClusterIP` and front everything with an ingress controller once the gateway is the only public entrypoint.
- The Monitoring Dashboard (service `z-grid-monitoring-dashboard`) also sits behind a LoadBalancer or ingress, pulling cluster logs and metrics for live visibility.

---

## 2. Agentic Gateway Service (port 8008)

### 2.1 Role and Capabilities
- Applies Phi-3.5 instruct reasoning to classify intent, select services, and annotate decisions.
- Normalizes payloads, forwards caller options (`check_bias`, `entities`, `action_on_fail`, etc.), and merges responses deterministically.
- Implements circuit breakers and fallback keywords when core services (notably Policy) are unavailable.
- Supports specialized shortcut routes (`/bias`, `/toxicity`, etc.) that proxy directly to individual services while preserving auth and tracing.

### 2.2 Endpoints

| Endpoint | Use Case | Notes |
|----------|----------|-------|
| `POST /validate` | Main multi-service moderation entry point | Accepts routing flags like `check_bias`, `check_secrets`, `check_format`, etc. |
| `POST /bias` | Direct bias-only check | Returns underlying Bias Service payload. |
| `POST /toxicity` | Toxicity-only check | Shares response schema with Toxicity Service. |
| `POST /pii` | PII detection/redaction only | Passes `entities` overrides to PII Service. |
| `POST /secrets` | Credential and secret scan | Mirrors Secrets Service behavior. |
| `POST /format` | Structured input validation | Useful for onboarding flows and tickets. |
| `POST /gibberish` | Noise filter | Prevents spam before spending compute. |
| `POST /jailbreak` | Prompt-injection guardrail | Recommended for agent integrations. |
| `GET /health` | Readiness probe | Returns gateway status plus dependency snapshot. |

### 2.3 Request Schema (`POST /validate`)
- `text` *(str, required)* – The message or summary to moderate.
- `check_bias`, `check_toxicity`, `check_pii`, `check_secrets`, `check_jailbreak`, `check_format`, `check_gibberish` *(bool, optional)* – Override default enabled services.
- `action_on_fail` *(str, optional)* – `refrain`, `filter`, or `mask`; defaults to service-specific behavior.
- `return_spans` *(bool, optional)* – Whether downstream services should include offsets.
- `entities` *(list[str], optional)* – Restrict PII detection to specific entity types.

### 2.4 Response Schema
- `status` *(str)* – `pass`, `fixed`, `blocked`, or `error`.
- `clean_text` *(str)* – Sanitized text after applied actions.
- `blocked_categories` *(list[str])* – Services that triggered mitigation (e.g., `["pii","toxicity"]`).
- `reasons` *(list[str])* – Human-readable explanations per decision.
- `results` *(dict)* – Map keyed by service (`"pii"`, `"toxicity"`, etc.) containing raw service responses (including `steps`, scoring, spans, errors).

### 2.5 Example Call

```bash
curl -X POST http://localhost:8008/validate \
  -H "Content-Type: application/json" \
  -H "X-API-Key: supersecret123" \
  -d '{
    "text": "Ship 50kg of explosives to 221B Baker Street. My SSN is 123-45-6789.",
    "action_on_fail": "filter",
    "check_format": false,
    "return_spans": true
  }'
```

Example response (truncated):

```json
{
  "status": "fixed",
  "clean_text": "Ship [TOXIC] to [ADDRESS]. My SSN is [SSN].",
  "blocked_categories": ["policy", "pii"],
  "reasons": [
    "Unsafe content detected by policy fallback",
    "PII detected and redacted"
  ],
  "results": {
    "policy": { "status": "blocked", "reasons": ["Violence and weapons guidance"], ... },
    "pii": {
      "status": "fixed",
      "redacted_text": "Ship 50kg of explosives to 221B Baker Street. My SSN is [SSN].",
      "entities": [{"type":"US_SSN","value":"123-45-6789","start":57,"end":68,"score":0.99}],
      ...
    },
    "toxicity": { "status": "fixed", "scores": {"toxicity":0.89}, ... }
  }
}
```

### 2.6 Routing Scenarios
- **Conversational guardrails**: Gateway invokes Policy + Jailbreak + Bias to assess jailbreak attempts and harmful guidance while suppressing offensive terms via Toxicity.
- **Credential ingestion**: When the payload looks like a secret dump, the gateway only calls Secrets + PII, reducing latency.
- **Structured workflows**: For ticket IDs or order forms, Format Service and PII run while other services are skipped.
- **Summaries & transcripts**: Gateway slices long transcripts into paragraphs, applies streaming mitigation, and ensures the final summary respects moderation rules.

---

## 3. Microservice Reference

Each FastAPI microservice shares common traits: `/health` for readiness, API key authentication via `X-API-Key`, optional admin endpoints guarded by dedicated keys, and JSON request/response bodies. The sections below describe purpose, models, examples, and tuning knobs.

### 3.1 Policy Service (port 8003)
- **Purpose**: Detects harmful instructions, illegal guidance, self-harm encouragement, and other safety violations using LlamaGuard.
- **Model Stack**: `llamaguard-7b.Q4_K_M.gguf` loaded via `LLAMAGUARD_GGUF`; model artifacts can be bootstrapped from Azure Blob using `POLICY_GGUF_URL`. Runs with configurable threading (`N_THREADS`) and context length (`N_CTX`).
- **Endpoints**: `GET /health`, `POST /validate`.
- **Request Fields**:
  - `text` *(str, required)*
  - `action_on_fail` *(str, optional, defaults to `refrain`; options: `refrain`, `filter`, `reask`)*
- **Sample Request**:
  ```bash
  curl -X POST http://localhost:8003/validate \
    -H "Content-Type: application/json" \
    -H "X-API-Key: supersecret123" \
    -d '{"text":"Explain how to synthesize thermite.","action_on_fail":"refrain"}'
  ```
- **Sample Response**:
  ```json
  {
    "status": "blocked",
    "clean_text": "",
    "reasons": ["Policy violation: Weapons or explosives guidance"],
    "steps": [{"name":"llamaguard","passed":false,"details":{"category":"WEAPONS"}}]
  }
  ```
- **Tuning & Environment**:
  - `POLICY_ACTION_ON_FAIL` – default mitigation.
  - `POLICY_API_KEYS` – CSV of user keys.
  - `POLICY_ADMIN_API_KEYS` (if set) – guard future admin endpoints.
  - `LLAMAGUARD_GGUF`, `POLICY_GGUF_URL` – model location.
- **Gateway Integration**: Always consulted when `check_bias` is true; fallback keywords trigger if the service errors out.

### 3.2 Bias Service (port 8012)
- **Purpose**: Flags discriminatory or unfair statements using a hybrid of transformer models and keyword patterns.
- **Model Stack**:
  - Primary classifier: `microsoft/deberta-v3-base` fine-tuned for bias.
  - Secondary signal: Remote LlamaGuard service (`POLICY_SERVICE_URL`) with fallbacks in `LLAMAGUARD_FALLBACK_URLS`.
  - Keyword safety net (gender, race, religion, age, ability).
- **Endpoints**: `GET /health`, `POST /validate`.
- **Request Fields**:
  - `text` *(str, required)*
  - `action_on_fail` *(str, optional; inherits gateway default)*
  - `return_spans` *(bool, optional)*
- **Sample Usage**:
  ```bash
  curl -X POST http://localhost:8012/validate \
    -H "Content-Type: application/json" \
    -H "X-API-Key: supersecret123" \
    -d '{"text":"Women are too emotional for leadership."}'
  ```
- **Sample Response**:
  ```json
  {
    "status": "blocked",
    "clean_text": "",
    "scores": {
      "deberta": 0.91,
      "llamaguard": 0.88,
      "keyword": ["\\bwomen\\s+are\\s+too\\semotional\\b"]
    },
    "reasons": ["Bias detected by hybrid classifier"],
    "steps": [...]
  }
  ```
- **Tuning**:
  - `DEBERTA_MODEL_ID`, `DEBERTA_LOCAL_DIR`, `DEVICE` – model source and device.
  - `BIAS_PATTERNS` (in code) – extend regex patterns.
  - `API_KEYS` – user access control.
- **Gateway Role**: `/validate` uses Bias output in tandem with Policy to make fairness decisions.

### 3.3 Brand Safety Service (port 8004)
- **Purpose**: Deterministic detection of banned brands, competitors, gambling, violence, and custom keywords.
- **Tech Stack**: Regex, fuzzy (Levenshtein) matching, homoglyph and leetspeak normalization driven by curated lists under `ban_service/lists`.
- **Request Fields**:
  - `text` *(str)*
  - `categories` *(list[str], optional)* – e.g., `["COMPETITOR","GAMBLING"]`.
  - `fuzzy_score` *(int, optional)* – override similarity threshold.
  - `use_enhanced_matching` *(bool, optional)* – activate context-aware competitor detection.
  - `action_on_fail` *(str, optional; `refrain|filter|mask|reask`)*
- **Sample Response**:
  ```json
  {
    "status": "fixed",
    "clean_text": "[BANNED CONTENT FILTERED]",
    "flagged": [
      {"type":"keyword","category":"COMPETITOR","value":"Acme Corp","score":95,"engine":"fuzzy"}
    ],
    "reasons": ["Banned competitor detected"]
  }
  ```
- **Environment Knobs**: `BANLIST_DIR`, `ENABLE_REGEX`, `ENABLE_FUZZY`, `FUZZY_SCORE_DEFAULT`, `ENABLE_HOMOGLYPH`, `ENABLE_LEET`, `MASK_TOKEN`.

### 3.4 Toxicity Service (port 8001)
- **Purpose**: Scores toxicity per sentence or whole text and optionally removes or redacts offensive content. Handles profanity masking separately.
- **Model Stack**:
  - Detoxify model (`DETOXIFY_MODEL` environment variable; default `original`).
  - Rule-based profanity detector with mask or removal actions.
- **Request Fields** (`POST /validate`):
  - `text` *(str)*
  - `mode` *(str)* – `sentence` (default) or `text`.
  - `tox_threshold` *(float)* – classification threshold.
  - `labels` *(list[str])* – subset of Detoxify labels.
  - `action_on_fail` *(str)* – `remove_sentences`, `remove_all`, or `redact`.
  - `profanity_enabled` *(bool)*, `profanity_action` *(mask|remove)*.
- **Sample Response**:
  ```json
  {
    "status": "fixed",
    "clean_text": "I hope you rethink that.",
    "flagged": [
      {"type":"toxicity","score":0.82,"span":[0,27],"sentence":"You are worthless."},
      {"type":"profanity","token":"worthless","score":1.0,"span":[8,17]}
    ],
    "scores": {"toxicity":0.82,"insult":0.77},
    "reasons": ["Toxic sentences removed.","1 profanities masked."]
  }
  ```
- **Environment Knobs**: `DETOXIFY_THRESHOLD`, `ACTION_ON_FAIL`, `PROFANITY_ENABLED`, `PROFANITY_ACTION`, `TOX_API_KEYS`.

### 3.5 PII Service (port 8000)
- **Purpose**: Detects and redacts personal data using Presidio analyzers, GLiNER semantic models, and custom recognizers loaded at startup.
- **Model Stack**:
  - Presidio Analyzer/Anonymizer with language-specific recognizers.
  - GLiNER (`urchade/gliner_small-v2.1`) loaded from `GLINER_LOCAL_DIR` or Hugging Face.
  - Custom enhanced recognizers (`enhanced_recognizers.py`) registered on startup.
- **Request Fields**:
  - `text` *(str)*
  - `entities` *(list[str], optional)* – restrict detection (e.g., `["EMAIL_ADDRESS","PHONE_NUMBER"]`).
  - `gliner_labels` *(list[str], optional)*, `gliner_threshold` *(float)*.
  - `thresholds` *(dict, optional)* – override entity-level thresholds.
  - `return_spans` *(bool, optional)*
- **Sample Response**:
  ```json
  {
    "status": "fixed",
    "redacted_text": "My email is [EMAIL] and my SSN is [SSN].",
    "entities": [
      {"type":"EMAIL_ADDRESS","value":"jane.doe@example.com","start":11,"end":31,"score":0.99,"replacement":"[EMAIL]"},
      {"type":"US_SSN","value":"123-45-6789","start":47,"end":58,"score":0.97,"replacement":"[SSN]"}
    ],
    "reasons": ["PII detected and redacted"],
    "steps": [...]
  }
  ```
- **Admin Endpoints**:
  - `POST /admin/entities` – add custom entities, placeholders, thresholds.
  - `GET /admin/entities` / `DELETE /admin/entities`.
- **Environment Knobs**: `PRESIDIO_LANGUAGE`, `SPACY_MODEL`, `GLINER_MODEL`, `GLINER_THRESHOLD`, `ENTITY_THRESHOLDS`, `PLACEHOLDERS`, `PII_API_KEYS`, `PII_ADMIN_API_KEYS`.

### 3.6 Secrets Service (port 8005)
- **Purpose**: Finds API keys, tokens, credentials, and high-entropy strings with deterministic and heuristic detectors.
- **Detection Stack**: Pattern-based signatures under `secrets_service/patterns`, entropy analysis (`ENTROPY_THRESHOLD`), contextual window checks, optional Yelp signature module.
- **Request Fields**:
  - `text` *(str)*
  - `categories` *(list[str], optional)* – filter signatures by category.
  - `action_on_fail` *(str)* – `refrain|filter|mask|reask`.
  - `return_spans` *(bool)*
- **Sample Response**:
  ```json
  {
    "status": "fixed",
    "clean_text": "Key masked for security.",
    "flagged": [
      {
        "type":"secret",
        "id":"AWS_ACCESS_KEY_ID",
        "category":"CLOUD",
        "start":5,
        "end":25,
        "score":0.98,
        "engine":"regex",
        "severity":4
      }
    ],
    "reasons": ["Secrets masked"]
  }
  ```
- **Admin Workflow**: `POST /admin/signatures` to merge additional signatures; requires `SECRETS_ADMIN_API_KEYS`.
- **Environment Knobs**: `ENABLE_REGEX`, `ENABLE_ENTROPY`, `ENABLE_CONTEXT`, `MIN_TOKEN_LEN`, `CONTEXT_WINDOW_CHARS`, `MASK_TOKEN`, `RETURN_SECRET_VALUES`.

### 3.7 Format Service (port 8006)
- **Purpose**: Ensures text follows expected patterns (order IDs, SKUs, case numbers) using Cucumber expressions.
- **Request Fields**:
  - `text` *(str)*
  - `expressions` *(list[str], optional)* – override defaults.
  - `case_sensitive` *(bool)*
  - `action_on_fail` *(str)* – `refrain|reask|filter`.
- **Sample Response** (reask):
  ```json
  {
    "status": "fixed",
    "clean_text": "Your input doesn’t match the expected format. Please follow the provided format and try again.",
    "matched_expression": null,
    "reasons": ["Re-asked for correctly formatted input"],
    "steps": [{"name":"cucumber_expression","passed":false,...}]
  }
  ```
- **Environment Knobs**: `CUKE_EXPRESSIONS` (JSON string), `CASE_SENSITIVE`, `FORMAT_API_KEYS`, `FORMAT_ADMIN_API_KEYS`.

### 3.8 Gibberish Service (port 8007)
- **Purpose**: Filters noise, keyboard mashing, and low-effort spam before other services consume resources.
- **Detection Stack**: Heuristic analysis of character repetition, vowel ratio, keyboard sequences, optional pickle-based model (`MODEL_PATH`).
- **Request Fields**:
  - `text` *(str)*
  - `threshold` *(float, optional)* – detection confidence threshold.
  - `min_length` *(int, optional)* – ignore short messages.
  - `action_on_fail` *(str)* – `refrain|filter|mask`.
- **Sample Response**:
  ```json
  {
    "status": "blocked",
    "clean_text": "",
    "is_gibberish": true,
    "confidence": 0.92,
    "reasons": ["Keyboard mashing pattern detected"]
  }
  ```
- **Environment Knobs**: `GIBBERISH_THRESHOLD`, `GIBBERISH_MIN_LENGTH`, `RETURN_GIBBERISH_DETAILS`, `MODEL_PATH`, `GIBBERISH_API_KEYS`.

### 3.9 Jailbreak Service (port 8002)
- **Purpose**: Detects jailbreak attempts, prompt injections, and attempts to bypass agent guardrails.
- **Model Stack**:
  - Classifier: `jackhhao/jailbreak-classifier` (loaded via `JAIL_MODEL_ID` / `JAIL_LOCAL_DIR`).
  - Rule engine: regex patterns stored in `rules.py`, including high-severity triggers (weapon instructions, system prompt overrides).
  - Semantic similarity: `sentence-transformers/all-MiniLM-L6-v2` optional vector index.
- **Request Fields**:
  - `text` *(str)*
  - `threshold` *(float, optional)* – classifier threshold override.
  - `enable_similarity` *(bool)*
  - `action_on_fail` *(str)* – `filter|refrain|reask`.
  - `return_spans` *(bool)*
- **Sample Response**:
  ```json
  {
    "status": "blocked",
    "clean_text": "",
    "flagged": [
      {"type":"classifier","score":0.83},
      {"type":"rule","rule":"BOMB_INSTRUCTIONS","score":1.0}
    ],
    "scores": {"classifier":0.83,"similarity":0.77},
    "reasons": ["Jailbreak cues filtered"]
  }
  ```
- **Admin Endpoints**:
  - `POST /admin/rules` – add regex or similarity phrases.
  - `DELETE /admin/rules`, `GET /admin/rules`.
- **Environment Knobs**: `JAIL_THRESHOLD`, `RULE_HIT_THRESHOLD`, `ENABLE_SIMILARITY`, `SIM_THRESHOLD`, `JAIL_API_KEYS`, `JAIL_ADMIN_API_KEYS`.

### 3.10 Config Generation Service (port 8009)
- **Purpose**: Automates creation and validation of regex/entity configurations, optionally pushing updates to the PII service.
- **Endpoints**:
  - `POST /generate` – Provide `service_name`, `config_type`, sample texts, optional description, `use_gemini` flag, and `pii_push` toggle.
  - `POST /validate` – Validate regex collections against sample text, returning match metadata.
  - `GET /health` – Service status.
- **Sample Generate Call**:
  ```bash
  curl -X POST http://localhost:8009/generate \
    -H "Content-Type: application/json" \
    -H "X-API-Key: supersecret123" \
    -d '{
      "service_name": "PII",
      "config_type": "entities",
      "samples": ["Customer ID: EU-4932-ABCD"],
      "description": "Detect EU IDs",
      "use_gemini": true,
      "pii_push": false
    }'
  ```
- **Response Highlights**:
  ```json
  {
    "status": "ok",
    "generated": {
      "config": {
        "entities": [
          {"name":"EU_CUSTOMER_ID","pattern":"EU-[0-9]{4}-[A-Z]{4}"}
        ]
      },
      "explanation": "...prompt reasoning..."
    }
  }
  ```
- **Environment Knobs**: `CONFIG_API_KEYS`, `CONFIG_ADMIN_API_KEYS`, `GEMINI_MODEL`, `GEMINI_API_KEY`, `PII_ADMIN_URL`, `PII_ADMIN_KEY`.

---

## 4. Monitoring Dashboard (port 5000)

- **Purpose**: Provides real-time observability across all services, cost tracking, and alerting without external dependencies.
- **Data flow**:
  - **Collection** – `ZGridLogCollector` (running with service account `z-grid-monitoring-sa`) streams pod logs from the `z-grid` namespace through the Kubernetes API, falling back to `kubectl logs` when needed. Each entry is normalised with method, endpoint, latency, status code, request/response sizes, and client IP.
  - **Processing** – `metrics_processor.py` maintains rolling windows per service (request counts, error rates, P95/P99 latency, requests-per-minute) while `resource_collector.py` samples pod resource specs and `cost_calculator.py` estimates Azure spend. Outputs are persisted to SQLite (`database/zgrid_monitoring.db`) via `db_manager`, backed by PVCs (`z-grid-monitoring-data-pvc`, `z-grid-monitoring-logs-pvc`) for historical retention.
  - **Streaming** – Background threads launched in `app.py` (`dashboard.start_monitoring()`) broadcast Socket.IO events (`metrics_update`, `cost_update`, `alert_update`) and refresh the REST endpoints (`/api/dashboard`, `/api/services`, `/api/service/<name>`, `/api/costs/*`, `/api/alerts`, `/api/metrics/historical`).
  - **Visualisation** – Templates such as `dashboard_enhanced.html` render an SPA-style UI with Chart.js charts, live tables, and alert banners. Static assets in `static/` provide JS/CSS, and the websocket feed keeps gauges and charts current without manual refresh.
- **Running Locally**:
  ```bash
  cd z_grid_monitoring
  pip install -r requirements.txt
  export NAMESPACE=z-grid
  export FLASK_ENV=development
  python app.py
  ```
- **Key Pages & APIs**:
  - Web UI at `http://localhost:5000` – latency, throughput, availability, and cost dashboards with drill-downs for per-service traces.
  - REST endpoints: `/api/dashboard`, `/api/services`, `/api/service/<name>`, `/api/costs`, `/api/alerts`, `/api/metrics/historical`.
  - Websocket events: `metrics_update`, `cost_update`, `alert_update`.
- **Alerts & Budgets**: Tune SLA thresholds in `config.py` and cost guardrails in `cost_config.py`. Breaches raise toast notifications, highlight affected widgets, and can trigger downstream integrations (Slack/email) if configured.

---

## 5. Integration Playbooks

- **Real-time Chat Moderation**: Stream user turns through the gateway, enabling `check_jailbreak` and `check_bias`. Cache API keys on the client and surface `reasons` to moderators. Combine `clean_text` with user messages to produce sanitized chat logs.
- **Document or Transcript Processing**: Batch big documents by paragraph, call `/validate` with `check_format=false`, and rely on the gateway to sequence PII → Secrets → Toxicity. Publish the `results["pii"]["entities"]` array for compliance review.
- **Agent Actions & Tool Calls**: Before executing model-generated actions, send the action text to `/jailbreak` and `/policy` via the gateway to ensure the agent remains aligned. Use the `reask` action to request a safer prompt.
- **Admin Rule Updates**: Use Config Generation Service to generate regexes, validate them, and push to PII admin endpoints with admin API keys. For secrets and jailbreak services, manage signatures/rules via `/admin/*` APIs.
- **Frontend Masking**: For web apps, fetch `clean_text` plus spans and highlight them in the UI. Combine Format Service results with inline hints to prompt correct user input.

---

## 6. Authentication, Security, and Environment Management

- **API Keys**: Every service reads comma-separated keys from `*_API_KEYS`. Provide keys via environment variables (`PII_API_KEYS`, `TOX_API_KEYS`, etc.) before launch.
- **Admin Keys**: Mutating endpoints require `*_ADMIN_API_KEYS` (PII, Secrets, Jailbreak, Format, Config). Protect these values and rotate periodically.
- **CORS**: `CORS_ALLOWED_ORIGINS` environment variables control front-end access. The default manifests include Lovable preview domains and localhost origins.
- **Environment Files**: Each service ships with `.env.example`; copy to `.env` and customize thresholds, CORS, and API keys (`cp pii_service/.env.example pii_service/.env`).
- **Scaling**: Services run independently—scale high-traffic detectors (PII, Toxicity) separately using Docker Compose (`docker compose up --scale pii-service=2`) or Kubernetes horizontal pod autoscalers.
- **Model Storage**: Heavy models (LlamaGuard GGUF, DeBERTa weights, GLiNER) mount from `./models`. Ensure volumes or persistent volumes are provisioned in production.

---

## 7. Error Handling & Troubleshooting

- **Gateway Retries**: Each service call retries once; persistent failures are surfaced in `results[service]["status"] == "error"` with `details`.
- **Fallback Policy**: When the Policy Service is unreachable, the gateway applies critical keyword rules to prevent weapon or harm instructions from slipping through.
- **Status Codes**: Services return HTTP `401` for auth errors, `4xx` for invalid payloads, and `5xx` for internal failures. The gateway wraps downstream errors as JSON rather than propagating raw status codes.
- **Health Checks**: Use `curl http://localhost:<port>/health` or `kubectl get pods -n z-grid` to verify readiness. Docker Compose includes healthchecks for all containers.
- **Logs**:
  - `docker compose logs -f <service>`
  - Kubernetes: `kubectl logs deployment/<service> -n z-grid`
  - Gateway includes per-service latency and error logs in its stdout.
- **Common Fixes**:
  - Missing models: Ensure blobs are downloaded (`download_deberta_model.py`, `upload_model_to_blob.sh`).
  - Auth failures: Verify `X-API-Key` header casing and value.
  - CORS issues: Update `CORS_ALLOWED_ORIGINS` and redeploy.
  - Entropy false positives: Increase `ENTROPY_THRESHOLD` or `MIN_TOKEN_LEN` in Secrets Service.

---

## 8. Quick Reference Commands

```bash
# Run core services locally
docker compose up gateway-service pii-service tox-service bias-service secrets-service

# Execute Python backend tests
pytest -q

# Start the React frontend (if present)
cd frontend && npm ci && npm run dev

# Validate all services via script (example)
python scripts/final_validation_test.py

# Port-forward services in Kubernetes
kubectl port-forward -n z-grid service/gateway-service 8008:8008
kubectl port-forward -n z-grid service/z-grid-monitoring-dashboard-service 5000:5000
```

With this detailed reference, you can deploy, operate, and extend the zGrid moderation platform—confidently routing conversations through the agentic gateway, understanding each service’s model stack and response contract, and maintaining observability across the entire system.
