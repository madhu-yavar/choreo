#!/bin/bash

# Z-Grid Chatbot Service Azure Kubernetes Deployment Script
# K8s-native deployment without local Docker building

set -e

echo "🚀 Z-GRID CHATBOT SERVICE AZURE KUBERNETES DEPLOYMENT"
echo "======================================================"

# Configuration
NAMESPACE="zgrid"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${BLUE}ℹ️  INFO:${NC} $1"
}

log_success() {
    echo -e "${GREEN}✅ SUCCESS:${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}⚠️  WARNING:${NC} $1"
}

log_error() {
    echo -e "${RED}❌ ERROR:${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check if kubectl is available
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed or not in PATH"
        exit 1
    fi

    # Check if connected to Kubernetes cluster
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Not connected to a Kubernetes cluster"
        exit 1
    fi

    # Check if connected to Azure cluster specifically
    if ! kubectl get nodes -o wide | grep -i "aks" &> /dev/null; then
        log_warning "This doesn't appear to be an Azure Kubernetes Service (AKS) cluster"
        log_info "Proceeding anyway, but Azure-specific features may not work"
    fi

    log_success "Prerequisites check passed"
}

# Create namespace if it doesn't exist
create_namespace() {
    log_info "Creating namespace: ${NAMESPACE}"

    kubectl create namespace ${NAMESPACE} --dry-run=client -o yaml | kubectl apply -f -

    log_success "Namespace ${NAMESPACE} is ready"
}

# Deploy Kubernetes resources using Azure-optimized approach
deploy_k8s() {
    log_info "Deploying chatbot service to Azure Kubernetes..."

    # Apply the Azure-optimized deployment configuration
    log_info "Applying Azure-optimized deployment..."
    kubectl apply -f k8s/chatbot-service-deployment-azure.yaml -n ${NAMESPACE}

    if [ $? -eq 0 ]; then
        log_success "Kubernetes resources deployed successfully"
    else
        log_error "Kubernetes deployment failed"
        exit 1
    fi
}

# Wait for deployment to be ready
wait_for_deployment() {
    log_info "Waiting for deployment to be ready..."

    # Wait for pods to be created and started
    log_info "Waiting for pods to be created..."
    kubectl wait --for=condition=available deployment/zgrid-chatbot-service -n ${NAMESPACE} --timeout=600s

    # Wait for pods to be ready
    log_info "Waiting for pods to be ready..."
    kubectl wait --for=condition=ready pod -l app=zgrid-chatbot-service -n ${NAMESPACE} --timeout=300s

    if [ $? -eq 0 ]; then
        log_success "Deployment is ready"
    else
        log_warning "Deployment taking longer than expected, continuing..."
    fi
}

# Get external IP
get_external_ip() {
    log_info "Getting external IP for the service..."

    # Get the LoadBalancer service external IP
    EXTERNAL_IP=""
    for i in {1..60}; do
        EXTERNAL_IP=$(kubectl get service zgrid-chatbot-service-external -n ${NAMESPACE} -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "")

        # Also try to get hostname (some Azure LBs provide hostname instead)
        if [ -z "$EXTERNAL_IP" ]; then
            EXTERNAL_IP=$(kubectl get service zgrid-chatbot-service-external -n ${NAMESPACE} -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null || echo "")
        fi

        if [ -n "$EXTERNAL_IP" ]; then
            break
        fi

        log_info "Waiting for external IP... (attempt $i/60)"
        sleep 10
    done

    if [ -n "$EXTERNAL_IP" ]; then
        log_success "External endpoint allocated: ${EXTERNAL_IP}"
        echo ""
        echo "🌐 EXTERNAL ACCESS URLS:"
        echo "========================"
        echo "🔗 Chatbot API: http://${EXTERNAL_IP}:8010"
        echo "🔗 Health Check: http://${EXTERNAL_IP}:8010/"
        echo "🔗 WebSocket: ws://${EXTERNAL_IP}:8010/ws"
        echo ""
        echo "📋 TEST COMMANDS:"
        echo "=================="
        echo "# Test health check:"
        echo "curl http://${EXTERNAL_IP}:8010/"
        echo ""
        echo "# Test chat endpoint:"
        echo "curl -X POST http://${EXTERNAL_IP}:8010/chat \\"
        echo "  -H 'Content-Type: application/json' \\"
        echo "  -d '{\"message\": \"Hello Zee!\", \"user_name\": \"test\"}'"
        echo ""
        echo "# Test PII detection:"
        echo "curl -X POST http://${EXTERNAL_IP}:8010/chat \\"
        echo "  -H 'Content-Type: application/json' \\"
        echo "  -d '{\"message\": \"My email is john.doe@example.com\", \"user_name\": \"pii_test\"}'"
        echo ""
        echo "# Test comprehensive PII (32 entities):"
        echo "curl -X POST http://${EXTERNAL_IP}:8010/chat \\"
        echo "  -H 'Content-Type: application/json' \\"
        echo "  -d '{\"message\": \"John Doe, 123 Main Street, Chennai, born 15/05/1985, mobile +91-9876543210, email john.doe@example.com, Aadhaar 1234 5678 9012, PAN ABCDE1234F, GSTIN 33ABCDE1234F1Z5\", \"user_name\": \"comprehensive_test\"}'"
        echo ""
    else
        log_warning "External endpoint not allocated yet. You can check manually with:"
        echo "kubectl get service zgrid-chatbot-service-external -n ${NAMESPACE}"
        echo ""
        echo "Or use port-forwarding for testing:"
        echo "kubectl port-forward service/zgrid-chatbot-service-external 8010:8010 -n ${NAMESPACE}"
        echo ""
    fi
}

