#!/bin/bash

# Comprehensive cleanup script for all previous jailbreak configurations
# Removes old deployments, services, configmaps, and other resources

set -e

# Configuration
NAMESPACE="z-grid"

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

    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed or not in PATH"
        exit 1
    fi

    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot access Kubernetes cluster"
        exit 1
    fi

    log_success "Prerequisites check passed"
}

# List all jailbreak resources
list_jailbreak_resources() {
    log_info "Current jailbreak resources in namespace '$NAMESPACE':"
    echo ""

    # Pods
    local pods=$(kubectl get pods -n "$NAMESPACE" -o jsonpath='{.items[*].metadata.name}' | xargs -n1 | grep jailbreak || true)
    if [ -n "$pods" ]; then
        echo "📦 Pods:"
        kubectl get pods -n "$NAMESPACE" | grep jailbreak || echo "  No jailbreak pods found"
        echo ""
    fi

    # Services
    echo "🌐 Services:"
    kubectl get services -n "$NAMESPACE" | grep jailbreak || echo "  No jailbreak services found"
    echo ""

    # Deployments
    echo "🚀 Deployments:"
    kubectl get deployments -n "$NAMESPACE" | grep jailbreak || echo "  No jailbreak deployments found"
    echo ""

    # ConfigMaps
    echo "⚙️  ConfigMaps:"
    kubectl get configmaps -n "$NAMESPACE" | grep jailbreak || echo "  No jailbreak configmaps found"
    echo ""

    # Secrets
    echo "🔒 Secrets:"
    kubectl get secrets -n "$NAMESPACE" | grep jailbreak || echo "  No jailbreak secrets found"
    echo ""

    # PVCs
    echo "💾 PVCs:"
    kubectl get pvc -n "$NAMESPACE" | grep jailbreak || echo "  No jailbreak PVCs found"
    echo ""

    # Jobs
    echo "🏗️  Jobs:"
    kubectl get jobs -n "$NAMESPACE" | grep jailbreak || echo "  No jailbreak jobs found"
    echo ""
}

# Delete jailbreak deployments
delete_deployments() {
    log_info "Deleting jailbreak deployments..."

    local deployments=$(kubectl get deployments -n "$NAMESPACE" -o jsonpath='{.items[*].metadata.name}' | xargs -n1 | grep jailbreak || true)

    if [ -n "$deployments" ]; then
        for deployment in $deployments; do
            log_info "Deleting deployment: $deployment"
            kubectl delete deployment "$deployment" -n "$NAMESPACE" --ignore-not-found=true
        done
        log_success "Deployments deleted"
    else
        log_warning "No jailbreak deployments found"
    fi
}

# Delete jailbreak services
delete_services() {
    log_info "Deleting jailbreak services..."

    local services=$(kubectl get services -n "$NAMESPACE" -o jsonpath='{.items[*].metadata.name}' | xargs -n1 | grep jailbreak || true)

    if [ -n "$services" ]; then
        for service in $services; do
            log_info "Deleting service: $service"
            kubectl delete service "$service" -n "$NAMESPACE" --ignore-not-found=true
        done
        log_success "Services deleted"
    else
        log_warning "No jailbreak services found"
    fi
}

# Delete jailbreak pods
delete_pods() {
    log_info "Deleting jailbreak pods..."

    local pods=$(kubectl get pods -n "$NAMESPACE" -o jsonpath='{.items[*].metadata.name}' | xargs -n1 | grep jailbreak || true)

    if [ -n "$pods" ]; then
        for pod in $pods; do
            log_info "Deleting pod: $pod"
            kubectl delete pod "$pod" -n "$NAMESPACE" --ignore-not-found=true --force --grace-period=0
        done
        log_success "Pods deleted"
    else
        log_warning "No jailbreak pods found"
    fi
}

