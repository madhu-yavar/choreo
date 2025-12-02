#!/bin/bash

# ZGrid Services Startup Script
# This script starts all ZGrid services in the background

# Exit on any error
set -e

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

# Function to check if a port is in use
is_port_in_use() {
    lsof -i :$1 >/dev/null 2>&1
}

# Function to start a service
start_service() {
    local service_name=$1
    local port=$2
    local dir=$3
    local app_module=${4:-"app:app"}
    
    print_status "Checking if $service_name is already running on port $port..."
    if is_port_in_use $port; then
        print_warning "$service_name is already running on port $port"
        return 0
    fi
    
    print_status "Starting $service_name on port $port..."
    
    # Change to service directory
    cd $dir
    
    # Check if virtual environment exists and activate it
    if [ -d "venv" ]; then
        source venv/bin/activate
        print_status "Activated virtual environment for $service_name"
    elif [ -d "../guards" ]; then
        source ../guards/bin/activate
        print_status "Activated shared virtual environment for $service_name"
    elif [ -d "../guards311" ]; then
        source ../guards311/bin/activate
        print_status "Activated shared virtual environment for $service_name"
    else
        print_warning "No virtual environment found for $service_name, using system Python"
    fi
    
    # Start the service in the background
    if command -v uvicorn &> /dev/null; then
        uvicorn $app_module --host 0.0.0.0 --port $port --log-level info &
        local pid=$!
        echo $pid > ".uvicorn_${port}.pid"
        print_status "$service_name started with PID $pid"
    else
        print_error "uvicorn not found. Please install it with: pip install uvicorn"
        return 1
    fi
    
    # Return to root directory
    cd - > /dev/null
}

# Function to check if all services are running
check_services() {
    local services=( 
        "PII Service:8000"
        "Toxicity Service:8001"
        "Jailbreak Service:8002"
        "Policy Service:8003"
        "Ban Service:8004"
        "Secrets Service:8005"
        "Format Service:8006"
        "Gibberish Service:8007"
        "Gateway Service:8008"
        "Config Service:8009"
    )
    
    print_status "Checking service status..."
    echo "----------------------------------------"
    
    for service_info in "${services[@]}"; do
        IFS=':' read -r service_name port <<< "$service_info"
        
        if is_port_in_use $port; then
            echo -e "$service_name: ${GREEN}RUNNING${NC} (port $port)"
        else
            echo -e "$service_name: ${RED}NOT RUNNING${NC} (port $port)"
        fi
    done
    
    echo "----------------------------------------"
}

# Main execution
print_status "ZGrid Services Startup Script"
print_status "============================="

# Start services one by one
start_service "PII Service" 8000 "./pii_service"
start_service "Toxicity Service" 8001 "./tox_service"
start_service "Jailbreak Service" 8002 "./jail_service"
start_service "Policy Service" 8003 "./policy_service"
start_service "Ban Service" 8004 "./ban_service"
start_service "Secrets Service" 8005 "./secrets_service"
start_service "Format Service" 8006 "./format_service"
start_service "Gibberish Service" 8007 "./gibberish_service"
start_service "Gateway Service" 8008 "./gateway_service"
start_service "Config Service" 8009 "./config_service"

print_status "All services startup commands issued!"
print_status "Waiting 10 seconds for services to initialize..."
sleep 10

# Check status of all services
check_services

print_status "Services startup process completed!"
print_status "Use './stop_services.sh' to stop all services"