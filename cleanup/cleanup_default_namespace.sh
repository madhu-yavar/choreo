#!/bin/bash

# Clean up all Z-grid services from default namespace

echo "=== Cleaning up Z-grid LoadBalancer services from default namespace ==="

LOADBALANCER_SERVICES=(
    "ban-service-yavar"
    "bias-service-yavar"
    "format-service-yavar"
    "gibberish-service-yavar"
    "jail-service-yavar"
    "pii-service-yavar"
    "secrets-service-yavar"
    "simple-bias-service"
    "tox-service-yavar"
)

for service in "${LOADBALANCER_SERVICES[@]}"; do
    echo "Deleting LoadBalancer service: $service"
    kubectl delete service $service -n default --ignore-not-found=true
    if [ $? -eq 0 ]; then
        echo "✅ Successfully deleted $service"
    else
        echo "❌ Failed to delete $service or service not found"
    fi
done

echo ""
echo "=== Cleaning up remaining Z-grid services from default namespace ==="

CLUSTERIP_SERVICES=(
    "config-service-yavar"
    "z-agent-app"
    "z-agent-web-service"
)

for service in "${CLUSTERIP_SERVICES[@]}"; do
    echo "Deleting ClusterIP service: $service"
    kubectl delete service $service -n default --ignore-not-found=true
    if [ $? -eq 0 ]; then
        echo "✅ Successfully deleted $service"
    else
        echo "❌ Failed to delete $service or service not found"
    fi
done

echo ""
echo "=== Cleaning up Z-grid deployments from default namespace ==="

DEPLOYMENTS=(
    "ban-service-yavar-deployment"
    "bias-service-yavar-deployment"
    "config-service-yavar-deployment"
    "format-service-yavar-deployment"
    "gibberish-service-enhanced-deployment"
    "jail-service-yavar-deployment"
    "pii-service-configmap-deployment"
    "pii-service-yavar-deployment"
    "secrets-service-yavar-deployment"
    "simple-bias-service-deployment"
    "tox-service-yavar-deployment"
    "z-agent-app"
    "z-agent-auth"
    "z-agent-web"
)

for deployment in "${DEPLOYMENTS[@]}"; do
    echo "Deleting deployment: $deployment"
    kubectl delete deployment $deployment -n default --ignore-not-found=true
    if [ $? -eq 0 ]; then
        echo "✅ Successfully deleted $deployment"
    else
        echo "❌ Failed to delete $deployment or deployment not found"
    fi
done

echo ""
echo "=== Cleanup completed! ==="