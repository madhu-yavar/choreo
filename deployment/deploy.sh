#!/bin/bash

# Production Deployment Script for LlamaGuard Hybrid Service
# ==========================================================
# This script automates the deployment of the LlamaGuard Hybrid Service
# with 95% accuracy + 100% coverage zero-failure architecture

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_NAME="llamaguard-hybrid"
NAMESPACE="z-grid"
SERVICE_NAME="llamaguard-hybrid-service"
DEPLOYMENT_NAME="llamaguard-hybrid-production"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

# Help function
show_help() {
    cat << EOF
LlamaGuard Hybrid Service Deployment Script

Usage: $0 [OPTIONS] COMMAND

Commands:
    local           Deploy locally with Docker Compose
    kubernetes      Deploy to Kubernetes cluster
    validate        Run production validation tests
    status          Check deployment status
    logs            Show service logs
    cleanup         Clean up deployment
    help            Show this help message

Options:
    --host          Service host (default: localhost)
    --port          Service port (default: 8003)
    --namespace     Kubernetes namespace (default: z-grid)
    --skip-validation Skip validation tests
    --verbose       Enable verbose logging
    --dry-run       Show what would be done without executing

Examples:
    $0 local                    # Deploy locally with Docker
    $0 kubernetes               # Deploy to Kubernetes
    $0 validate --host prod.example.com  # Validate production deployment
    $0 status                   # Check deployment status
    $0 logs --namespace prod    # Show logs from production namespace

EOF
}

# Parse command line arguments
VERBOSE=false
DRY_RUN=false
SKIP_VALIDATION=false
SERVICE_HOST="localhost"
SERVICE_PORT="8003"

while [[ $# -gt 0 ]]; do
    case $1 in
        --host)
            SERVICE_HOST="$2"
            shift 2
            ;;
        --port)
            SERVICE_PORT="$2"
            shift 2
            ;;
        --namespace)
            NAMESPACE="$2"
            shift 2
            ;;
        --skip-validation)
            SKIP_VALIDATION=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        local|kubernetes|validate|status|logs|cleanup|help)
            COMMAND="$1"
            shift
            ;;
        *)
            log_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Set command if not provided
if [[ -z "${COMMAND:-}" ]]; then
    log_error "No command specified"
    show_help
    exit 1
fi

# Show help
if [[ "$COMMAND" == "help" ]]; then
    show_help
    exit 0
fi

# Execute command with dry run support
execute() {
    local cmd="$1"
    local description="${2:-$cmd}"

    if [[ "$VERBOSE" == true ]]; then
        log_info "Executing: $description"
    fi

    if [[ "$DRY_RUN" == true ]]; then
        log_info "[DRY RUN] Would execute: $cmd"
        return 0
    fi

    if [[ "$VERBOSE" == true ]]; then
        log_info "Running: $cmd"
        eval "$cmd"
    else
        eval "$cmd" > /dev/null 2>&1
    fi
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check if script is run from correct directory
    if [[ ! -f "$SCRIPT_DIR/production_llamaguard_hybrid.py" ]]; then
        log_error "production_llamaguard_hybrid.py not found in script directory"
        exit 1
    fi

    # Check Docker for local deployment
    if [[ "$COMMAND" == "local" ]]; then
        if ! command -v docker &> /dev/null; then
            log_error "Docker is not installed or not in PATH"
            exit 1
        fi

        if ! command -v docker-compose &> /dev/null; then
            log_error "Docker Compose is not installed or not in PATH"
            exit 1
        fi

        # Check if Docker is running
        if ! docker info &> /dev/null; then
            log_error "Docker is not running"
            exit 1
        fi
    fi

    # Check kubectl for Kubernetes deployment
    if [[ "$COMMAND" == "kubernetes" ]]; then
        if ! command -v kubectl &> /dev/null; then
            log_error "kubectl is not installed or not in PATH"
            exit 1
        fi

        # Check if cluster is accessible
        if ! kubectl cluster-info &> /dev/null; then
            log_error "Kubernetes cluster is not accessible"
            exit 1
        fi
    fi

    # Check Python for validation
    if [[ "$COMMAND" == "validate" ]] || [[ "$SKIP_VALIDATION" == false ]]; then
        if ! command -v python3 &> /dev/null; then
            log_error "Python 3 is not installed or not in PATH"
            exit 1
        fi
    fi

    log_success "Prerequisites check passed"
}

