#!/bin/bash

# This script starts all zGrid services using FastAPI's development server

# Function to start a service
start_service() {
    local service_name=$1
    local service_dir=$2
    local venv_dir=$3
    local port=$4
    
    echo "Starting $service_name on port $port..."
    cd $service_dir
    source $venv_dir/bin/activate
    python -m uvicorn app:app --host 0.0.0.0 --port $port &
    echo "$service_name started with PID $!"
    deactivate
    cd - > /dev/null
}

# Start all services
start_service "PII Service" "/Users/yavar/Documents/CoE/zGrid/pii_service" "/Users/yavar/Documents/CoE/zGrid/guards311" 8000
start_service "Toxicity Service" "/Users/yavar/Documents/CoE/zGrid/tox_service" "/Users/yavar/Documents/CoE/zGrid/guards" 8001
start_service "Jailbreak Service" "/Users/yavar/Documents/CoE/zGrid/jail_service" "/Users/yavar/Documents/CoE/zGrid/jail_service/jail_venv" 8002
start_service "Policy Service" "/Users/yavar/Documents/CoE/zGrid/policy_service" "/Users/yavar/Documents/CoE/zGrid/policy_service/policy_venv" 8003
start_service "Ban Service" "/Users/yavar/Documents/CoE/zGrid/ban_service" "/Users/yavar/Documents/CoE/zGrid/ban_service/ban_venv" 8004
start_service "Secrets Service" "/Users/yavar/Documents/CoE/zGrid/secrets_service" "/Users/yavar/Documents/CoE/zGrid/secrets_service/secrets_venv" 8005
start_service "Format Service" "/Users/yavar/Documents/CoE/zGrid/format_service" "/Users/yavar/Documents/CoE/zGrid/format_service/format_venv" 8006

echo "All services started!"
echo "You can check their status by running 'curl http://localhost:<port>/health' for each service"