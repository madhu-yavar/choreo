# Gibberish Detection Service

This service detects gibberish text using machine learning models and heuristic analysis.

## Features

- Detects random character sequences and nonsensical text
- Configurable threshold for sensitivity
- Multiple action modes (refrain, filter, mask)
- RESTful API with health checks
- Docker support

## API Endpoints

### Health Check
```
GET /health
```

### Validate Text
```
POST /validate
```

Headers:
- `Content-Type: application/json`
- `X-API-Key: <your-api-key>`

Body:
```json
{
  "text": "string to analyze",
  "threshold": 0.8,
  "min_length": 10,
  "action_on_fail": "refrain",
  "return_spans": true
}
```

Parameters:
- `text`: The text to analyze
- `threshold`: Detection threshold (0.0-1.0), defaults to 0.8
- `min_length`: Minimum text length to analyze, defaults to 10
- `action_on_fail`: Action when gibberish detected (refrain, filter, mask), defaults to "refrain"
- `return_spans`: Whether to return detailed span information, defaults to true

## Response Format

```json
{
  "status": "pass|blocked|fixed",
  "clean_text": "processed text",
  "is_gibberish": true|false,
  "confidence": 0.0-1.0,
  "flagged": [...],
  "steps": [...],
  "reasons": [...]
}
```

## Environment Variables

- `GIBBERISH_API_KEYS`: Comma-separated list of valid API keys
- `GIBBERISH_ADMIN_API_KEYS`: Comma-separated list of admin API keys
- `GIBBERISH_THRESHOLD`: Default detection threshold (0.0-1.0)
- `GIBBERISH_MIN_LENGTH`: Minimum text length to analyze
- `GIBBERISH_ACTION_ON_FAIL`: Default action when gibberish detected
- `MODEL_PATH`: Path to the gibberish detection model
- `RETURN_GIBBERISH_DETAILS`: Whether to return detailed information
- `CORS_ALLOWED_ORIGINS`: Comma-separated list of allowed CORS origins

## Running the Service

### With Docker

```bash
docker-compose up --build
```

### Without Docker

1. Create a virtual environment:
   ```bash
   python -m venv gibberish_venv
   source gibberish_venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the service:
   ```bash
   python app.py
   ```

## Testing

Run the test script:
```bash
python test_gibberish_service.py
```