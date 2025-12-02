#!/bin/bash

# Config Service Deployment Script for Z-Grid

set -e

echo "🚀 Deploying Z-Grid Config Service..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    print_error "kubectl is not installed or not in PATH"
    exit 1
fi

# Set namespace
NAMESPACE="z-grid"
print_status "Using namespace: $NAMESPACE"

# Create namespace if it doesn't exist
kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -

# Check if secrets file exists
SECRETS_FILE="../deploy/k8s/config-service-secrets.yaml"
if [[ ! -f "$SECRETS_FILE" ]]; then
    print_error "Secrets file not found: $SECRETS_FILE"
    exit 1
fi

# Check if secrets have been updated (check for placeholder)
if grep -q "<BASE64_ENCODED" "$SECRETS_FILE"; then
    print_warning "Secrets file contains placeholder values. Please update them with actual encoded values."
    print_warning "You can encode values using: echo -n 'your-value' | base64"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Apply secrets
print_status "Applying config service secrets..."
kubectl apply -f "$SECRETS_FILE" -n $NAMESPACE

# Apply deployment
print_status "Applying config service deployment..."
kubectl apply -f "../deploy/k8s/config-service-deployment.yaml" -n $NAMESPACE

# Wait for deployment to be ready
print_status "Waiting for deployment to be ready..."
kubectl rollout status deployment/config-service-yavar-deployment -n $NAMESPACE --timeout=300s

# Get service status
print_status "Checking service status..."
kubectl get pods -l app=config-service-yavar -n $NAMESPACE

# Get service URL
SERVICE_URL=$(kubectl get service config-service-yavar -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "localhost:8009")
if [[ "$SERVICE_URL" == "localhost:8009" ]]; then
    print_warning "LoadBalancer IP not available. Use port-forwarding for local access:"
    print_warning "kubectl port-forward service/config-service-yavar 8009:8009 -n $NAMESPACE"
else
    print_status "Service is available at: http://$SERVICE_URL:8009"
fi

# Health check
print_status "Performing health check..."
sleep 10
if kubectl exec -n $NAMESPACE deployment/config-service-yavar-deployment -- curl -f http://localhost:8009/health &>/dev/null; then
    print_status "✅ Health check passed!"
else
    print_warning "⚠️  Health check failed. Check pod logs with: kubectl logs -l app=config-service-yavar -n $NAMESPACE"
fi

echo "🎉 Config service deployment completed!"
echo ""
echo "Next steps:"
echo "1. Update secrets with your actual API keys if you haven't already"
echo "2. Test the API endpoints"
echo "3. Configure your applications to use the config service"
echo ""
echo "Useful commands:"
echo "- View logs: kubectl logs -l app=config-service-yavar -n $NAMESPACE -f"
echo "- Port forward: kubectl port-forward service/config-service-yavar 8009:8009 -n $NAMESPACE"
echo "- Scale deployment: kubectl scale deployment config-service-yavar-deployment --replicas=2 -n $NAMESPACE"