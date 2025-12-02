#!/bin/bash

# Z-Grid Chatbot Startup Script
# This script starts all services needed for the chatbot demo

set -e

echo "🌟 Starting Z-Grid Chatbot Demo Environment..."

# Check if we're in the right directory
if [ ! -f "services/chatbot_service/app.py" ]; then
    echo "❌ Error: Please run this script from the z_grid root directory"
    exit 1
fi

# Function to check if a service is running
check_service() {
    local url=$1
    local name=$2
    echo "🔍 Checking $name..."
    if curl -s "$url" > /dev/null; then
        echo "✅ $name is running"
        return 0
    else
        echo "❌ $name is not responding"
        return 1
    fi
}

# Function to start a service in background
start_service() {
    local service_dir=$1
    local service_name=$2
    local port=$3
    local command=$4

    echo "🚀 Starting $service_name on port $port..."
    cd "$service_dir"

    # Activate virtual environment if exists
    if [ -d "venv" ]; then
        source venv/bin/activate
    fi

    # Install dependencies if needed
    if [ -f "requirements.txt" ] && [ ! -d "venv" ]; then
        echo "📦 Installing dependencies for $service_name..."
        python3 -m venv venv
        source venv/bin/activate
        pip install -r requirements.txt
    fi

    # Start the service
    nohup $command > "${service_name}.log" 2>&1 &
    echo $! > "${service_name}.pid"
    cd - > /dev/null

    echo "✅ $service_name started (PID: $(cat ${service_dir}/${service_name}.pid))"
}

# Function to stop a service
stop_service() {
    local service_dir=$1
    local service_name=$2

    if [ -f "${service_dir}/${service_name}.pid" ]; then
        local pid=$(cat "${service_dir}/${service_name}.pid")
        echo "🛑 Stopping $service_name (PID: $pid)..."
        kill $pid 2>/dev/null || true
        rm -f "${service_dir}/${service_name}.pid"
        echo "✅ $service_name stopped"
    fi
}

# Cleanup function
cleanup() {
    echo "🧹 Cleaning up services..."
    stop_service "gateway_service" "gateway"
    stop_service "services/chatbot_service" "chatbot"
    echo "✅ Cleanup complete"
    exit 0
}

# Trap Ctrl+C to cleanup
trap cleanup SIGINT SIGTERM

# Main execution
case "${1:-start}" in
    "start")
        echo "🏗️  Starting Z-Grid services for chatbot demo..."

        # Start Gateway Service
        if check_service "http://localhost:8000/health" "Gateway Service"; then
            echo "✅ Gateway service already running"
        else
            start_service "gateway_service" "gateway" "8000" "python app_circuit_breaker.py"
            sleep 5
        fi

        # Start Chatbot Service
        if check_service "http://localhost:8008/" "Chatbot Service"; then
            echo "✅ Chatbot service already running"
        else
            start_service "services/chatbot_service" "chatbot" "8008" "python app.py"
            sleep 3
        fi

        # Check Frontend
        echo "🌐 Starting Frontend..."
        cd frontend
        if [ ! -d "node_modules" ]; then
            echo "📦 Installing frontend dependencies..."
            npm install
        fi

        echo "🚀 Starting frontend development server..."
        npm run dev &
        FRONTEND_PID=$!
        cd - > /dev/null

        echo "🎉 Z-Grid Chatbot Demo is starting up!"
        echo ""
        echo "📱 Access the demo at:"
        echo "   • Technical View: http://localhost:3000"
        echo "   • Meet Zee Chatbot: http://localhost:3000 (click 'Meet Zee' button)"
        echo ""
        echo "🔧 Services running:"
        echo "   • Gateway Service: http://localhost:8000"
        echo "   • Chatbot Service: http://localhost:8008"
        echo "   • Frontend: http://localhost:3000"
        echo ""
        echo "💡 Try these demo prompts:"
        echo "   • 'Hi Zee! How are you today?'"
        echo "   • 'My email is john.doe@example.com' (PII detection)"
        echo "   • 'Tell me about Z-Grid services' (educational)"
        echo "   • 'This is absolutely terrible!' (toxicity detection)"
        echo ""
        echo "Press Ctrl+C to stop all services..."

        # Keep script running
        wait $FRONTEND_PID
        ;;

    "stop")
        echo "🛑 Stopping Z-Grid Chatbot services..."
        stop_service "gateway_service" "gateway"
        stop_service "services/chatbot_service" "chatbot"

        # Stop frontend
        pkill -f "npm run dev" || true
        pkill -f "vite" || true
        echo "✅ All services stopped"
        ;;

    "status")
        echo "📊 Checking Z-Grid services status..."
        check_service "http://localhost:8000/health" "Gateway Service"
        check_service "http://localhost:8008/" "Chatbot Service"
        check_service "http://localhost:3000" "Frontend"
        ;;

    "test")
        echo "🧪 Testing chatbot functionality..."
        echo "Testing health endpoints..."

        # Test chatbot service
        echo "📤 Testing chatbot service..."
        curl -s http://localhost:8008/ | jq . || echo "Chatbot service test failed"

        echo "📤 Testing chat endpoint..."
        curl -X POST http://localhost:8008/chat \
            -H "Content-Type: application/json" \
            -d '{"message": "Hello Zee!"}' | jq . || echo "Chat endpoint test failed"

        echo "✅ Tests completed"
        ;;

    "logs")
        echo "📋 Service logs:"
        echo ""
        echo "🚀 Gateway Service logs:"
        tail -f gateway_service/gateway.log 2>/dev/null || echo "No gateway logs found"
        ;;

    *)
        echo "Usage: $0 {start|stop|status|test|logs}"
        echo ""
        echo "Commands:"
        echo "  start  - Start all Z-Grid chatbot services"
        echo "  stop   - Stop all running services"
        echo "  status - Check service health status"
        echo "  test   - Test service functionality"
        echo "  logs   - Show service logs"
        exit 1
        ;;
esac