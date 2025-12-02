#!/bin/bash

# Load Test Dashboard Access Script
# Provides multiple ways to access your 48-hour load test monitoring

NAMESPACE="z-grid"

echo "🚀 Gateway V2 Load Test Dashboard Access"
echo "=========================================="

# Function to show load test status
show_status() {
    echo ""
    echo "📊 Current Load Test Status:"
    echo "=========================="

    # Load test pod
    POD=$(kubectl get pods -n $NAMESPACE -l job-name=gateway-v2-load-test-48hr-fixed -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
    if [ -n "$POD" ]; then
        echo "🚀 Load Test Pod: $POD"
        echo "📈 Status: $(kubectl get pod $POD -n $NAMESPACE -o jsonpath='{.status.phase}')"
        echo "💾 Memory Usage: $(kubectl top pod $POD -n $NAMESPACE 2>/dev/null | awk 'NR>1 {print $3}' || echo 'Not available')"
        echo "🖥️ CPU Usage: $(kubectl top pod $POD -n $NAMESPACE 2>/dev/null | awk 'NR>1 {print $2}' || echo 'Not available')"
    else
        echo "❌ Load test pod not found"
    fi

    # Gateway V2 pods
    echo ""
    echo "🎯 Gateway V2 Service Status:"
    kubectl get pods -n $NAMESPACE -l app=gateway-v2 -o custom-columns=NAME:.metadata.name,READY:.status.containerStatuses[0].ready,STATUS:.status.phase

    # Internal services
    echo ""
    echo "🔧 Internal Services Status:"
    SERVICES=("bias-deberta-v3" "tox-service-ml-enabled" "pii-enhanced-v3" "secrets-service-yavar-fixed" "jailbreak-service-yavar-fixed" "format-service-yavar-fixed" "gibberish-service-yavar-fixed")
    for service in "${SERVICES[@]}"; do
        COUNT=$(kubectl get pods -n $NAMESPACE -l app=$service --no-headers 2>/dev/null | wc -l)
        READY=$(kubectl get pods -n $NAMESPACE -l app=$service --no-headers 2>/dev/null | grep "1/1" | wc -l)
        echo "   $(echo $service | sed 's/-yavar-fixed//'): $READY/$COUNT pods ready"
    done
}

# Function to show access methods
show_access() {
    echo ""
    echo "🔗 Load Test Dashboard Access Options:"
    echo "====================================="

    echo ""
    echo "1️⃣  PORT-FORWARD ACCESS (Recommended - Immediate Access):"
    echo "   ------------------------------------------------------"
    echo "   # Start port forwarding in one terminal:"
    echo "   kubectl port-forward service/load-test-monitor-service -n $NAMESPACE 8080:80"
    echo ""
    echo "   # Then access dashboard in browser:"
    echo "   http://localhost:8080"
    echo ""

    echo "2️⃣  DIRECT LOGS MONITORING:"
    echo "   -----------------------"
    if [ -n "$POD" ]; then
        echo "   # Follow load test logs in real-time:"
        echo "   kubectl logs $POD -n $NAMESPACE -f"
        echo ""
        echo "   # Check progress updates:"
        echo "   kubectl logs $POD -n $NAMESPACE --tail=50 | grep '📈'"
    fi

    echo ""
    echo "3️⃣  API ACCESS:"
    echo "   ------------"
    echo "   # Load test status API:"
    echo "   curl -s http://localhost:8080/api/status | python3 -m json.tool"
    echo ""

    echo "4️⃣  YOUR EXISTING DASHBOARD INTEGRATION:"
    echo "   -------------------------------------"
    echo "   Your existing dashboard at http://134.33.241.178/ can be enhanced"
    echo "   by adding this iframe or API integration:"
    echo ""
    echo "   <iframe src='http://localhost:8080' width='100%' height='600'></iframe>"
    echo ""
    echo "   Or call the API from your dashboard:"
    echo "   fetch('http://localhost:8080/api/status').then(r=>r.json()).then(console.log)"
}

# Function to show monitoring commands
show_monitoring() {
    echo ""
    echo "📈 Real-time Monitoring Commands:"
    echo "================================="
    echo ""
    echo "🔄 CONTINUOUS STATUS UPDATES:"
    echo "   watch -n 5 './scripts/monitor_load_test.sh status'"
    echo ""
    echo "📜 LOG MONITORING:"
    echo "   ./scripts/monitor_load_test.sh logs 20"
    echo ""
    echo "🏥 HEALTH CHECKS:"
    echo "   ./scripts/monitor_load_test.sh health"
    echo ""
    echo "📊 FULL MONITORING DASHBOARD:"
    echo "   ./scripts/monitor_load_test.sh monitor"
    echo ""
    echo "💾 RESOURCE USAGE:"
    echo "   kubectl top pods -n $NAMESPACE | grep -E '(gateway|load-test)'"
    echo ""
    echo "🎯 GATEWAY V2 PERFORMANCE:"
    echo "   kubectl logs -n $NAMESPACE -l app=gateway-v2 --tail=50"
}

# Function to show load test details
show_details() {
    echo ""
    echo "🎯 Load Test Configuration:"
    echo "=========================="
    echo "   • Duration: 48 hours"
    echo "   • Rate: 1,000 requests per hour"
    echo "   • Total: 48,000 requests"
    echo "   • Interval: Every 3.6 seconds"
    echo "   • Target: Gateway V2 (gateway-v2-service.z-grid:8008)"
    echo ""
    echo "🔧 Services Being Tested:"
    echo "   • 🧠 DeBERTa Bias Detection (AI bias analysis)"
    echo "   • ☠️ Toxicity Detection (ML-powered content moderation)"
    echo "   • 🔍 PII Detection (Personal information identification)"
    echo "   • 🔑 Secrets Detection (API keys, credentials)"
    echo "   • 🛡️ Jailbreak Detection (Prompt injection prevention)"
    echo "   • 📋 Format Validation (Pattern matching)"
    echo "   • 🔤 Gibberish Detection (Content filtering)"
}

# Main execution
case "${1:-access}" in
    "status")
        show_status
        ;;
    "access")
        show_access
        ;;
    "monitor")
        show_monitoring
        ;;
    "details")
        show_details
        ;;
    "all")
        show_status
        show_details
        show_access
        show_monitoring
        ;;
    "help")
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  status  - Show current load test and service status"
        echo "  access  - Show dashboard access options"
        echo "  monitor - Show monitoring commands"
        echo "  details - Show load test configuration details"
        echo "  all     - Show all information"
        echo "  help    - Show this help"
        ;;
    *)
        echo "Unknown command: $1"
        echo "Use '$0 help' for usage information"
        exit 1
        ;;
esac