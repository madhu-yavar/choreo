#!/usr/bin/env bash

# Enhanced PII Service Deployment Script
# This script pushes the enhanced Docker image to Azure Container Registry and updates the Kubernetes deployment

set -euo pipefail

# Configuration
ACR_NAME="zinfradevv1.azurecr.io"
IMAGE_NAME="zgrid-pii"
IMAGE_TAG="enhanced-20241022-1430"
FULL_IMAGE_NAME="${ACR_NAME}/${IMAGE_NAME}:${IMAGE_TAG}"
NAMESPACE="z-grid"

echo "🚀 Enhanced PII Service Deployment"
echo "=================================="
echo "ACR: ${ACR_NAME}"
echo "Image: ${FULL_IMAGE_NAME}"
echo "Namespace: ${NAMESPACE}"
echo ""

# Step 1: Login to Azure Container Registry
echo "Step 1: Login to Azure Container Registry"
echo "----------------------------------------"
echo "Please run the following command to login to ACR:"
echo "az acr login --name ${ACR_NAME%%.*}"
echo ""

read -p "Press Enter after you've successfully logged into ACR..."

# Step 2: Push the Docker image to ACR
echo "Step 2: Push Docker image to ACR"
echo "--------------------------------"
echo "Pushing ${FULL_IMAGE_NAME}..."

docker push "${FULL_IMAGE_NAME}"

echo "✅ Docker image pushed successfully!"
echo ""

# Step 3: Update Kubernetes deployment
echo "Step 3: Update Kubernetes deployment"
echo "------------------------------------"
echo "Updating PII service deployment..."

kubectl apply -f deploy/k8s/pii-service-deployment.yaml -n "${NAMESPACE}"

echo "✅ Kubernetes deployment updated!"
echo ""

# Step 4: Watch the deployment rollout
echo "Step 4: Monitor deployment rollout"
echo "----------------------------------"
echo "Waiting for deployment to complete..."

kubectl rollout status deployment/poi-service-yavar-deployment -n "${NAMESPACE}" --timeout=300s

echo "✅ Deployment completed successfully!"
echo ""

# Step 5: Verify the service is working
echo "Step 5: Verify service health"
echo "----------------------------"
echo "Checking service health endpoint..."

# Get the external IP
EXTERNAL_IP=$(kubectl get service pii-service-yavar -n "${NAMESPACE}" -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

if [ -n "${EXTERNAL_IP}" ]; then
    echo "Service is accessible at: http://${EXTERNAL_IP}:8000"
    echo "Testing health endpoint..."

    # Wait a moment for the service to be ready
    sleep 10

    if curl -f "http://${EXTERNAL_IP}:8000/health"; then
        echo "✅ Service health check passed!"
    else
        echo "⚠️  Service health check failed - please check the pod logs"
    fi
else
    echo "⚠️  External IP not yet assigned. Please check service status with:"
    echo "kubectl get service pii-service-yavar -n ${NAMESPACE}"
fi

echo ""
echo "🎉 Enhanced PII Service Deployment Complete!"
echo "The service now supports the following enhanced entity types:"
echo "- Organizations"
echo "- IP Addresses"
echo "- MAC Addresses"
echo "- Bank Accounts"
echo "- Bank Routing Numbers"
echo "- US Driver Licenses"
echo "- US Passports"
echo "- IN Aadhaar numbers"
echo "- IN PAN numbers"
echo ""
echo "All with proper thresholds and placeholders configured."