# Delete jailbreak configmaps
delete_configmaps() {
    log_info "Deleting jailbreak configmaps..."

    local configmaps=$(kubectl get configmaps -n "$NAMESPACE" -o jsonpath='{.items[*].metadata.name}' | xargs -n1 | grep jailbreak || true)

    if [ -n "$configmaps" ]; then
        for configmap in $configmaps; do
            log_info "Deleting configmap: $configmap"
            kubectl delete configmap "$configmap" -n "$NAMESPACE" --ignore-not-found=true
        done
        log_success "ConfigMaps deleted"
    else
        log_warning "No jailbreak configmaps found"
    fi
}

# Delete jailbreak secrets
delete_secrets() {
    log_info "Deleting jailbreak secrets..."

    local secrets=$(kubectl get secrets -n "$NAMESPACE" -o jsonpath='{.items[*].metadata.name}' | xargs -n1 | grep jailbreak || true)

    if [ -n "$secrets" ]; then
        for secret in $secrets; do
            log_info "Deleting secret: $secret"
            kubectl delete secret "$secret" -n "$NAMESPACE" --ignore-not-found=true
        done
        log_success "Secrets deleted"
    else
        log_warning "No jailbreak secrets found"
    fi
}

# Delete jailbreak PVCs
delete_pvcs() {
    log_info "Deleting jailbreak PVCs..."

    local pvcs=$(kubectl get pvc -n "$NAMESPACE" -o jsonpath='{.items[*].metadata.name}' | xargs -n1 | grep jailbreak || true)

    if [ -n "$pvcs" ]; then
        for pvc in $pvcs; do
            log_info "Deleting PVC: $pvc"
            kubectl delete pvc "$pvc" -n "$NAMESPACE" --ignore-not-found=true
        done
        log_success "PVCs deleted"
    else
        log_warning "No jailbreak PVCs found"
    fi
}

# Delete jailbreak jobs
delete_jobs() {
    log_info "Deleting jailbreak jobs..."

    local jobs=$(kubectl get jobs -n "$NAMESPACE" -o jsonpath='{.items[*].metadata.name}' | xargs -n1 | grep jailbreak || true)

    if [ -n "$jobs" ]; then
        for job in $jobs; do
            log_info "Deleting job: $job"
            kubectl delete job "$job" -n "$NAMESPACE" --ignore-not-found=true
        done
        log_success "Jobs deleted"
    else
        log_warning "No jailbreak jobs found"
    fi
}

# Delete any remaining resources by label selector
delete_by_label() {
    log_info "Deleting resources by jailbreak labels..."

    # Delete resources with jailbreak-related labels
    kubectl delete all -n "$NAMESPACE" -l app=jailbreak --ignore-not-found=true
    kubectl delete all -n "$NAMESPACE" -l service-type=jailbreak --ignore-not-found=true
    kubectl delete all -n "$NAMESPACE" -l app.kubernetes.io/name~jailbreak --ignore-not-found=true

    log_success "Labeled resources deleted"
}

# Wait for resource cleanup
wait_for_cleanup() {
    log_info "Waiting for resources to be cleaned up..."

    # Wait for pods to terminate
    local max_wait=60
    local wait_count=0

    while [ $wait_count -lt $max_wait ]; do
        local remaining_pods=$(kubectl get pods -n "$NAMESPACE" -o jsonpath='{.items[*].metadata.name}' | xargs -n1 | grep jailbreak | wc -l || echo 0)

        if [ "$remaining_pods" -eq 0 ]; then
            log_success "All jailbreak pods terminated"
            break
        fi

        log_info "Waiting for $remaining_pods jailbreak pods to terminate... ($wait_count/$max_wait)"
        sleep 5
        wait_count=$((wait_count + 1))
    done

    if [ $wait_count -eq $max_wait ]; then
        log_warning "Timeout waiting for pod cleanup. Some pods may still be terminating."
    fi
}

