#!/bin/bash

# Script to build and push PII service Docker image to Azure Container Registry
# This script is meant to be run in Azure DevOps or from Azure Cloud Shell
# to avoid memory issues on local machines

set -e  # Exit on any error

# Configuration - adjust these values for your environment
ACR_NAME="zgridregistry94f5525a"  # ACR names must be globally unique and 5-50 alphanumeric characters
IMAGE_NAME="pii-service-yavar"
IMAGE_TAG="latest"

# Azure storage configuration
AZURE_STORAGE_ACCOUNT="zagentstoragedev94f5525a"
AZURE_BLOB_CONTAINER="z-grid-storage-blob"

echo "Building PII service Docker image for Azure Container Registry..."

# Login to Azure Container Registry
echo "Logging into Azure Container Registry..."
az acr login --name $ACR_NAME

if [ $? -ne 0 ]; then
    echo "Failed to log into Azure Container Registry. Please ensure you're authenticated with Azure CLI."
    exit 1
fi

# Build and tag the image
ACR_REGISTRY="${ACR_NAME}.azurecr.io"
FULL_IMAGE_NAME="${ACR_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"

echo "Building Docker image: ${FULL_IMAGE_NAME}"
az acr build --registry $ACR_NAME --image $FULL_IMAGE_NAME --file ./pii_service/Dockerfile .

if [ $? -ne 0 ]; then
    echo "Failed to build Docker image in Azure Container Registry."
    exit 1
fi

echo "Successfully built and pushed PII service to ACR: ${FULL_IMAGE_NAME}"

# Verify the image exists
echo "Verifying image in ACR..."
az acr repository show --name $ACR_NAME --image $IMAGE_NAME:$IMAGE_TAG

echo "PII service Docker image successfully built and pushed to Azure Container Registry!"
echo "Image: ${FULL_IMAGE_NAME}"