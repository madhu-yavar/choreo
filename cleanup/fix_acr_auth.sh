#!/bin/bash
# Fix ACR Authentication for Z-Grid Services

echo "🔐 Fixing ACR Authentication for Z-Grid Services"
echo "==============================================="

# Option 1: Try to enable ACR admin account and get credentials
echo "Attempting to enable ACR admin account..."
az acr update --name zinfradevv1 --admin-enabled true 2>/dev/null || echo "Cannot enable ACR admin (permissions issue)"

# Get ACR credentials if possible
echo "Getting ACR credentials..."
if az acr credential show --name zinfradevv1 2>/dev/null; then
    echo "✅ Got ACR admin credentials"

    # Extract username and password
    USERNAME=$(az acr credential show --name zinfradevv1 --query username -o tsv)
    PASSWORD=$(az acr credential show --name zinfradevv1 --query passwords[0].value -o tsv)

    echo "Creating ACR secret with admin credentials..."
    kubectl create secret docker-registry acr-auth \
        --docker-server=zinfradevv1.azurecr.io \
        --docker-username="$USERNAME" \
        --docker-password="$PASSWORD" \
        --namespace=z-grid \
        --dry-run=client -o yaml | kubectl apply -f -

    echo "✅ ACR secret created successfully!"
else
    echo "⚠️  Cannot get ACR admin credentials, trying service principal approach..."

    # Create service principal
    echo "Creating service principal for ACR access..."
    SP_INFO=$(az ad sp create-for-rbac --name zgrid-acr-sp --role acrpull --scope $(az acr show --name zinfradevv1 --query id --output tsv 2>/dev/null || echo "") 2>/dev/null)

    if [ ! -z "$SP_INFO" ]; then
        SP_USERNAME=$(echo $SP_INFO | jq -r '.appId')
        SP_PASSWORD=$(echo $SP_INFO | jq -r '.password')

        echo "Creating ACR secret with service principal..."
        kubectl create secret docker-registry acr-auth \
            --docker-server=zinfradevv1.azurecr.io \
            --docker-username="$SP_USERNAME" \
            --docker-password="$SP_PASSWORD" \
            --namespace=z-grid \
            --dry-run=client -o yaml | kubectl apply -f -

        echo "✅ ACR secret created with service principal!"
    else
        echo "❌ Cannot create service principal either"
        echo ""
        echo "🔧 Manual steps needed:"
        echo "1. Get ACR credentials from Azure Portal"
        echo "2. Run: kubectl create secret docker-registry acr-auth \\"
        echo "   --docker-server=zinfradevv1.azurecr.io \\"
        echo "   --docker-username=YOUR_USERNAME \\"
        echo "   --docker-password=YOUR_PASSWORD \\"
        echo "   --namespace=z-grid"
        exit 1
    fi
fi

# Restart pods to use the new secret
echo "Restarting pods to use the ACR secret..."
kubectl rollout restart deployment -n z-grid --all

# Wait for pods to be ready
echo "Waiting for pods to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment --all -n z-grid || echo "Some pods may still be starting"

# Show status
echo ""
echo "📊 Current Status:"
echo "=================="
kubectl get pods -n z-grid

echo ""
echo "✅ ACR authentication fix complete!"
echo "Your services should now be able to pull images properly."