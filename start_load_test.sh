#!/bin/bash

# Gateway V2 Load Test Deployment Script
# Deploys and starts the 48-hour load test for all 7 internal services

set -e

echo "🚀 Gateway V2 Load Test Deployment Script"
echo "========================================"

# Configuration
NAMESPACE="z-grid"
GATEWAY_URL="http://gateway-v2-service.z-grid:8008"
API_KEY="supersecret123"

echo "📋 Configuration:"
echo "   Namespace: $NAMESPACE"
echo "   Gateway URL: $GATEWAY_URL"
echo "   Test Duration: 48 hours"
echo "   Requests per Hour: 1,000"
echo "   Total Requests: 48,000"
echo ""

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl not found. Please install kubectl first."
    exit 1
fi

# Check if we can access the cluster
if ! kubectl cluster-info &> /dev/null; then
    echo "❌ Cannot connect to Kubernetes cluster. Please check your kubeconfig."
    exit 1
fi

echo "✅ Kubernetes cluster access verified"

# Check if the namespace exists
if ! kubectl get namespace $NAMESPACE &> /dev/null; then
    echo "❌ Namespace '$NAMESPACE' does not exist"
    exit 1
fi

echo "✅ Namespace '$NAMESPACE' found"

# Check if gateway v2 is running
echo "🔍 Checking Gateway V2 service..."
if ! kubectl get service gateway-v2-service -n $NAMESPACE &> /dev/null; then
    echo "❌ Gateway V2 service 'gateway-v2-service' not found in namespace $NAMESPACE"
    exit 1
fi

echo "✅ Gateway V2 service found"

