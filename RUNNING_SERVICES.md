# Running PII and Toxicity Services Directly with FastAPI

This directory contains scripts to run the PII service (port 8000) and Toxicity service (port 8001) directly with FastAPI without using Docker.

## Prerequisites

1. Python 3.11 installed
2. Virtual environment (recommended)
3. All required dependencies installed

## Installation

1. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install the combined requirements:
   ```bash
   pip install -r combined_requirements.txt
   ```

3. Download required models:

   For PII service:
   ```bash
   python -m spacy download en_core_web_lg
   ```

   For Toxicity service:
   ```bash
   python -c "import nltk; nltk.download('punkt')"
   ```

## Running the Services

### Option 1: Run Both Services Simultaneously

```bash
python run_both_services.py
```

This will start both services:
- PII service on port 8000
- Toxicity service on port 8001

Press Ctrl+C to stop both services.

### Option 2: Run Services Individually

Run the PII service:
```bash
python run_pii_service.py
```

In a separate terminal, run the Toxicity service:
```bash
python run_tox_service.py
```

### Option 3: Using uvicorn directly

You can also run the services directly with uvicorn:

For PII service:
```bash
cd ../pii_service
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

For Toxicity service:
```bash
cd ../tox_service
uvicorn app:app --host 0.0.0.0 --port 8001 --reload
```

## Testing the Services

You can test the services using curl or any HTTP client:

PII Service Health Check:
```bash
curl http://localhost:8000/health
```

Toxicity Service Health Check:
```bash
curl http://localhost:8001/health
```

## Environment Variables

Make sure the environment variables in the `.env` files in each service directory are properly configured:
- `../pii_service/.env`
- `../tox_service/.env`

## Notes

1. The services will use the same configuration as when running in Docker.
2. Make sure the required model files are downloaded and accessible.
3. The services will log to stdout, similar to the Docker version.