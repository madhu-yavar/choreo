# Format Service

This service provides input format validation using Cucumber expressions.

## Running the Service

To run the format service directly with FastAPI:

```bash
uvicorn app:app --host 0.0.0.0 --port 8005 --reload
```

## Running Other Services Directly

This directory also contains scripts to run the PII and Toxicity services directly with FastAPI without Docker:

- [Running Services Guide](RUNNING_SERVICES.md) - Instructions for running services directly
- [run_pii_service.py](run_pii_service.py) - Script to run PII service (port 8000)
- [run_tox_service.py](run_tox_service.py) - Script to run Toxicity service (port 8001)
- [run_both_services.py](run_both_services.py) - Script to run both services simultaneously
- [combined_requirements.txt](combined_requirements.txt) - Combined requirements for all services

## API Endpoints

- `GET /health` - Health check endpoint
- `POST /validate` - Validate input against Cucumber expressions

## Configuration

The service is configured using environment variables in the `.env` file.