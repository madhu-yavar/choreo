#!/bin/bash

# Z-Grid Chatbot Service Kubernetes Deployment Script
# Enhanced for Gateway 2 integration with external IP access

set -e

echo "🚀 Z-GRID CHATBOT SERVICE KUBERNETES DEPLOYMENT"
echo "===================================================="

# Configuration
IMAGE_NAME="zgrid/chatbot-service"
IMAGE_TAG="gateway2-v2"
NAMESPACE="zgrid"
DOCKER_REGISTRY="your-registry.com"  # Update with your registry

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

    # Check if docker is available
    if ! command -v docker &> /dev/null; then
        log_error "docker is not installed or not in PATH"
        exit 1
    fi

    # Check if connected to Kubernetes cluster
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Not connected to a Kubernetes cluster"
        exit 1
    fi

    log_success "Prerequisites check passed"
}

# Build Docker image
build_image() {
    log_info "Building Docker image for chatbot service..."

    cd services/chatbot_service

    # Use the K8s optimized Dockerfile
    docker build -f Dockerfile.k8s -t ${IMAGE_NAME}:${IMAGE_TAG} .

    if [ $? -eq 0 ]; then
        log_success "Docker image built successfully: ${IMAGE_NAME}:${IMAGE_TAG}"
    else
        log_error "Docker image build failed"
        exit 1
    fi

    cd ../..
}

# Optional: Push to registry
push_image() {
    if [ "$1" = "--push" ]; then
        log_info "Pushing image to registry..."

        docker tag ${IMAGE_NAME}:${IMAGE_TAG} ${DOCKER_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}
        docker push ${DOCKER_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}

        if [ $? -eq 0 ]; then
            log_success "Image pushed to registry successfully"
        else
            log_error "Failed to push image to registry"
            exit 1
        fi
    fi
}

# Create namespace if it doesn't exist
create_namespace() {
    log_info "Creating namespace: ${NAMESPACE}"

    kubectl create namespace ${NAMESPACE} --dry-run=client -o yaml | kubectl apply -f -

    log_success "Namespace ${NAMESPACE} is ready"
}

# Deploy Kubernetes resources
deploy_k8s() {
    log_info "Deploying chatbot service to Kubernetes..."

    # Deploy ConfigMap first
    log_info "Applying ConfigMap..."
    kubectl apply -f k8s/chatbot-service-deployment-updated.yaml -n ${NAMESPACE}

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

    # Wait for pods to be ready
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
    for i in {1..30}; do
        EXTERNAL_IP=$(kubectl get service zgrid-chatbot-service-external -n ${NAMESPACE} -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "")

        if [ -n "$EXTERNAL_IP" ]; then
            break
        fi

        log_info "Waiting for external IP... (attempt $i/30)"
        sleep 10
    done

    if [ -n "$EXTERNAL_IP" ]; then
        log_success "External IP allocated: ${EXTERNAL_IP}"
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
    else
        log_warning "External IP not allocated yet. You can check manually with:"
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
    echo "HPA (if configured):"
    kubectl get hpa -n ${NAMESPACE} 2>/dev/null || echo "No HPA configured"
    echo ""
}

# Cleanup function
cleanup() {
    log_warning "Cleaning up previous deployment..."
    kubectl delete -f k8s/chatbot-service-deployment-updated.yaml -n ${NAMESPACE} --ignore-not-found=true
    log_info "Cleanup completed"
}

# Main execution
main() {
    echo "Starting deployment at $(date)"
    echo ""

    # Parse arguments
    PUSH_IMAGE=false
    CLEANUP=false

    for arg in "$@"; do
        case $arg in
            --push)
                PUSH_IMAGE=true
                ;;
            --cleanup)
                CLEANUP=true
                ;;
            --help)
                echo "Usage: $0 [options]"
                echo "Options:"
                echo "  --push    Push image to registry after building"
                echo "  --cleanup Clean up previous deployment before deploying"
                echo "  --help    Show this help message"
                exit 0
                ;;
        esac
    done

    # Execute deployment steps
    if [ "$CLEANUP" = true ]; then
        cleanup
    fi

    check_prerequisites
    build_image
    push_image $([ "$PUSH_IMAGE" = true ] && echo "--push")
    create_namespace
    deploy_k8s
    wait_for_deployment
    get_external_ip
    show_status

    echo ""
    log_success "🎉 Chatbot service deployment completed successfully!"
    echo ""
}

# Trap to handle interruption
trap 'log_error "Deployment interrupted"; exit 1' INT TERM

# Run main function
main "$@"