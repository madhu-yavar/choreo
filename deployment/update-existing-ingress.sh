#!/bin/bash

# Update existing ingress resources to point to z-grid services

echo "Updating bias-service-ingress to point to z-grid service..."
kubectl patch ingress bias-service-ingress -n default --type='json' -p='[{"op":"replace","path":"/spec/rules/0/http/paths/0/backend/service/name","value":"bias-service-yavar.z-grid"}]'

if [ $? -eq 0 ]; then
    echo "✅ Updated bias-service-ingress"
else
    echo "❌ Failed to update bias-service-ingress"
fi

echo "Checking other existing ingresses that might need updates..."

# Check if there are other service ingresses that need updating
INGRESS_SERVICES=("working-bias-service-ingress")

for ingress in "${INGRESS_SERVICES[@]}"; do
    if kubectl get ingress $ingress -n default >/dev/null 2>&1; then
        echo "Found ingress: $ingress"
        # Check what service it points to
        SERVICE_NAME=$(kubectl get ingress $ingress -n default -o jsonpath='{.spec.rules[0].http.paths[0].backend.service.name}')
        echo "  Currently points to: $SERVICE_NAME"

        # Update to point to z-grid namespace
        kubectl patch ingress $ingress -n default --type='json' -p="[{'op':'replace','path':'/spec/rules/0/http/paths/0/backend/service/name','value':'${SERVICE_NAME}.z-grid'}]"

        if [ $? -eq 0 ]; then
            echo "  ✅ Updated $ingress"
        else
            echo "  ❌ Failed to update $ingress"
        fi
    fi
done

echo "Ingress updates completed!"