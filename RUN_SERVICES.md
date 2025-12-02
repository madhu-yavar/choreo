# How to Run Z-Grid Services

## Quick Start

### 1. Install Dependencies
```bash
# Install core dependencies
pip install -r requirements.txt

# Install service-specific dependencies  
pip install -r requirements_pii.txt
pip install -r requirements_jailbreak.txt
pip install -r requirements_format.txt
pip install -r requirements_gibberish.txt
```

### 2. Run Individual Services

#### Jailbreak Detection API
```bash
python jailbreak_detection_api.py
# Runs on: http://localhost:8001
```

#### Enhanced Jailbreak Service
```bash  
python jailbreak_roberta_heuristic_service.py
# Runs on: http://localhost:8002
```

#### Format Service
```bash
python format_service.py
# Runs on: http://localhost:8006
```

#### Gibberish Detection
```bash
python gibberish_service.py
# Runs on: http://localhost:8003
```

### 3. Using Docker (Recommended)
```bash
# Build and run jailbreak service
docker build -f Dockerfile.jailbreak-roberta -t zgrid-jailbreak .
docker run -p 8001:8001 zgrid-jailbreak

# Build and run format service  
docker build -f Dockerfile.format-service -t zgrid-format .
docker run -p 8006:8006 zgrid-format
```

### 4. Kubernetes Deployment
```bash
# Deploy all services
kubectl apply -f k8s/
```

## Testing Services

Each service has a `/health` endpoint:
```bash
curl http://localhost:8001/health
curl http://localhost:8002/health  
curl http://localhost:8006/health
```

## Notes
- Models will be downloaded automatically on first run
- Some services may require additional configuration
- See individual service directories for detailed setup