# Show deployment status
show_status() {
    log_info "Deployment Status:"
    echo "===================="

    echo "Pods:"
    kubectl get pods -l app=zgrid-chatbot-service -n ${NAMESPACE}
    echo ""
    echo "Services:"
    kubectl get services -l app=zgrid-chatbot-service -n ${NAMESPACE}
    echo ""
    echo "LoadBalancer Services:"
    kubectl get services -n ${NAMESPACE} -o wide | grep LoadBalancer || echo "No LoadBalancer services found"
    echo ""
    echo "HPA (if configured):"
    kubectl get hpa -n ${NAMESPACE} 2>/dev/null || echo "No HPA configured"
    echo ""
    echo "Node Status:"
    kubectl get nodes -o wide | head -5
    echo ""
}

# Cleanup function
cleanup() {
    log_warning "Cleaning up previous deployment..."
    kubectl delete -f k8s/chatbot-service-deployment-azure.yaml -n ${NAMESPACE} --ignore-not-found=true
    log_info "Cleanup completed"
}

# Test the deployed service
test_deployment() {
    log_info "Testing the deployed service..."

    # Get service endpoint
    EXTERNAL_IP=$(kubectl get service zgrid-chatbot-service-external -n ${NAMESPACE} -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "")
    if [ -z "$EXTERNAL_IP" ]; then
        EXTERNAL_IP=$(kubectl get service zgrid-chatbot-service-external -n ${NAMESPACE} -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null || echo "")
    fi

    if [ -n "$EXTERNAL_IP" ]; then
        log_info "Testing health endpoint..."
        if curl -f -s http://${EXTERNAL_IP}:8010/ > /dev/null; then
            log_success "Health check passed"
        else
            log_warning "Health check failed"
        fi

        log_info "Testing chat endpoint..."
        response=$(curl -s -X POST http://${EXTERNAL_IP}:8010/chat \
            -H "Content-Type: application/json" \
            -d '{"message": "Hello from Azure!", "user_name": "test"}' || echo "")

        if echo "$response" | grep -q "response"; then
            log_success "Chat endpoint test passed"
        else
            log_warning "Chat endpoint test failed: $response"
        fi
    else
        log_warning "Cannot test - no external IP available"
    fi
}

# Main execution
main() {
    echo "Starting Azure Kubernetes deployment at $(date)"
    echo ""

    # Parse arguments
    CLEANUP=false
    TEST=false

    for arg in "$@"; do
        case $arg in
            --cleanup)
                CLEANUP=true
                ;;
            --test)
                TEST=true
                ;;
            --help)
                echo "Usage: $0 [options]"
                echo "Options:"
                echo "  --cleanup Clean up previous deployment before deploying"
                echo "  --test     Test the deployment after it's ready"
                echo "  --help     Show this help message"
                exit 0
                ;;
        esac
    done

    # Execute deployment steps
    if [ "$CLEANUP" = true ]; then
        cleanup
    fi

    check_prerequisites
    create_namespace
    deploy_k8s
    wait_for_deployment
    get_external_ip
    show_status

    if [ "$TEST" = true ]; then
        test_deployment
    fi

    echo ""
    log_success "🎉 Chatbot service deployment completed successfully!"
    echo ""
    log_info "📝 Next Steps:"
    echo "1. Test the service using the provided URLs"
    echo "2. Verify Gateway 2 integration with PII detection"
    echo "3. Monitor pod logs: kubectl logs -f deployment/zgrid-chatbot-service -n ${NAMESPACE}"
    echo "4. Check HPA status: kubectl get hpa -n ${NAMESPACE} --watch"
    echo ""
}

# Trap to handle interruption
trap 'log_error "Deployment interrupted"; exit 1' INT TERM

# Run main function
main "$@"