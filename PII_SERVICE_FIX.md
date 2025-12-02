# PII Service GLiNER Fix

## Problem
The production PII service (http://52.170.163.62:8000) is not detecting PERSON or LOCATION entities, only basic patterns like EMAIL_ADDRESS. This is a critical security gap.

## Root Cause
GLiNER model is not loading properly in the production container due to:
1. Model files missing or corrupted
2. Silent initialization failures
3. Inadequate error handling and logging

## Solution Implemented

### 1. Enhanced Health Endpoint (`/health`)
- Added GLiNER status reporting (loaded, labels, threshold, model_path)
- Shows available entities and error states
- Provides debugging information

### 2. Improved GLiNER Initialization (`pii_gliner.py`)
- Better error handling with detailed logging
- Model file validation before loading
- Graceful degradation when GLiNER fails
- Clear error messages in logs

### 3. Enhanced Bootstrap Script (`bootstrap_and_run.sh`)
- Detailed logging of model download process
- Verification of downloaded files
- Better error reporting when downloads fail
- Status reporting before service startup

### 4. Request Body Format Fix
- Updated to use `check_*` flags instead of `services` array
- Aligns with documented gateway contract

## Deployment Steps

### 1. Build and Deploy New PII Service
```bash
# Build new Docker image
cd z_grid/pii_service
docker build -t pii-service:fixed .

# Update Kubernetes deployment
kubectl apply -f ../deploy/k8s/pii-service-deployment.yaml
```

### 2. Verify GLiNER Status
```bash
# Check health endpoint
curl http://52.170.163.62:8000/health | jq .

# Should show GLiNER loaded with labels
{
  "ok": true,
  "gliner": {
    "loaded": true,
    "labels": ["person", "location", "organization"],
    "threshold": 0.45,
    "model_path": "/app/models/gliner_small-v2.1"
  }
}
```

### 3. Test PERSON Detection
```bash
# Test with PERSON entity
curl -s -X POST http://52.170.163.62:8000/validate \
  -H "Content-Type: application/json" \
  -H "x-api-key: supersecret123" \
  -d '{"text": "My name is John Doe", "entities": ["PERSON"], "gliner_threshold": 0.3}' | jq .

# Should detect PERSON entities
{
  "entities": [
    {
      "type": "PERSON",
      "value": "John Doe",
      "score": 0.8,
      "start": 11,
      "end": 19
    }
  ],
  "status": "refrain"
}
```

### 4. Test Through Gateway
```bash
# Test through gateway
curl -s -X POST https://gateway.20.242.183.197.nip.io/validate \
  -H "Content-Type: application/json" \
  -H "x-api-key: supersecret123" \
  -d '{"text": "Meet Rakesh from London", "check_pii": true}' | jq .

# Should detect both PERSON and LOCATION
```

## Monitoring
- Check container logs for GLiNER initialization messages
- Health endpoint shows GLiNER status
- Watch for "[GLiNER]" log messages during startup

## Rollback
If issues occur, rollback by:
```bash
kubectl rollout undo deployment/pii-service
```

## Testing Checklist
- [ ] Health endpoint shows GLiNER loaded
- [ ] PERSON detection works with direct PII service calls
- [ ] LOCATION detection works with direct PII service calls
- [ ] Gateway aggregation includes PERSON/LOCATION entities
- [ ] Frontend correctly displays detected entities
- [ ] Container logs show successful GLiNER initialization