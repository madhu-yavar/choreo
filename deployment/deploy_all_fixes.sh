#!/bin/bash
# Z-Grid Connectivity Fixes Deployment Script
# Run this script to deploy all connectivity fixes

set -e

echo "=================================================================="
echo "🚀 Z-Grid Connectivity Fixes Deployment"
echo "=================================================================="
echo ""

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    local status=$1
    local message=$2

    case $status in
        "SUCCESS")
            echo -e "${GREEN}✓${NC} $message"
            ;;
        "INFO")
            echo -e "${YELLOW}ℹ${NC} $message"
            ;;
        "ERROR")
            echo -e "${RED}✗${NC} $message"
            ;;
        "WARN")
            echo -e "${YELLOW}⚠${NC} $message"
            ;;
    esac
}

# Check if kubectl is configured
if ! kubectl cluster-info &>/dev/null; then
    print_status "ERROR" "Cannot connect to Kubernetes cluster. Please check your kubeconfig."
    exit 1
fi

print_status "SUCCESS" "Connected to Kubernetes cluster"

# Check if z-grid namespace exists
print_status "INFO" "Checking z-grid namespace..."
if ! kubectl get namespace z-grid &>/dev/null; then
    print_status "INFO" "Creating z-grid namespace..."
    kubectl create namespace z-grid
    print_status "SUCCESS" "Created z-grid namespace"
else
    print_status "SUCCESS" "z-grid namespace exists"
fi

# Deploy SSL certificate
print_status "INFO" "Deploying SSL certificate..."
if kubectl apply -f k8s/wildcard-ssl-certificate.yaml --validate=false; then
    print_status "SUCCESS" "SSL certificate deployed"
else
    print_status "WARN" "SSL certificate deployment failed, continuing..."
fi

# Deploy unified ingress configuration
print_status "INFO" "Deploying unified ingress configuration..."
if kubectl apply -f k8s/zgrid-all-services-ingress.yaml --validate=false; then
    print_status "SUCCESS" "Unified ingress deployed"
else
    print_status "ERROR" "Failed to deploy unified ingress"
    exit 1
fi

# Deploy monitoring dashboard
print_status "INFO" "Deploying monitoring dashboard..."
if kubectl apply -f k8s/service-monitoring-dashboard.yaml --validate=false; then
    print_status "SUCCESS" "Monitoring dashboard deployed"
else
    print_status "WARN" "Monitoring dashboard deployment failed"
fi

# Check if ingress controller is ready
print_status "INFO" "Checking ingress controller..."
if kubectl get pods -n ingress-nginx | grep -q "Running"; then
    print_status "SUCCESS" "Ingress controller is running"
else
    print_status "WARN" "Ingress controller may not be ready"
fi

# Wait for ingress to be ready
print_status "INFO" "Waiting for ingress to become available..."
sleep 10

# Run service discovery check
print_status "INFO" "Running service discovery check..."
if kubectl create -f k8s/service-discovery-check.yaml --validate=false; then
    print_status "SUCCESS" "Service discovery job created"

    # Wait for job completion
    echo "Waiting for service discovery to complete..."
    kubectl wait --for=condition=complete job/zgrid-service-discovery -n z-grid --timeout=120s || true

    # Show logs
    print_status "INFO" "Service discovery results:"
    kubectl logs job/zgrid-service-discovery -n z-grid || true
else
    print_status "WARN" "Service discovery job creation failed"
fi

# Test connectivity to services
print_status "INFO" "Testing connectivity to main gateway..."
echo "Testing main gateway health endpoint..."

# Test with curl
for i in {1..3}; do
    echo "Attempt $i of 3..."
    if curl -k -s -o /dev/null -w "%{http_code}" \
        -H "X-API-Key: supersecret123" \
        "https://zgrid-gateway.20.242.183.197.nip.io/health" | grep -q "200"; then
        print_status "SUCCESS" "Gateway is responding!"
        break
    else
        if [ $i -eq 3 ]; then
            print_status "WARN" "Gateway not yet accessible (may need DNS propagation)"
        else
            echo "Retrying in 10 seconds..."
            sleep 10
        fi
    fi
done

# Show service status
print_status "INFO" "Current service status:"
echo ""
echo "=== Services in z-grid namespace ==="
kubectl get services -n z-grid || print_status "WARN" "Could not list services"

echo ""
echo "=== Pods in z-grid namespace ==="
kubectl get pods -n z-grid || print_status "WARN" "Could not list pods"

echo ""
echo "=== Ingress status ==="
kubectl get ingress -n z-grid || print_status "WARN" "Could not list ingress"

echo ""
echo "=== External IP of Load Balancer ==="
kubectl get svc ingress-nginx-controller -n ingress-nginx -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "Load balancer IP not available"

echo ""
echo "=================================================================="
echo "🎉 Deployment Complete!"
echo "=================================================================="
echo ""

print_status "INFO" "Next steps:"
echo "1. Wait 2-3 minutes for DNS propagation"
echo "2. Run the connectivity test: ./test_all_services_connectivity.sh"
echo "3. Access the monitoring dashboard (if deployed)"
echo ""

print_status "INFO" "Service URLs:"
echo "• Main Gateway: https://zgrid-gateway.20.242.183.197.nip.io"
echo "• API Gateway: https://api.20.242.183.197.nip.io"
echo "• Individual services: https://service-name.20.242.183.197.nip.io"
echo ""

print_status "INFO" "Quick test command:"
echo "curl -X POST \"https://zgrid-gateway.20.242.183.197.nip.io/validate\" \\"
echo "  -H \"Content-Type: application/json\" \\"
echo "  -H \"X-API-Key: supersecret123\" \\"
echo "  -d '{\"text\": \"test\", \"check_pii\": true}' \\"
echo "  --max-time 300 --insecure | jq ."
echo ""

# Run a basic connectivity test
echo "Running quick connectivity test..."
if ./test_all_services_connectivity.sh 2>/dev/null; then
    print_status "SUCCESS" "All services are accessible!"
else
    print_status "WARN" "Some services may not be ready yet"
    echo "Please wait a few minutes and run: ./test_all_services_connectivity.sh"
fi