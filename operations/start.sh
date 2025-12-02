#!/bin/bash
# Start Content Moderation Gateway Service

echo "Starting Content Moderation Gateway Service..."

# Check if the virtual environment exists, if not create it
if [ ! -d "gateway_venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv gateway_venv
fi

# Activate virtual environment
source gateway_venv/bin/activate

# Install requirements if not already installed
if [ ! -f "gateway_venv/installed" ]; then
    echo "Installing requirements..."
    pip install -r requirements.txt
    touch gateway_venv/installed
fi

# Start the service
echo "Starting gateway service on port 8008..."
python -m uvicorn app:app --host 0.0.0.0 --port 8008