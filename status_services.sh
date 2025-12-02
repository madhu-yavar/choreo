#!/bin/bash

# ZGrid Services Status Script
# This script checks the status of all ZGrid services

# Define colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[STATUS]${NC} $1"
}

# Function to check if a port is in use
is_port_in_use() {
    lsof -i :$1 >/dev/null 2>&1
}

# Function to get process info for a port
get_process_info() {
    lsof -ti :$1
}

print_status "ZGrid Services Status"
print_status "===================="

# Define services
services=( 
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

# Check each service
for service_info in "${services[@]}"; do
    IFS=':' read -r service_name port <<< "$service_info"
    
    if is_port_in_use $port; then
        pid=$(get_process_info $port)
        echo -e "$service_name: ${GREEN}RUNNING${NC} (port $port, PID $pid)"
    else
        echo -e "$service_name: ${RED}NOT RUNNING${NC} (port $port)"
    fi
done