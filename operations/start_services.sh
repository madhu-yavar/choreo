#!/bin/bash

# Z-Grid Services Startup Script
# Starts Phi service and Intelligent Gateway with proper MPS GPU support

set -e

echo "🚀 Starting Z-Grid Services for Phi-3.5 Intelligent Gateway"
echo "============================================================="

# Get the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Function to check if a port is in use
check_port() {
    local port=$1
    if lsof -i :$port >/dev/null 2>&1; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Function to wait for service to be ready
wait_for_service() {
    local url=$1
    local name=$2
    local max_attempts=30
    local attempt=1

    echo "⏳ Waiting for $name to be ready..."

    while [ $attempt -le $max_attempts ]; do
        if curl -s -f "$url" >/dev/null 2>&1; then
            echo "✅ $name is ready!"
            return 0
        fi
        echo "   Attempt $attempt/$max_attempts..."
        sleep 2
        ((attempt++))
    done

    echo "❌ $name failed to start within expected time"
    return 1
}

# Check if ports are already in use
echo "🔍 Checking port availability..."

if check_port 8009; then
    echo "⚠️  Port 8009 is already in use (Phi service might be running)"
    PHI_RUNNING=true
else
    PHI_RUNNING=false
fi

if check_port 8001; then
    echo "⚠️  Port 8001 is already in use (Gateway service might be running)"
    GATEWAY_RUNNING=true
else
    GATEWAY_RUNNING=false
fi

# Start Phi Service if not running
if [ "$PHI_RUNNING" = false ]; then
    echo ""
    echo "🧠 Starting Phi Service with MPS GPU acceleration..."

    # Set MPS device for Apple Silicon
    export PHI_DEVICE=mps
    export PHI_MODEL_ID=microsoft/Phi-3.5-mini-instruct

    cd services/phi_service

    # Start Phi service in background
    nohup ./start.sh > phi_service.log 2>&1 &
    PHI_PID=$!

    echo "📋 Phi Service started with PID: $PHI_PID"
    echo "   Device: MPS (Apple Silicon GPU)"
    echo "   Model: microsoft/Phi-3.5-mini-instruct"
    echo "   Port: 8009"
    echo "   Log file: $(pwd)/phi_service.log"

    # Wait for Phi service to be ready
    if wait_for_service "http://localhost:8009/health" "Phi Service"; then
        echo "✅ Phi Service is healthy and ready!"

        # Show Phi service details
        curl -s "http://localhost:8009/health" -H "x-api-key: supersecret123" | python3 -m json.tool || echo "   Health check successful"
    else
        echo "❌ Phi Service failed to start properly"
        echo "   Check the log file: $(pwd)/phi_service.log"
        exit 1
    fi

    cd "$SCRIPT_DIR"
else
    echo "✅ Phi Service is already running on port 8009"
fi

# Start Gateway Service if not running
if [ "$GATEWAY_RUNNING" = false ]; then
    echo ""
    echo "🔥 Starting Intelligent Gateway Service..."

    cd gateway_service

    # Start Gateway service in background
    nohup python app_circuit_breaker.py > gateway_service.log 2>&1 &
    GATEWAY_PID=$!

    echo "📋 Gateway Service started with PID: $GATEWAY_PID"
    echo "   Port: 8001"
    echo "   Features: Circuit Breaker, Intelligent Routing, Phi Integration"
    echo "   Log file: $(pwd)/gateway_service.log"

    # Wait for Gateway service to be ready
    if wait_for_service "http://localhost:8001/health" "Gateway Service"; then
        echo "✅ Gateway Service is healthy and ready!"

        # Show gateway service details
        curl -s "http://localhost:8001/health" -H "x-api-key: supersecret123" | python3 -m json.tool || echo "   Health check successful"
    else
        echo "❌ Gateway Service failed to start properly"
        echo "   Check the log file: $(pwd)/gateway_service.log"
        exit 1
    fi

    cd "$SCRIPT_DIR"
else
    echo "✅ Gateway Service is already running on port 8001"
fi

echo ""
echo "🎉 All Z-Grid Services are running and ready!"
echo "============================================================="
echo ""
echo "📊 Service Summary:"
echo "   🧠 Phi Service:     http://localhost:8009 (MPS GPU enabled)"
echo "   🔥 Gateway Service: http://localhost:8001 (Intelligent Routing)"
echo ""
echo "🧪 Ready for testing! Try these curl commands:"
echo ""
echo "   # Health checks:"
echo "   curl -X GET 'http://localhost:8001/health' -H 'x-api-key: supersecret123'"
echo "   curl -X GET 'http://localhost:8009/health' -H 'x-api-key: supersecret123'"
echo ""
echo "   # Test intelligent routing:"
echo "   curl -X POST 'http://localhost:8001/validate' \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -H 'x-api-key: supersecret123' \\"
echo "     -d '{\"text\": \"Hello, how are you today?\", \"intelligent_routing\": true}'"
echo ""
echo "   # Test PII detection:"
echo "   curl -X POST 'http://localhost:8001/validate' \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -H 'x-api-key: supersecret123' \\"
echo "     -d '{\"text\": \"My email is john@example.com\", \"intelligent_routing\": true}'"
echo ""
echo "📝 Log files:"
if [ "$PHI_RUNNING" = false ]; then
    echo "   Phi Service:     $(pwd)/services/phi_service/phi_service.log"
fi
if [ "$GATEWAY_RUNNING" = false ]; then
    echo "   Gateway Service: $(pwd)/gateway_service/gateway_service.log"
fi
echo ""
echo "🛑 To stop services:"
echo "   pkill -f 'app_circuit_breaker.py'  # Stop Gateway"
echo "   pkill -f 'uvicorn.*app:app'       # Stop Phi"
echo ""
echo "✨ Your Phi-3.5 Intelligent Gateway is ready for testing! 🚀"