# Deploy locally with Docker Compose
deploy_local() {
    log_info "Deploying LlamaGuard Hybrid Service locally..."

    # Check if model file exists
    if [[ ! -f "$SCRIPT_DIR/models/llamaguard-7b.Q4_0.gguf" ]]; then
        log_warning "Model file not found. Please download the model to models/llamaguard-7b.Q4_0.gguf"
        log_info "Model download URL: https://huggingface.co/TheBloke/LlamaGuard-7B-GGUF/resolve/main/llamaguard-7b.Q4_K_M.gguf"

        if [[ "$DRY_RUN" == false ]]; then
            read -p "Do you want to download the model now? (y/N): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                log_info "Downloading model (3.6GB)..."
                mkdir -p "$SCRIPT_DIR/models"
                execute "wget -O $SCRIPT_DIR/models/llamaguard-7b.Q4_0.gguf https://huggingface.co/TheBloke/LlamaGuard-7B-GGUF/resolve/main/llamaguard-7b.Q4_K_M.gguf" "Download LlamaGuard model"
            else
                log_error "Model file is required for deployment"
                exit 1
            fi
        fi
    fi

    # Build and start services
    log_info "Building Docker image..."
    execute "docker-compose -f $SCRIPT_DIR/docker-compose-llamaguard-hybrid.yml build" "Build Docker image"

    log_info "Starting services..."
    execute "docker-compose -f $SCRIPT_DIR/docker-compose-llamaguard-hybrid.yml up -d" "Start services"

    # Wait for service to be ready
    log_info "Waiting for service to be ready..."
    local max_attempts=30
    local attempt=0

    while [[ $attempt -lt $max_attempts ]]; do
        if curl -s "http://localhost:8003/health" &> /dev/null; then
            log_success "Service is ready!"
            break
        fi

        attempt=$((attempt + 1))
        log_info "Attempt $attempt/$max_attempts..."
        sleep 5
    done

    if [[ $attempt -eq $max_attempts ]]; then
        log_error "Service failed to start within expected time"
        exit 1
    fi

    log_success "Local deployment completed successfully!"
    log_info "Service is available at: http://localhost:8003"
    log_info "Grafana dashboard: http://localhost:3001 (admin/llamaguard2024)"
}

# Deploy to Kubernetes
deploy_kubernetes() {
    log_info "Deploying LlamaGuard Hybrid Service to Kubernetes..."

    # Create namespace if it doesn't exist
    log_info "Creating namespace..."
    execute "kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -" "Create namespace"

    # Check if model PVC exists and has model
    log_info "Checking model storage..."
    local pvc_exists=$(kubectl get pvc llamaguard-models-pvc -n $NAMESPACE --no-headers 2>/dev/null | wc -l)

    if [[ $pvc_exists -eq 0 ]]; then
        log_info "Creating PVC for model storage..."
        execute "kubectl apply -f $SCRIPT_DIR/k8s-llamaguard-hybrid-deployment.yaml" "Create PVC and deployment"

        log_warning "Please upload the LlamaGuard model to the PVC manually"
        log_info "Model should be placed at: /app/models/llamaguard-7b.Q4_0.gguf"
    else
        log_info "PVC already exists, applying deployment..."
        execute "kubectl apply -f $SCRIPT_DIR/k8s-llamaguard-hybrid-deployment.yaml" "Apply Kubernetes manifests"
    fi

    # Wait for deployment to be ready
    log_info "Waiting for deployment to be ready..."
    execute "kubectl rollout status deployment/$DEPLOYMENT_NAME -n $NAMESPACE --timeout=300s" "Wait for deployment"

    # Check service status
    log_info "Checking service status..."
    local service_ready=$(kubectl get svc $SERVICE_NAME -n $NAMESPACE --no-headers 2>/dev/null | wc -l)

    if [[ $service_ready -gt 0 ]]; then
        log_success "Kubernetes deployment completed successfully!"
        log_info "Service is available at: kubectl port-forward svc/$SERVICE_NAME 8003:8003 -n $NAMESPACE"
    else
        log_error "Service deployment failed"
        exit 1
    fi
}

