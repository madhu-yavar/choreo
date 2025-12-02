#!/bin/bash

# Phi Service Startup Script

set -e

echo "🚀 Starting Phi Content Analysis Service..."

# Default port if not set
export PHI_SERVICE_PORT=${PHI_SERVICE_PORT:-8009}

# Default model if not set
export PHI_MODEL_ID=${PHI_MODEL_ID:-microsoft/Phi-3.5-mini-instruct}

# Force CPU mode for Azure
export PHI_DEVICE="cpu"

echo "☁️ Azure Phi Content Analysis Service Configuration:"
echo "  Model: $PHI_MODEL_ID"
echo "  Device: $PHI_DEVICE (Azure CPU optimized)"
echo "  Port: $PHI_SERVICE_PORT"
echo "  Temperature: ${PHI_TEMPERATURE:-0.1}"
echo "  Max Tokens: ${PHI_MAX_TOKENS:-512}"
echo "  OMP Threads: ${OMP_NUM_THREADS:-4}"

# Start the service
echo "☁️ Starting Azure FastAPI server..."
python -m uvicorn app:app \
    --host 0.0.0.0 \
    --port $PHI_SERVICE_PORT \
    --workers 1 \
    --log-level info \
    --timeout-keep-alive 120