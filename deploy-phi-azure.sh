#!/bin/bash

# Azure Phi Service Deployment Script
set -e

echo "☁️ Deploying Phi Service to Azure Kubernetes Service"

# Configuration
RESOURCE_GROUP=${RESOURCE_GROUP:-"z-grid-rg"}
AKS_CLUSTER=${AKS_CLUSTER:-"z-grid-aks"}
ACR_NAME=${ACR_NAME:-"zgridacr"}
IMAGE_TAG=${IMAGE_TAG:-"latest"}
NAMESPACE=${NAMESPACE:-"phi-service"}

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    echo "❌ Azure CLI not found. Please install it first."
    exit 1
fi

# Check if kubectl is installed
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl not found. Please install it first."
    exit 1
fi

# Login to Azure (interactive if needed)
echo "🔐 Checking Azure authentication..."
if ! az account show &> /dev/null; then
    echo "Please login to Azure..."
    az login
fi

# Set subscription if provided
if [ ! -z "$SUBSCRIPTION_ID" ]; then
    echo "📝 Setting subscription: $SUBSCRIPTION_ID"
    az account set --subscription "$SUBSCRIPTION_ID"
fi

# Create resource group if it doesn't exist
echo "🏗️ Ensuring resource group exists..."
az group create \
    --name "$RESOURCE_GROUP" \
    --location "${LOCATION:-eastus}" \
    --only-show-errors \
    --output none

# Create ACR if it doesn't exist
echo "📦 Ensuring Azure Container Registry exists..."
az acr create \
    --resource-group "$RESOURCE_GROUP" \
    --name "$ACR_NAME" \
    --sku "${ACR_SKU:-Standard}" \
    --only-show-errors \
    --output none

# Create AKS if it doesn't exist
echo "☸️ Ensuring AKS cluster exists..."
az aks create \
    --resource-group "$RESOURCE_GROUP" \
    --name "$AKS_CLUSTER" \
    --node-count "${NODE_COUNT:-3}" \
    --node-vm-size "${NODE_SIZE:-Standard_D4s_v3}" \
    --enable-cluster-autoscaler \
    --min-count 1 \
    --max-count 5 \
    --generate-ssh-keys \
    --attach-acr "$ACR_NAME" \
    --only-show-errors \
    --output none || echo "AKS cluster might already exist"

# Get AKS credentials
echo "🔑 Getting AKS credentials..."
az aks get-credentials \
    --resource-group "$RESOURCE_GROUP" \
    --name "$AKS_CLUSTER" \
    --overwrite-existing

# Build and push Docker image
echo "🐳 Building Docker image..."
cd "$(dirname "$0")/.."
docker build -t phi-service-azure:$IMAGE_TAG ./services/phi_service

echo "📤 Pushing to Azure Container Registry..."
docker tag phi-service-azure:$IMAGE_TAG "$ACR_NAME.azurecr.io/phi-service-azure:$IMAGE_TAG"
az acr login --name "$ACR_NAME"
docker push "$ACR_NAME.azurecr.io/phi-service-azure:$IMAGE_TAG"

# Create namespace
echo "📂 Creating namespace: $NAMESPACE"
kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -

# Update deployment with ACR image
echo "🔧 Updating deployment configuration..."
sed -i.bak "s|image: phi-service-azure:latest|image: $ACR_NAME.azurecr.io/phi-service-azure:$IMAGE_TAG|g" deploy/k8s/phi-service-azure-deployment.yaml

# Apply Kubernetes configurations
echo "☸️ Applying Kubernetes configurations..."
kubectl apply -f deploy/k8s/phi-service-azure-configmap.yaml -n "$NAMESPACE"
kubectl apply -f deploy/k8s/phi-service-azure-secrets.yaml -n "$NAMESPACE"
kubectl apply -f deploy/k8s/phi-service-azure-deployment.yaml -n "$NAMESPACE"
kubectl apply -f deploy/k8s/phi-service-azure-service-monitor.yaml -n "$NAMESPACE"

# Wait for deployment
echo "⏳ Waiting for deployment to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/phi-service-azure -n "$NAMESPACE"

# Get service URL
echo "🔗 Getting service details..."
kubectl get pods,svc,hpa -n "$NAMESPACE"

# Get external IP (if using LoadBalancer)
if kubectl get svc phi-service-azure -n "$NAMESPACE" -o jsonpath='{.spec.type}' | grep -q "LoadBalancer"; then
    echo "⏳ Waiting for external IP..."
    kubectl wait --for=condition=ready --timeout=300s svc/phi-service-azure -n "$NAMESPACE"
    EXTERNAL_IP=$(kubectl get svc phi-service-azure -n "$NAMESPACE" -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
    echo "🌐 Service available at: http://$EXTERNAL_IP:8009"
else
    echo "🔗 Service available internally at: http://phi-service-azure.$NAMESPACE.svc.cluster.local:8009"
fi

echo "✅ Phi Service deployed successfully to Azure!"
echo "📊 To monitor: kubectl logs -f deployment/phi-service-azure -n $NAMESPACE"
echo "🧪 To test: kubectl port-forward svc/phi-service-azure 8009:8009 -n $NAMESPACE"

# Cleanup backup file
rm -f deploy/k8s/phi-service-azure-deployment.yaml.bak