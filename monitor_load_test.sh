#!/bin/bash

# Gateway V2 Load Test Monitoring Script
# Real-time monitoring and status reporting for the 48-hour load test

set -e

NAMESPACE="z-grid"
LOAD_TEST_JOB="gateway-v2-load-test-48hr-fixed"
MONITOR_SERVICE="load-test-monitor-service"

echo "📊 Gateway V2 Load Test Monitoring Dashboard"
echo "============================================="

# Function to show current status
show_status() {
    echo ""
    echo "🔍 Current Status - $(date)"
    echo "========================"

    # Job status
    echo "📋 Load Test Job Status:"
    kubectl get job $LOAD_TEST_JOB -n $NAMESPACE -o custom-columns=NAME:.metadata.name,COMPLETIONS:.status.succeeded,FAILED:.status.failed,DURATION:.status.active | grep -v COMPLETIONS || echo "Job not found"

    # Pod status
    echo ""
    echo "🚀 Load Test Pod Status:"
    kubectl get pods -n $NAMESPACE -l job-name=$LOAD_TEST_JOB -o custom-columns=NAME:.metadata.name,STATUS:.status.phase,RESTARTS:.status.restartCount,NODE:.spec.nodeName

    # Monitor service status
    echo ""
    echo "🖥️ Monitor Service Status:"
    kubectl get service $MONITOR_SERVICE -n $NAMESPACE -o custom-columns=NAME:.metadata.name,TYPE:.spec.type,CLUSTER-IP:.spec.clusterIP,EXTERNAL-IP:.status.loadBalancer.ingress[0].ip

    # Gateway V2 pods
    echo ""
    echo "🎯 Gateway V2 Service Status:"
    kubectl get pods -n $NAMESPACE -l app=gateway-v2 --field-selector=status.phase=Running -o custom-columns=NAME:.metadata.name,READY:.status.containerStatuses[0].ready,RESTARTS:.status.restartCount

    # Resource usage
    echo ""
    echo "📈 Resource Usage:"
    echo "Load Test Pod:"
    kubectl top pod -n $NAMESPACE -l job-name=$LOAD_TEST_JOB 2>/dev/null || echo "Metrics not available"
    echo "Gateway V2 Pods:"
    kubectl top pod -n $NAMESPACE -l app=gateway-v2 2>/dev/null || echo "Metrics not available"
}

