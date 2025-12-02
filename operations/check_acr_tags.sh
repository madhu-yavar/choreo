#!/bin/bash
# Check what tags are available in ACR and fix deployment files

echo "🔍 Checking available ACR tags..."
echo "=================================="

# List all repositories in ACR
echo "Available repositories in zinfradevv1.azurecr.io:"
az acr repository list --name zinfradevv1 --output table 2>/dev/null || echo "Cannot list ACR repositories (permissions issue)"

# Check specific repositories
repositories=("zgrid-pii" "zgrid-tox" "ban-service" "format-service" "secrets-service" "config-service" "gibberish-service" "gateway-service")

for repo in "${repositories[@]}"; do
    echo ""
    echo "=== $repo ==="
    az acr repository show-tags --name zinfradevv1 --repository "$repo" --output table 2>/dev/null || echo "Cannot access $repo tags"
done

echo ""
echo "📝 Recommended fixes based on available tags:"
echo "================================================"

# Based on available patterns, suggest fixes
echo "1. Ban service likely uses 'latest' tag instead of 'clean-v1'"
echo "2. Some services may need tag adjustments"
echo "3. Update deployment files to use correct tags"