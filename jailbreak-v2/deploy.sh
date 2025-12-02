#!/bin/bash

# Production-ready jailbreak detection deployment script
# Deploys optimized DistilBERT model with 97.6% accuracy

set -e

# Configuration
NAMESPACE="z-grid"
CHART_NAME="jailbreak-distilbert"
RELEASE_NAME="jailbreak-prod"
MODEL_PATH="../jailbreak_distilbert_1035data/model"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed or not in PATH"
        exit 1
    fi

    # Check Helm (optional)
    if ! command -v helm &> /dev/null; then
        log_warning "Helm is not installed. Will use direct YAML deployment."
        USE_HELM=false
    else
        USE_HELM=true
    fi

    # Check cluster access
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot access Kubernetes cluster"
        exit 1
    fi

    # Check model files
    if [ ! -d "$MODEL_PATH" ]; then
        log_error "Model directory not found: $MODEL_PATH"
        log_info "Please ensure the optimized model is available at jailbreak_distilbert_1035data/model/"
        exit 1
    fi

    log_success "Prerequisites check passed"
}

# Create namespace
create_namespace() {
    log_info "Creating namespace: $NAMESPACE"

    if kubectl get namespace "$NAMESPACE" &> /dev/null; then
        log_warning "Namespace $NAMESPACE already exists"
    else
        kubectl create namespace "$NAMESPACE"
        log_success "Namespace $NAMESPACE created"
    fi
}

# Deploy using YAML files (direct method)
deploy_yaml() {
    log_info "Deploying using direct YAML files..."

    # Deploy in order
    local files=("configmap.yaml" "secret.yaml" "pvc.yaml" "service.yaml" "deployment.yaml")

    for file in "${files[@]}"; do
        log_info "Applying $file..."
        if kubectl apply -f "$file" -n "$NAMESPACE"; then
            log_success "$file applied successfully"
        else
            log_error "Failed to apply $file"
            exit 1
        fi
    done

    # Wait for PVC to be bound
    log_info "Waiting for PVC to be bound..."
    kubectl wait --for=condition=Bound pvc/jailbreak-distilbert-v2-pvc -n "$NAMESPACE" --timeout=300s

    # Copy model to PVC
    log_info "Copying model to PVC..."
    copy_model_to_pvc

    # Wait for deployment
    log_info "Waiting for deployment to be ready..."
    kubectl wait --for=condition=available deployment/jailbreak-distilbert-v2 -n "$NAMESPACE" --timeout=600s

    log_success "Deployment completed successfully"
}

# Deploy using Helm
deploy_helm() {
    log_info "Deploying using Helm..."

    # Check if release exists
    if helm list -n "$NAMESPACE" | grep -q "$RELEASE_NAME"; then
        log_warning "Release $RELEASE_NAME already exists. Upgrading..."
        helm upgrade "$RELEASE_NAME" . \
            --namespace "$NAMESPACE" \
            --values values.yaml \
            --wait \
            --timeout 600s
    else
        log_info "Installing new release..."
        helm install "$RELEASE_NAME" . \
            --namespace "$NAMESPACE" \
            --values values.yaml \
            --wait \
            --timeout 600s
    fi

    # Copy model to PVC
    log_info "Copying model to PVC..."
    copy_model_to_pvc

    log_success "Helm deployment completed successfully"
}

# Copy model files to PVC
copy_model_to_pvc() {
    log_info "Copying optimized model to PVC..."

    # Wait for a pod to be running
    local pod_name
    pod_name=$(kubectl get pods -l app=jailbreak-distilbert -n "$NAMESPACE" -o jsonpath='{.items[0].metadata.name}')

    if [ -z "$pod_name" ]; then
        log_error "No running pod found. Waiting for pod startup..."
        sleep 30
        pod_name=$(kubectl get pods -l app=jailbreak-distilbert -n "$NAMESPACE" -o jsonpath='{.items[0].metadata.name}')
    fi

    if [ -z "$pod_name" ]; then
        log_error "Could not find running pod to copy model"
        exit 1
    fi

    log_info "Found pod: $pod_name"

    # Copy model files
    if kubectl exec "$pod_name" -n "$NAMESPACE" -- test -d /model_volume; then
        kubectl cp "$MODEL_PATH" "$NAMESPACE/$pod_name:/model_volume" -c jailbreak-detector
        log_success "Model files copied successfully"
    else
        log_error "Model volume not found in pod"
        exit 1
    fi
}