# Test gateway connectivity
echo "🔍 Testing Gateway V2 connectivity..."
GATEWAY_POD=$(kubectl get pods -n $NAMESPACE -l app=gateway-v2 -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")

if [ -n "$GATEWAY_POD" ]; then
    echo "✅ Gateway V2 pod found: $GATEWAY_POD"

    # Test health endpoint
    if kubectl exec -n $NAMESPACE $GATEWAY_POD -- curl -s http://localhost:8008/health > /dev/null; then
        echo "✅ Gateway V2 health check passed"
    else
        echo "⚠️  Gateway V2 health check failed, but proceeding anyway..."
    fi
else
    echo "⚠️  Could not find Gateway V2 pod, but proceeding with deployment..."
fi

echo ""
echo "🚀 Deploying Load Test Infrastructure..."

# Deploy PVCs first
echo "📦 Deploying Persistent Volume Claims..."
kubectl apply -f k8s/load-test-pvcs.yaml -n $NAMESPACE

# Wait for PVCs to be bound
echo "⏳ Waiting for PVCs to be ready..."
kubectl wait --for=condition=Bound pvc/load-test-logs-pvc -n $NAMESPACE --timeout=60s
kubectl wait --for=condition=Bound pvc/load-test-reports-pvc -n $NAMESPACE --timeout=60s

# Deploy monitor service
echo "🖥️ Deploying Load Test Monitor..."
kubectl apply -f k8s/load-test-monitor.yaml -n $NAMESPACE

# Wait for monitor to be ready
echo "⏳ Waiting for monitor to be ready..."
kubectl wait --for=condition=Available deployment/load-test-monitor -n $NAMESPACE --timeout=120s

# Deploy the actual load test job
echo "🚀 Deploying 48-Hour Load Test Job..."
kubectl apply -f k8s/load-test-job.yaml -n $NAMESPACE

echo ""
echo "✅ Load test deployment completed!"
echo ""

# Get monitor service details
MONITOR_SERVICE="load-test-monitor-service"
echo "📊 Load Test Monitor Information:"
echo "================================"

# Get LoadBalancer IP if available
MONITOR_IP=$(kubectl get service $MONITOR_SERVICE -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "")
MONITOR_HOSTNAME=$(kubectl get service $MONITOR_SERVICE -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null || echo "")

if [ -n "$MONITOR_IP" ]; then
    echo "🌐 Monitor URL: http://$MONITOR_IP"
elif [ -n "$MONITOR_HOSTNAME" ]; then
    echo "🌐 Monitor URL: http://$MONITOR_HOSTNAME"
else
    echo "🔗 Port-forward to access monitor:"
    echo "   kubectl port-forward service/$MONITOR_SERVICE -n $NAMESPACE 8080:80"
    echo "   Then open: http://localhost:8080"
fi

echo ""
echo "🚀 Load Test Job Information:"
echo "============================="
LOAD_TEST_JOB="gateway-v2-load-test-48hr"

echo "📋 Job name: $LOAD_TEST_JOB"
echo "🔍 Check job status:"
echo "   kubectl get job $LOAD_TEST_JOB -n $NAMESPACE"
echo "📜 View job logs:"
echo "   kubectl logs job/$LOAD_TEST_JOB -n $NAMESPACE -f"
echo ""

# Get job pod
echo "🔍 Finding load test pod..."
LOAD_TEST_POD=$(kubectl get pods -n $NAMESPACE -l job-name=$LOAD_TEST_JOB -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")

if [ -n "$LOAD_TEST_POD" ]; then
    echo "✅ Load test pod: $LOAD_TEST_POD"
    echo ""
    echo "📊 Real-time monitoring commands:"
    echo "================================="
    echo "📜 Follow load test logs:"
    echo "   kubectl logs $LOAD_TEST_POD -n $NAMESPACE -f"
    echo ""
    echo "📈 Check pod resource usage:"
    echo "   kubectl top pod $LOAD_TEST_POD -n $NAMESPACE"
    echo ""
    echo "🔍 Check pod events:"
    echo "   kubectl describe pod $LOAD_TEST_POD -n $NAMESPACE"
else
    echo "⚠️  Load test pod not yet available. Check job status first."
fi

echo ""
echo "📊 Gateway V2 Service Monitoring:"
echo "================================="
echo "🔍 Check gateway pods:"
echo "   kubectl get pods -n $NAMESPACE -l app=gateway-v2"
echo ""
echo "📈 Check gateway service:"
echo "   kubectl get service gateway-v2-service -n $NAMESPACE -o wide"
echo ""
echo "📜 Check gateway logs:"
echo "   kubectl logs -n $NAMESPACE -l app=gateway-v2 --tail=100"

echo ""
echo "🔧 Internal Services Status:"
echo "=========================="
echo "🧠 Bias Detection (DeBERTa): bias-deberta-v3.z-grid:8012"
echo "☠️ Toxicity Detection: tox-service-ml-enabled.z-grid:8001"
echo "🔍 PII Detection: pii-enhanced-v3-service.z-grid:8000"
echo "🔑 Secrets Detection: secrets-service-yavar-fixed.z-grid:8005"
echo "🛡️ Jailbreak Detection: jailbreak-service-yavar-fixed.z-grid:8002"
echo "📋 Format Validation: format-service-yavar-fixed.z-grid:8006"
echo "🔤 Gibberish Detection: gibberish-service-yavar-fixed.z-grid:8007"

echo ""
echo "📂 Accessing Test Results:"
echo "=========================="
echo "📊 View logs volume:"
echo "   kubectl exec -it $LOAD_TEST_POD -n $NAMESPACE -- ls -la /app/load_test_logs/"
echo ""
echo "📄 View reports volume:"
echo "   kubectl exec -it $LOAD_TEST_POD -n $NAMESPACE -- ls -la /app/load_test_reports/"
echo ""
echo "📥 Download final report (when available):"
echo "   kubectl cp $LOAD_TEST_POD:/app/load_test_reports/gateway_v2_load_test_report_*.json ./load_test_report.json -n $NAMESPACE"

echo ""
echo "🛑 Cleanup Commands:"
echo "===================="
echo "🗑️ Delete load test job:"
echo "   kubectl delete job $LOAD_TEST_JOB -n $NAMESPACE"
echo ""
echo "🗑️ Delete monitor:"
echo "   kubectl delete deployment load-test-monitor -n $NAMESPACE"
echo "   kubectl delete service $MONITOR_SERVICE -n $NAMESPACE"
echo ""
echo "🗑️ Delete PVCs:"
echo "   kubectl delete pvc load-test-logs-pvc load-test-reports-pvc -n $NAMESPACE"

echo ""
echo "🎉 Load test deployment completed successfully!"
echo "📊 The test will run for 48 hours, sending 1,000 requests per hour"
echo "🔍 Each request tests all 7 internal services through Gateway V2"
echo "📄 Final report will be generated in JSON format with comprehensive metrics"