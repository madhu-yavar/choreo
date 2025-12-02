#!/bin/bash

# Enhanced Toxicity Service Deployment Script
# Deploys enhanced toxicity service to Azure Kubernetes

set -e

# Configuration
ACR_REGISTRY="zinfradevv1.azurecr.io"
IMAGE_NAME="zgrid-tox"
VERSION="enhanced-v2.0.0"
NAMESPACE="z-grid"

echo "🚀 Starting Enhanced Toxicity Service Deployment"
echo "=========================================="

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    echo "❌ Azure CLI not found. Please install Azure CLI first."
    exit 1
fi

# Check if kubectl is installed
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl not found. Please install kubectl first."
    exit 1
fi

# Login to Azure Container Registry
echo "🔐 Logging into Azure Container Registry..."
az acr login --name zinfradevv1

# Build and push Docker image
echo "🏗️  Building enhanced Docker image..."
cd "$(dirname "$0")/../tox_service"

docker buildx build --platform linux/amd64 \
  -f Dockerfile.enhanced \
  -t ${ACR_REGISTRY}/${IMAGE_NAME}:${VERSION} \
  -t ${ACR_REGISTRY}/${IMAGE_NAME}:latest-enhanced \
  --push .

echo "✅ Docker image built and pushed successfully"

# Switch to correct namespace
echo "🔄 Switching to Kubernetes namespace: ${NAMESPACE}"
kubectl config set-context --current --namespace=${NAMESPACE}

# Deploy enhanced service
echo "☸️  Deploying enhanced toxicity service to Kubernetes..."
cd "$(dirname "$0")/.."
kubectl apply -f deploy/k8s/tox-service-enhanced-deployment.yaml

# Wait for deployment to be ready
echo "⏳ Waiting for deployment to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/tox-service-yavar-enhanced

# Verify deployment
echo "✅ Verifying deployment..."
kubectl get pods -l app=tox-service-yavar-enhanced
kubectl get services -l app=tox-service-yavar-enhanced

# Test the service
echo "🧪 Testing enhanced service..."
SERVICE_IP=$(kubectl get service tox-service-yavar-enhanced -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
if [ -n "$SERVICE_IP" ]; then
    echo "🌐 Testing service at IP: $SERVICE_IP"
    curl -f -X GET "http://$SERVICE_IP:8001/health" || {
        echo "❌ Health check failed"
        exit 1
    }
    echo "✅ Health check passed"
else
    echo "⚠️  Service IP not available yet, checking internal connectivity..."
    kubectl port-forward service/tox-service-yavar-enhanced 8001:8001 &
    PF_PID=$!
    sleep 5
    curl -f -X GET "http://localhost:8001/health" || {
        echo "❌ Health check failed"
        kill $PF_PID 2>/dev/null
        exit 1
    }
    echo "✅ Health check passed"
    kill $PF_PID 2>/dev/null
fi

echo ""
echo "🎉 Enhanced Toxicity Service Deployment Complete!"
echo "=========================================="
echo "Service Name: tox-service-yavar-enhanced"
echo "Image: ${ACR_REGISTRY}/${IMAGE_NAME}:${VERSION}"
echo "Enhanced Features:"
echo "  ✅ Pattern-based toxicity detection"
echo "  ✅ Context-aware processing"
echo "  ✅ Multilingual profanity support"
echo "  ✅ Disguised toxicity detection"
echo "  ✅ Hybrid ML + rule-based approach"
echo ""
echo "Next Steps:"
echo "1. Update gateway configuration to use enhanced service"
echo "2. Run integration tests"
echo "3. Monitor performance metrics"