# Verify deployment
verify_deployment() {
    log_info "Verifying deployment..."

    # Check pods
    local pod_status
    pod_status=$(kubectl get pods -l app=jailbreak-distilbert -n "$NAMESPACE" -o jsonpath='{.items[0].status.phase}')

    if [ "$pod_status" = "Running" ]; then
        log_success "Pods are running"
    else
        log_error "Pods are not running. Status: $pod_status"
        kubectl get pods -l app=jailbreak-distilbert -n "$NAMESPACE"
        exit 1
    fi

    # Check services
    if kubectl get service jailbreak-distilbert-v2 -n "$NAMESPACE" &> /dev/null; then
        log_success "Service is created"
    else
        log_error "Service creation failed"
        exit 1
    fi

    # Get service IP
    local service_ip
    service_ip=$(kubectl get service jailbreak-distilbert-v2 -n "$NAMESPACE" -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

    if [ -n "$service_ip" ]; then
        log_success "Service IP: $service_ip"

        # Test health endpoint
        log_info "Testing health endpoint..."
        local health_response
        health_response=$(curl -s -w "%{http_code}" "http://$service_ip:8002/health" -o /tmp/health_response.json)

        if [ "$health_response" = "200" ]; then
            log_success "Health endpoint responding"
            cat /tmp/health_response.json | jq .
        else
            log_warning "Health endpoint returned: $health_response"
        fi
    else
        log_warning "Service IP not yet available (still provisioning)"
    fi
}

# Show deployment info
show_deployment_info() {
    log_info "Deployment Information:"
    echo "Namespace: $NAMESPACE"
    echo "Release Name: $RELEASE_NAME"
    echo "Chart Name: $CHART_NAME"

    # Get service IP
    local service_ip
    service_ip=$(kubectl get service jailbreak-distilbert-v2 -n "$NAMESPACE" -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "Pending")

    echo "Service IP: $service_ip"
    echo "Service Port: 8002"
    echo "Metrics Port: 9090"
    echo ""

    echo "API Usage:"
    echo "curl -X POST http://$service_ip:8002/validate \\"
    echo "  -H 'Content-Type: application/json' \\"
    echo "  -H 'x-api-key: supersecret123' \\"
    echo "  -d '{\"text\": \"Your test text here\"}'"
    echo ""

    echo "Health Check:"
    echo "curl http://$service_ip:8002/health"
    echo ""

    echo "Metrics:"
    echo "curl http://$service_ip:9090/metrics"
    echo ""

    echo "Management Commands:"
    echo "# View pods: kubectl get pods -l app=jailbreak-distilbert -n $NAMESPACE"
    echo "# View logs: kubectl logs -f deployment/jailbreak-distilbert-v2 -n $NAMESPACE"
    echo "# Scale: kubectl scale deployment jailbreak-distilbert-v2 --replicas=3 -n $NAMESPACE"
}

# Cleanup function
cleanup() {
    log_info "Cleaning up temporary files..."
    rm -f /tmp/health_response.json
}

# Main execution
main() {
    log_info "Starting production jailbreak detection deployment..."
    log_info "Optimized model with 97.6% accuracy"

    check_prerequisites
    create_namespace

    if [ "$USE_HELM" = true ]; then
        deploy_helm
    else
        deploy_yaml
    fi

    verify_deployment
    show_deployment_info

    # Set up trap for cleanup
    trap cleanup EXIT

    log_success "🚀 Deployment completed successfully!"
    log_success "Your optimized jailbreak detection service is now running!"
}

# Handle script interruption
trap 'log_warning "Deployment interrupted"; exit 1' INT

# Run main function
main "$@"