# Function to show recent logs
show_logs() {
    local lines=${1:-20}
    echo ""
    echo "📜 Recent Load Test Logs (last $lines lines):"
    echo "============================================"

    POD=$(kubectl get pods -n $NAMESPACE -l job-name=$LOAD_TEST_JOB -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
    if [ -n "$POD" ]; then
        kubectl logs $POD -n $NAMESPACE --tail=$lines
    else
        echo "Load test pod not found"
    fi
}

# Function to show access instructions
show_access() {
    echo ""
    echo "🔗 Access Instructions"
    echo "======================"

    # Monitor dashboard access
    MONITOR_IP=$(kubectl get service $MONITOR_SERVICE -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null)
    MONITOR_HOSTNAME=$(kubectl get service $MONITOR_SERVICE -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null)

    if [ -n "$MONITOR_IP" ]; then
        echo "🌐 Monitor Dashboard: http://$MONITOR_IP"
    elif [ -n "$MONITOR_HOSTNAME" ]; then
        echo "🌐 Monitor Dashboard: http://$MONITOR_HOSTNAME"
    else
        echo "🔗 Port-forward to access monitor:"
        echo "   kubectl port-forward service/$MONITOR_SERVICE -n $NAMESPACE 8080:80"
        echo "   Then open: http://localhost:8080"
    fi

    echo ""
    echo "📜 Follow load test logs:"
    POD=$(kubectl get pods -n $NAMESPACE -l job-name=$LOAD_TEST_JOB -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
    if [ -n "$POD" ]; then
        echo "   kubectl logs $POD -n $NAMESPACE -f"
    fi

    echo ""
    echo "🔍 Check gateway V2 service logs:"
    echo "   kubectl logs -n $NAMESPACE -l app=gateway-v2 --tail=100 -f"

    echo ""
    echo "📊 Internal Services Being Tested:"
    echo "   🧠 DeBERTa Bias Detection: bias-deberta-v3.z-grid:8012"
    echo "   ☠️ Toxicity Detection: tox-service-ml-enabled.z-grid:8001"
    echo "   🔍 PII Detection: pii-enhanced-v3-service.z-grid:8000"
    echo "   🔑 Secrets Detection: secrets-service-yavar-fixed.z-grid:8005"
    echo "   🛡️ Jailbreak Detection: jailbreak-service-yavar-fixed.z-grid:8002"
    echo "   📋 Format Validation: format-service-yavar-fixed.z-grid:8006"
    echo "   🔤 Gibberish Detection: gibberish-service-yavar-fixed.z-grid:8007"
}

# Function to show load test progress
show_progress() {
    echo ""
    echo "📊 Load Test Progress Analysis"
    echo "==============================="

    POD=$(kubectl get pods -n $NAMESPACE -l job-name=$LOAD_TEST_JOB -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
    if [ -n "$POD" ]; then
        echo "🔍 Analyzing recent logs for progress..."

        # Extract progress information from logs
        LOGS=$(kubectl logs $POD -n $NAMESPACE --tail=100)

        if echo "$LOGS" | grep -q "🚀 STARTING 48-HOUR GATEWAY V2 LOAD TEST"; then
            echo "✅ Load test has started successfully"

            # Look for progress updates
            if echo "$LOGS" | grep -q "📈"; then
                echo "📈 Progress updates found:"
                echo "$LOGS" | grep "📈" | tail -5
            else
                echo "⏳ Waiting for first progress update (usually takes a few minutes)..."
            fi
        else
            echo "⏳ Load test still initializing..."
        fi

        # Look for any error messages
        if echo "$LOGS" | grep -qi "error\|failed\|exception"; then
            echo ""
            echo "⚠️ Potential issues detected in logs:"
            echo "$LOGS" | grep -i "error\|failed\|exception" | tail -3
        fi
    else
        echo "❌ Load test pod not found"
    fi
}

# Function to check health of all services
check_service_health() {
    echo ""
    echo "🏥 Service Health Check"
    echo "======================="

    echo "🎯 Gateway V2 Health:"
    GATEWAY_POD=$(kubectl get pods -n $NAMESPACE -l app=gateway-v2 -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
    if [ -n "$GATEWAY_POD" ]; then
        kubectl exec -n $NAMESPACE $GATEWAY_POD -- curl -s http://localhost:8008/health 2>/dev/null | python3 -m json.tool 2>/dev/null || echo "Health check failed"
    fi

    echo ""
    echo "📊 Service Pod Status:"
    kubectl get pods -n $NAMESPACE -o custom-columns=NAME:.metadata.name,STATUS:.status.phase,READY:.status.containerStatuses[0].ready | grep -E "(bias|tox|pii|secrets|jailbreak|format|gibberish|gateway)" | sort
}

# Main script logic
case "${1:-status}" in
    "status")
        show_status
        show_progress
        ;;
    "logs")
        show_logs "${2:-50}"
        ;;
    "access")
        show_access
        ;;
    "health")
        check_service_health
        ;;
    "monitor")
        while true; do
            clear
            echo "📊 Gateway V2 Load Test - Live Monitoring"
            echo "=========================================="
            echo "Last updated: $(date)"
            echo ""

            show_status
            show_progress

            echo ""
            echo "Press Ctrl+C to stop monitoring"
            echo "Monitoring every 30 seconds..."
            sleep 30
        done
        ;;
    "help")
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  status   - Show current status and progress"
        echo "  logs     - Show recent logs (usage: $0 logs [number_of_lines])"
        echo "  access   - Show access instructions for dashboard"
        echo "  health   - Check health of all services"
        echo "  monitor  - Start continuous monitoring (updates every 30s)"
        echo "  help     - Show this help"
        ;;
    *)
        echo "Unknown command: $1"
        echo "Use '$0 help' for usage information"
        exit 1
        ;;
esac