#!/bin/bash

# Build script for enhanced toxicity service with ML models
set -e

echo "🚀 Building Enhanced Toxicity Service with ML Models"
echo "=================================================="

# Configuration
ACR_REGISTRY="zinfradevv1.azurecr.io"
IMAGE_NAME="zgrid-tox"
IMAGE_TAG="enhanced-ml-v2.1.0"

# Function to check if docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        echo "❌ Docker is not running. Please start Docker Desktop."
        echo "💡 Alternative: Use cloud build service if Docker unavailable"
        exit 1
    fi
    echo "✅ Docker is running"
}

# Function to build and push image
build_and_push() {
    echo "🏗️  Building enhanced toxicity service image..."

    # Build the image
    docker build \
        -f Dockerfile.enhanced \
        -t ${ACR_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG} \
        -t ${ACR_REGISTRY}/${IMAGE_NAME}:latest-enhanced \
        .

    if [ $? -eq 0 ]; then
        echo "✅ Docker build successful"
    else
        echo "❌ Docker build failed"
        exit 1
    fi

    # Push to ACR
    echo "📤 Pushing to Azure Container Registry..."
    docker push ${ACR_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}

    if [ $? -eq 0 ]; then
        echo "✅ Image pushed successfully"
    else
        echo "❌ Image push failed"
        exit 1
    fi

    docker push ${ACR_REGISTRY}/${IMAGE_NAME}:latest-enhanced
}

# Function to verify image in registry
verify_image() {
    echo "🔍 Verifying image in registry..."
    az acr repository show-tags \
        --name zinfradevv1 \
        --repository ${IMAGE_NAME} \
        --output table | grep ${IMAGE_TAG}

    if [ $? -eq 0 ]; then
        echo "✅ Image verified in ACR"
    else
        echo "❌ Image not found in ACR"
        exit 1
    fi
}

# Main execution
echo "🔍 Checking prerequisites..."
check_docker

echo "🏗️  Starting build process..."
build_and_push

echo "🔍 Verifying deployment..."
verify_image

echo ""
echo "🎉 Enhanced Toxicity Service Build Complete!"
echo "=============================================="
echo "✅ Image: ${ACR_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"
echo "✅ Status: Successfully built and pushed to ACR"
echo "✅ Ready for Kubernetes deployment"
echo ""
echo "🚀 Next Steps:"
echo "1. Update Kubernetes deployment:"
echo "   kubectl set image deployment/tox-service-yavar-v2 \\"
echo "     tox-service-yavar-v2=${ACR_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"
echo ""
echo "2. Verify deployment:"
echo "   kubectl rollout status deployment/tox-service-yavar-v2"
echo ""
echo "3. Test enhanced features via port-forward"