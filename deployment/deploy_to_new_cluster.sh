#!/bin/bash
# Deploy Z-Grid to new z-grid-dev cluster

set -e

echo "🚀 Deploying Z-Grid to new cluster"
echo "=================================="

# Wait for cluster to be available
echo "Checking for z-grid-dev cluster..."
for i in {1..30}; do
    if az aks list --query "[?name=='z-grid-dev'] | length(@)" -o tsv 2>/dev/null | grep -q "1"; then
        echo "✅ Found z-grid-dev cluster!"
        break
    fi
    echo "Waiting for cluster to be available... ($i/30)"
    sleep 10
done

# Find the resource group
echo "Finding resource group..."
RG=$(az aks list --query "[?name=='z-grid-dev'].resourceGroup" -o tsv)
if [ -z "$RG" ]; then
    echo "❌ Could not find resource group for z-grid-dev cluster"
    echo "Please check the cluster name and try again"
    exit 1
fi

echo "✅ Found cluster in resource group: $RG"

# Get credentials
echo "Getting cluster credentials..."
az aks get-credentials --resource-group "$RG" --name "z-grid-dev" --overwrite

# Test connection
echo "Testing cluster connection..."
kubectl get nodes
if [ $? -ne 0 ]; then
    echo "❌ Cannot connect to cluster"
    exit 1
fi

echo "✅ Connected to cluster successfully!"

# Create namespace
echo "Creating z-grid namespace..."
kubectl create namespace z-grid --dry-run=client -o yaml | kubectl apply -f -

# Deploy services
echo "Deploying Z-Grid services..."
services=(
    "deploy/k8s/pii-service-deployment.yaml"
    "deploy/k8s/tox-service-deployment.yaml"
    "deploy/k8s/jail-service-deployment.yaml"
    "deploy/k8s/secrets-service-deployment.yaml"
    "deploy/k8s/format-service-deployment.yaml"
    "deploy/k8s/gibberish-service-deployment.yaml"
    "deploy/k8s/ban-service-deployment.yaml"
    "deploy/k8s/bias-service-deployment.yaml"
    "deploy/k8s/config-service-deployment.yaml"
    "working-gateway-service.yaml"
)

for service in "${services[@]}"; do
    if [ -f "$service" ]; then
        echo "Deploying $service..."
        kubectl apply -f "$service" -n z-grid
    else
        echo "⚠️  Service file not found: $service"
    fi
done

# Deploy SSL certificate
echo "Deploying SSL certificate..."
kubectl apply -f k8s/wildcard-ssl-certificate.yaml -n z-grid

# Deploy ingress
echo "Deploying ingress configuration..."
kubectl apply -f k8s/complete-zgrid-ingress-fix.yaml

# Wait for pods to be ready
echo "Waiting for pods to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment --all -n z-grid || true

# Show status
echo ""
echo "=================================================================="
echo "📊 Deployment Status"
echo "=================================================================="
echo "Services:"
kubectl get services -n z-grid
echo ""
echo "Pods:"
kubectl get pods -n z-grid
echo ""
echo "Ingress:"
kubectl get ingress -n z-grid

echo ""
echo "🎯 Testing connectivity..."
sleep 30

# Test main gateway
echo "Testing gateway..."
if curl -k -s -o /dev/null -w "%{http_code}" \
    -H "X-API-Key: supersecret123" \
    "https://zgrid-gateway.20.242.183.197.nip.io/health" | grep -q "200"; then
    echo "✅ Gateway is accessible!"
else
    echo "⚠️  Gateway not yet accessible (this may take a few more minutes)"
fi

echo ""
echo "🌐 Your services will be accessible at:"
echo "  • Main Gateway: https://zgrid-gateway.20.242.183.197.nip.io"
echo "  • PII Service:   https://pii.20.242.183.197.nip.io"
echo "  • Toxicity:      https://tox.20.242.183.197.nip.io"
echo "  • Policy:        https://policy.20.242.183.197.nip.io"
echo "  • API Gateway:   https://api.20.242.183.197.nip.io/pii"
echo ""

echo "✅ Deployment complete! Run ./quick_connectivity_test.sh to test all services."