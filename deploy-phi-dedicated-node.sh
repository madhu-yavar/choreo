#!/bin/bash

# Azure Phi Service Deployment with Dedicated Node Pool
set -e

echo "🚀 Deploying Azure Phi Service with Dedicated Node Pool"

# Configuration
RESOURCE_GROUP=${RESOURCE_GROUP:-"z-grid-dev"}
AKS_CLUSTER=${AKS_CLUSTER:-"z-girid-dev"}
NODE_POOL_NAME=${NODE_POOL_NAME:-"phi-pool"}
NODE_COUNT=${NODE_COUNT:-1}
NODE_SIZE=${NODE_SIZE:-"Standard_D4s_v3"}
NAMESPACE=${NAMESPACE:-"phi-service"}

echo "📋 Configuration:"
echo "  Resource Group: $RESOURCE_GROUP"
echo "  AKS Cluster: $AKS_CLUSTER"
echo "  Node Pool: $NODE_POOL_NAME"
echo "  Node Count: $NODE_COUNT"
echo "  Node Size: $NODE_SIZE"
echo "  Namespace: $NAMESPACE"

# Check Azure CLI
if ! command -v az &> /dev/null; then
    echo "❌ Azure CLI not found. Please install it first."
    exit 1
fi

# Check kubectl
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl not found. Please install it first."
    exit 1
fi

# Azure login check
echo "🔐 Checking Azure authentication..."
if ! az account show &> /dev/null; then
    echo "Please login to Azure..."
    az login
fi

# Get AKS credentials
echo "🔑 Getting AKS credentials..."
az aks get-credentials \
    --resource-group "$RESOURCE_GROUP" \
    --name "$AKS_CLUSTER" \
    --overwrite-existing

# Create dedicated node pool for Phi service
echo "🏗️ Creating dedicated node pool for Phi service..."
az aks nodepool add \
    --resource-group "$RESOURCE_GROUP" \
    --cluster-name "$AKS_CLUSTER" \
    --name "$NODE_POOL_NAME" \
    --node-count "$NODE_COUNT" \
    --node-vm-size "$NODE_SIZE" \
    --node-taints "phi-service=dedicated:NoSchedule" \
    --mode User \
    --max-pods 30 \
    --os-sku Linux \
    --enable-cluster-autoscaler \
    --min-count 1 \
    --max-count 3 \
    --only-show-errors

echo "✅ Dedicated node pool '$NODE_POOL_NAME' created successfully"

# Wait for node pool to be ready
echo "⏳ Waiting for node pool nodes to be ready..."
az aks nodepool list \
    --resource-group "$RESOURCE_GROUP" \
    --cluster-name "$AKS_CLUSTER" \
    --query "[?name=='$NODE_POOL_NAME'].{name:name,provisioningState:provisioningState}" \
    --output table

# Wait for nodes to be ready
echo "🔄 Checking node status..."
kubectl wait --for=condition=Ready nodes -l "phi-service=dedicated" --timeout=600s

echo "✅ Dedicated nodes are ready"

# Create namespace if it doesn't exist
echo "📂 Ensuring namespace exists..."
kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -

# Apply configurations
echo "🔧 Applying Phi service configurations..."
kubectl apply -f deploy/k8s/phi-service-azure-configmap.yaml -n "$NAMESPACE"
kubectl apply -f deploy/k8s/phi-service-azure-secrets-simple.yaml -n "$NAMESPACE"

# Deploy the Phi service to dedicated node pool
echo "🚀 Deploying Phi service to dedicated node pool..."
kubectl apply -f deploy/k8s/phi-service-azure-dedicated.yaml -n "$NAMESPACE"

# Wait for deployment
echo "⏳ Waiting for Phi service deployment..."
kubectl rollout status deployment/phi-service-azure -n "$NAMESPACE" --timeout=600s

# Get service details
echo "📊 Deployment Status:"
kubectl get pods -n "$NAMESPACE" -o wide
kubectl get svc -n "$NAMESPACE"
kubectl get hpa -n "$NAMESPACE"

# Get node information
echo ""
echo "🖥️ Dedicated Node Pool Status:"
kubectl get nodes -l "phi-service=dedicated" -o wide

echo ""
echo "🔗 Service Endpoints:"
CLUSTER_IP=$(kubectl get svc phi-service-azure -n "$NAMESPACE" -o jsonpath='{.spec.clusterIP}')
if [ ! -z "$CLUSTER_IP" ]; then
    echo "  Internal Service: http://$CLUSTER_IP:8009"
    echo "  Health Check: http://$CLUSTER_IP:8009/health"
    echo "  Model Status: http://$CLUSTER_IP:8009/model/status"
    echo "  Detailed Health: http://$CLUSTER_IP:8009/health/detailed"
fi

# Test connection
echo ""
echo "🧪 Testing Phi service connectivity..."
sleep 30  # Wait for pod startup
kubectl port-forward svc/phi-service-azure 8009:8009 -n "$NAMESPACE" &
PORT_FORWARD_PID=$!

sleep 10
if curl -s http://localhost:8009/health > /dev/null 2>&1; then
    echo "✅ Phi service is responding correctly!"
    curl -s http://localhost:8009/health | jq . 2>/dev/null || curl -s http://localhost:8009/health
else
    echo "⚠️ Phi service not ready yet, but deployment was successful"
fi

# Clean up
kill $PORT_FORWARD_PID 2>/dev/null || true

echo ""
echo "✅ Phi service deployment completed successfully!"
echo ""
echo "📋 Next Steps:"
echo "1. Monitor logs: kubectl logs -f deployment/phi-service-azure -n $NAMESPACE"
echo "2. Test endpoints: curl http://<pod-ip>:8009/health/detailed"
echo "3. Scale as needed: kubectl scale deployment phi-service-azure --replicas=2 -n $NAMESPACE"
echo "4. Monitor resources: kubectl top pods -n $NAMESPACE"

echo ""
echo "🎉 Phi service is running on dedicated nodes with resource isolation!"