# Verify cleanup
verify_cleanup() {
    log_info "Verifying cleanup completion..."

    local remaining_resources=0

    # Check for remaining pods
    local pods=$(kubectl get pods -n "$NAMESPACE" -o jsonpath='{.items[*].metadata.name}' | xargs -n1 | grep jailbreak | wc -l || echo 0)
    if [ "$pods" -gt 0 ]; then
        log_warning "Found $pods remaining jailbreak pods"
        remaining_resources=$((remaining_resources + pods))
    fi

    # Check for remaining services
    local services=$(kubectl get services -n "$NAMESPACE" -o jsonpath='{.items[*].metadata.name}' | xargs -n1 | grep jailbreak | wc -l || echo 0)
    if [ "$services" -gt 0 ]; then
        log_warning "Found $services remaining jailbreak services"
        remaining_resources=$((remaining_resources + services))
    fi

    # Check for remaining deployments
    local deployments=$(kubectl get deployments -n "$NAMESPACE" -o jsonpath='{.items[*].metadata.name}' | xargs -n1 | grep jailbreak | wc -l || echo 0)
    if [ "$deployments" -gt 0 ]; then
        log_warning "Found $deployments remaining jailbreak deployments"
        remaining_resources=$((remaining_resources + deployments))
    fi

    if [ $remaining_resources -eq 0 ]; then
        log_success "✅ Cleanup completed successfully! No jailbreak resources remaining."
    else
        log_warning "⚠️  Cleanup completed with $remaining_resources resources remaining."
        log_info "You may need to manually clean up remaining resources."
    fi

    # Show final status
    echo ""
    log_info "Final resource status:"
    kubectl get all -n "$NAMESPACE" | grep jailbreak || echo "  No jailbreak resources found"
}

# Force cleanup (optional)
force_cleanup() {
    if [ "$1" = "--force" ]; then
        log_info "Performing force cleanup..."

        # Force delete all remaining pods
        kubectl delete pods -n "$NAMESPACE" -l app=jailbreak --force --grace-period=0 --ignore-not-found=true
        kubectl delete pods -n "$NAMESPACE" -l service-type=jailbreak --force --grace-period=0 --ignore-not-found=true

        # Force delete all remaining resources
        kubectl delete all,configmaps,secrets,pvc,jobs -n "$NAMESPACE" -l app=jailbreak --force --grace-period=0 --ignore-not-found=true
        kubectl delete all,configmaps,secrets,pvc,jobs -n "$NAMESPACE" -l service-type=jailbreak --force --grace-period=0 --ignore-not-found=true

        log_success "Force cleanup completed"
    fi
}

# Main execution
main() {
    log_info "Starting comprehensive jailbreak cleanup..."
    log_info "Namespace: $NAMESPACE"

    check_prerequisites

    echo ""
    log_info "=== CURRENT JAILBREAK RESOURCES ==="
    list_jailbreak_resources

    echo ""
    read -p "Do you want to proceed with cleanup? (y/N): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Cleanup cancelled by user"
        exit 0
    fi

    echo ""
    log_info "=== STARTING CLEANUP ==="

    # Delete resources in order to avoid dependencies
    delete_deployments
    delete_services
    delete_jobs
    delete_pods
    delete_configmaps
    delete_secrets
    delete_pvcs
    delete_by_label

    # Force cleanup if requested
    force_cleanup "$1"

    # Wait for cleanup to complete
    wait_for_cleanup

    # Verify cleanup
    echo ""
    log_info "=== CLEANUP VERIFICATION ==="
    verify_cleanup

    log_success "🧹 Jailbreak cleanup process completed!"
}

# Handle script interruption
trap 'log_warning "Cleanup interrupted"; exit 1' INT

# Show usage
usage() {
    echo "Usage: $0 [--force]"
    echo ""
    echo "Options:"
    echo "  --force    Force delete all jailbreak resources (use with caution)"
    echo ""
    echo "This script will remove ALL jailbreak-related resources from the '$NAMESPACE' namespace."
    echo "Resources include: deployments, services, pods, configmaps, secrets, PVCs, and jobs."
}

# Check for help flag
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    usage
    exit 0
fi

# Run main function
main "$@"