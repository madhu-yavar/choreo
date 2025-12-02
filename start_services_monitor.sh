#!/bin/bash

# This script starts all zGrid services using FastAPI's development server
# and monitors their status

# Function to start a service and log its output
start_service() {
    local service_name=$1
    local service_dir=$2
    local venv_dir=$3
    local port=$4
    local log_file="/tmp/${service_name// /_}.log"
    
    echo "Starting $service_name on port $port..."
    echo "Logging to $log_file"
    
    # Change to service directory
    cd $service_dir
    
    # Activate virtual environment and start service
    source $venv_dir/bin/activate
    python -m uvicorn app:app --host 0.0.0.0 --port $port > $log_file 2>&1 &
    local pid=$!
    
    # Deactivate virtual environment and return to original directory
    deactivate
    cd - > /dev/null
    
    # Store PID for later checking
    echo $pid > "/tmp/${service_name// /_}.pid"
    
    echo "$service_name started with PID $pid"
}

# Function to check if a service is running
check_service() {
    local service_name=$1
    local port=$2
    
    # Try to access the health endpoint
    if curl -s --max-time 10 http://localhost:$port/health > /dev/null; then
        echo "$service_name: Running"
    else
        echo "$service_name: Not responding (check logs)"
    fi
}

# Start all services one by one
echo "Starting all zGrid services..."
echo "=============================="

start_service "PII Service" "/Users/yavar/Documents/CoE/zGrid/pii_service" "/Users/yavar/Documents/CoE/zGrid/guards311" 8000
sleep 3  # Give the service time to start

start_service "Toxicity Service" "/Users/yavar/Documents/CoE/zGrid/tox_service" "/Users/yavar/Documents/CoE/zGrid/guards" 8001
sleep 3

start_service "Jailbreak Service" "/Users/yavar/Documents/CoE/zGrid/jail_service" "/Users/yavar/Documents/CoE/zGrid/jail_service/jail_venv" 8002
sleep 3

start_service "Policy Service" "/Users/yavar/Documents/CoE/zGrid/policy_service" "/Users/yavar/Documents/CoE/zGrid/policy_service/policy_venv" 8003
sleep 3

start_service "Ban Service" "/Users/yavar/Documents/CoE/zGrid/ban_service" "/Users/yavar/Documents/CoE/zGrid/ban_service/ban_venv" 8004
sleep 3

start_service "Secrets Service" "/Users/yavar/Documents/CoE/zGrid/secrets_service" "/Users/yavar/Documents/CoE/zGrid/secrets_service/secrets_venv" 8005
sleep 3

start_service "Format Service" "/Users/yavar/Documents/CoE/zGrid/format_service" "/Users/yavar/Documents/CoE/zGrid/format_service/format_venv" 8006
sleep 3

echo ""
echo "Waiting for services to initialize..."
sleep 60  # Give more time for services to start, especially toxicity service which needs to download models

echo ""
echo "Checking service status..."
echo "========================="
check_service "PII Service" 8000
check_service "Toxicity Service" 8001
check_service "Jailbreak Service" 8002
check_service "Policy Service" 8003
check_service "Ban Service" 8004
check_service "Secrets Service" 8005
check_service "Format Service" 8006

echo ""
echo "To check logs for a specific service, use:"
echo "tail -f /tmp/[Service_Name].log"
echo ""
echo "To stop all services, use:"
echo "pkill -f 'uvicorn app:app'"