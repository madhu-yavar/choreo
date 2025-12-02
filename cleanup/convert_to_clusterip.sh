#!/bin/bash

# Script to convert LoadBalancer services to ClusterIP to save costs

# Services to convert in z-grid namespace (excluding gateway)
SERVICES=(
    "ban-service-yavar"
    "bias-service-yavar"
    "format-service-yavar"
    "gibberish-service-yavar"
    "jail-service-yavar"
    "pii-enhanced-service"
    "pii-service-yavar"
    "policy-service-external"
    "secrets-service-yavar"
    "simple-bias-service"
    "tox-service-yavar"
)

echo "Converting LoadBalancer services to ClusterIP in z-grid namespace..."

for service in "${SERVICES[@]}"; do
    echo "Converting $service to ClusterIP..."

    # Patch service to change from LoadBalancer to ClusterIP
    kubectl patch service $service -n z-grid -p '{"spec":{"type":"ClusterIP"}}'

    if [ $? -eq 0 ]; then
        echo "✅ Successfully converted $service to ClusterIP"
    else
        echo "❌ Failed to convert $service"
    fi
done

echo "LoadBalancer to ClusterIP conversion completed!"