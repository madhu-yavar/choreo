#!/bin/bash

# LlamaGuard Hybrid v2.0.0 Kubernetes Deployment Script
# Deploys policy-service-llamaguard-hybrid-v2 to z-grid namespace

set -e

# Configuration
NAMESPACE="z-grid"
DEPLOYMENT_NAME="policy-service-llamaguard-hybrid-v2"
SERVICE_NAME="policy-service-llamaguard-hybrid-v2"
ACR_IMAGE="zinfradevv1.azurecr.io/llamaguard-hybrid:v2.0.0"

echo "🚀 Deploying LlamaGuard Hybrid v2.0.0 to Kubernetes..."
echo "Namespace: $NAMESPACE"
echo "Deployment: $DEPLOYMENT_NAME"
echo "Image: $ACR_IMAGE"
echo ""

# Check if namespace exists
if ! kubectl get namespace $NAMESPACE > /dev/null 2>&1; then
    echo "❌ Namespace $NAMESPACE does not exist. Please create it first."
    exit 1
fi

# Check if ACR secret exists
if ! kubectl get secret acr-secret -n $NAMESPACE > /dev/null 2>&1; then
    echo "⚠️ ACR secret not found. Creating it..."
    kubectl create secret docker-registry acr-secret \
        --docker-server=zinfradevv1.azurecr.io \
        --docker-username=zinfradevv1 \
        --docker-password=$(az acr login --name zinfradevv1 --expose-token --query accessToken -o tsv) \
        --namespace $NAMESPACE
    echo "✅ ACR secret created"
fi

echo "📦 Applying manifests..."

# Apply service first
echo "🔗 Creating service..."
kubectl apply -f service.yaml

# Apply network policy
echo "🛡️ Creating network policy..."
kubectl apply -f network-policy.yaml

# Apply deployment
echo "🚀 Creating deployment..."
kubectl apply -f deployment.yaml

echo ""
echo "✅ Deployment manifests applied successfully!"
echo ""

# Wait for deployment to be ready
echo "⏳ Waiting for deployment to be ready (this may take 2-3 minutes)..."
kubectl wait --for=condition=available --timeout=300s deployment/$DEPLOYMENT_NAME -n $NAMESPACE

echo ""
echo "🎉 Deployment completed successfully!"
echo ""

# Show deployment status
echo "📊 Deployment status:"
kubectl get pods -n $NAMESPACE -l app=policy-service-llamaguard-hybrid-v2

echo ""
echo "🌐 Service details:"
kubectl get service $SERVICE_NAME -n $NAMESPACE

echo ""
echo "🔍 To check logs:"
echo "kubectl logs -n $NAMESPACE -l app=policy-service-llamaguard-hybrid-v2 -f"

echo ""
echo "🧪 To test the service (through gateway):"
echo "curl -X POST http://<gateway-url>/policy/check \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -H 'X-API-Key: supersecret123' \\"
echo "  -d '{\"user_prompt\": \"What is the capital of France?\"}'"

echo ""
echo "✅ LlamaGuard Hybrid v2.0.0 is ready!"