# Run validation tests
run_validation() {
    log_info "Running production validation tests..."

    # Wait a moment for service to be fully ready
    sleep 5

    # Run validation
    if [[ "$DRY_RUN" == true ]]; then
        log_info "[DRY RUN] Would run: python3 $SCRIPT_DIR/production_validation_tests.py --host $SERVICE_HOST --port $SERVICE_PORT --comprehensive"
        return 0
    fi

    log_info "Executing comprehensive validation..."
    if python3 "$SCRIPT_DIR/production_validation_tests.py" --host "$SERVICE_HOST" --port "$SERVICE_PORT" --comprehensive; then
        log_success "All validation tests passed! Service is production-ready."
    else
        log_error "Validation tests failed. Please check the deployment."
        exit 1
    fi
}

# Check deployment status
check_status() {
    log_info "Checking deployment status..."

    if command -v kubectl &> /dev/null && kubectl cluster-info &> /dev/null; then
        # Kubernetes status
        log_info "Kubernetes deployment status:"

        # Check pods
        log_info "Pods:"
        kubectl get pods -n $NAMESPACE -l app=llamaguard-hybrid

        # Check services
        log_info "Services:"
        kubectl get svc -n $NAMESPACE -l app=llamaguard-hybrid

        # Check HPA if exists
        local hpa_exists=$(kubectl get hpa llamaguard-hybrid-hpa -n $NAMESPACE --no-headers 2>/dev/null | wc -l)
        if [[ $hpa_exists -gt 0 ]]; then
            log_info "Horizontal Pod Autoscaler:"
            kubectl get hpa llamaguard-hybrid-hpa -n $NAMESPACE
        fi

    else
        # Local Docker status
        log_info "Local Docker deployment status:"
        execute "docker-compose -f $SCRIPT_DIR/docker-compose-llamaguard-hybrid.yml ps" "Check Docker services"
    fi

    # Health check
    log_info "Service health check:"
    if curl -s "http://$SERVICE_HOST:$SERVICE_PORT/health" &> /dev/null; then
        local health_data=$(curl -s "http://$SERVICE_HOST:$SERVICE_PORT/health")
        log_success "Service is healthy"
        if [[ "$VERBOSE" == true ]]; then
            echo "$health_data" | jq . 2>/dev/null || echo "$health_data"
        fi
    else
        log_error "Service health check failed"
    fi
}

# Show logs
show_logs() {
    log_info "Showing service logs..."

    if command -v kubectl &> /dev/null && kubectl cluster-info &> /dev/null; then
        # Kubernetes logs
        execute "kubectl logs -n $NAMESPACE -l app=llamaguard-hybrid -f --tail=50" "Show Kubernetes logs"
    else
        # Docker logs
        execute "docker-compose -f $SCRIPT_DIR/docker-compose-llamaguard-hybrid.yml logs -f --tail=50" "Show Docker logs"
    fi
}

# Clean up deployment
cleanup_deployment() {
    log_info "Cleaning up deployment..."

    if command -v kubectl &> /dev/null && kubectl cluster-info &> /dev/null; then
        # Kubernetes cleanup
        log_info "Cleaning up Kubernetes deployment..."
        execute "kubectl delete -f $SCRIPT_DIR/k8s-llamaguard-hybrid-deployment.yaml -n $NAMESPACE --ignore-not-found=true" "Delete Kubernetes resources"
    else
        # Docker cleanup
        log_info "Cleaning up Docker deployment..."
        execute "docker-compose -f $SCRIPT_DIR/docker-compose-llamaguard-hybrid.yml down -v" "Stop and remove Docker services"
        execute "docker-compose -f $SCRIPT_DIR/docker-compose-llamaguard-hybrid.yml rm -f" "Remove Docker containers"
    fi

    log_success "Cleanup completed"
}

# Main execution
main() {
    log_info "LlamaGuard Hybrid Service Deployment Script"
    log_info "=========================================="

    case "$COMMAND" in
        local)
            check_prerequisites
            deploy_local
            if [[ "$SKIP_VALIDATION" == false ]]; then
                run_validation
            fi
            ;;
        kubernetes)
            check_prerequisites
            deploy_kubernetes
            if [[ "$SKIP_VALIDATION" == false ]]; then
                run_validation
            fi
            ;;
        validate)
            check_prerequisites
            run_validation
            ;;
        status)
            check_status
            ;;
        logs)
            show_logs
            ;;
        cleanup)
            cleanup_deployment
            ;;
        *)
            log_error "Unknown command: $COMMAND"
            show_help
            exit 1
            ;;
    esac

    log_success "Operation completed successfully!"
}

# Trap for cleanup on exit
trap 'log_info "Script interrupted"; exit 130' INT TERM

# Run main function
main "$@"