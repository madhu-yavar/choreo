# Bias & Brand Safety (Ban List) Service

Local, config-driven brand safety moderation:
- Exact, regex, and fuzzy matching
- Normalization (NFKC), leet, basic homoglyph folding
- Allowlist to reduce false positives
- Actions: refrain | filter | mask | reask

## Run locally
```bash
cd ban_service
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app:app --host 0.0.0.0 --port 8004 --reload --env-file .env
