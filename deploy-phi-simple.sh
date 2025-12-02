#!/bin/bash

# Simple Azure Phi Service Deployment
set -e

echo "🚀 Deploying Azure Phi Service"

# Configuration
RESOURCE_GROUP="z-grid-dev"
AKS_CLUSTER="z-girid-dev"
NAMESPACE="phi-service"

echo "📋 Using existing AKS cluster: $AKS_CLUSTER"

# Get AKS credentials
echo "🔑 Getting AKS credentials..."
az aks get-credentials \
    --resource-group "$RESOURCE_GROUP" \
    --name "$AKS_CLUSTER" \
    --overwrite-existing

# Check current nodes
echo "🖥️ Current cluster nodes:"
kubectl get nodes -o wide

# Clean up existing Phi service deployment
echo "🧹 Cleaning up existing Phi service..."
kubectl delete deployment phi-service-azure -n phi-service --ignore-not-found=true
kubectl delete service phi-service-azure -n phi-service --ignore-not-found=true

# Create updated deployment without node affinity for now
echo "🚀 Deploying Phi service..."
kubectl apply -f deploy/k8s/phi-service-azure-dedicated.yaml -n phi-service

# Wait for deployment
echo "⏳ Waiting for deployment..."
kubectl rollout status deployment/phi-service-azure -n "$NAMESPACE" --timeout=600s

# Get deployment status
echo "📊 Deployment Status:"
kubectl get pods -n phi-service -o wide
kubectl get svc -n phi-service

echo ""
echo "🔗 Phi service endpoints:"
SERVICE_IP=$(kubectl get svc phi-service-azure -n phi-service -o jsonpath='{.spec.clusterIP}' 2>/dev/null || echo "")
if [ ! -z "$SERVICE_IP" ]; then
    echo "  Internal: http://$SERVICE_IP:8009"
    echo "  Health: http://$SERVICE_IP:8009/health"
    echo "  Model Status: http://$SERVICE_IP:8009/model/status"
fi

echo ""
echo "🎉 Phi service deployment completed!"