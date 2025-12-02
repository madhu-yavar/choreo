#!/bin/bash

# ZGrid Services Stop Script
# This script stops all ZGrid services

# Define colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[STATUS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to stop a service
stop_service() {
    local service_name=$1
    local port=$2
    local pid_file=".uvicorn_${port}.pid"
    
    print_status "Stopping $service_name (port $port)..."
    
    # Check if PID file exists
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if kill -0 $pid 2>/dev/null; then
            kill $pid
            rm "$pid_file"
            print_status "$service_name stopped (PID $pid)"
        else
            print_warning "$service_name PID $pid is not running"
            rm "$pid_file"
        fi
    else
        # Try to find process by port
        local pid=$(lsof -ti :$port)
        if [ ! -z "$pid" ]; then
            kill $pid
            print_status "$service_name stopped (PID $pid)"
        else
            print_warning "$service_name is not running on port $port"
        fi
    fi
}

# Function to force kill if needed
force_kill_service() {
    local service_name=$1
    local port=$2
    
    local pid=$(lsof -ti :$port)
    if [ ! -z "$pid" ]; then
        kill -9 $pid 2>/dev/null
        print_status "Force killed $service_name (PID $pid)"
    fi
}

# Main execution
print_status "ZGrid Services Stop Script"
print_status "=========================="

# Stop services one by one
stop_service "PII Service" 8000
stop_service "Toxicity Service" 8001
stop_service "Jailbreak Service" 8002
stop_service "Policy Service" 8003
stop_service "Ban Service" 8004
stop_service "Secrets Service" 8005
stop_service "Format Service" 8006
stop_service "Gibberish Service" 8007
stop_service "Gateway Service" 8008
stop_service "Config Service" 8009

print_status "All stop commands issued!"
print_status "Waiting 5 seconds..."
sleep 5

# Force kill any remaining services
print_status "Force killing any remaining services..."
force_kill_service "PII Service" 8000
force_kill_service "Toxicity Service" 8001
force_kill_service "Jailbreak Service" 8002
force_kill_service "Policy Service" 8003
force_kill_service "Ban Service" 8004
force_kill_service "Secrets Service" 8005
force_kill_service "Format Service" 8006
force_kill_service "Gibberish Service" 8007
force_kill_service "Gateway Service" 8008
force_kill_service "Config Service" 8009

print_status "Services stop process completed!"