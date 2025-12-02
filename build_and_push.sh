#!/bin/bash

# Exit on any error
set -e

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Define variables
ACR_NAME="zinfradevv1"
ACR_REGISTRY="${ACR_NAME}.azurecr.io"
IMAGE_TAG="latest"  # Consider using a more specific tag like GIT_COMMIT or SEMVER
PLATFORM="linux/amd64"  # Specify the platform architecture

# Function to build and push a service
build_and_push() {
  local SERVICE_NAME=$1
  local DOCKERFILE_PATH=$2
  local CONTEXT_PATH=$3
  local IMAGE_NAME="${ACR_REGISTRY}/zgrid-${SERVICE_NAME}:${IMAGE_TAG}"

  echo "Building ${SERVICE_NAME} service for ${PLATFORM}..."
  docker build --platform ${PLATFORM} -t ${IMAGE_NAME} -f ${DOCKERFILE_PATH} ${CONTEXT_PATH}

  echo "Pushing ${SERVICE_NAME} service to ${ACR_REGISTRY}..."
  docker push ${IMAGE_NAME}

  echo "Completed ${SERVICE_NAME} service deployment."
}

# Login to ACR (assuming you have az cli installed and logged in)
echo "Logging into Azure Container Registry..."
az acr login --name ${ACR_NAME}

# Build and push PII service
build_and_push "pii" "${PROJECT_DIR}/pii_service/Dockerfile" "${PROJECT_DIR}/pii_service"

# Build and push Toxicity service
build_and_push "tox" "${PROJECT_DIR}/tox_service/Dockerfile" "${PROJECT_DIR}/tox_service"

# Build and push Jailbreak service
build_and_push "jail" "${PROJECT_DIR}/jail_service/Dockerfile" "${PROJECT_DIR}/jail_service"

# Build and push Policy service
build_and_push "policy" "${PROJECT_DIR}/policy_service/Dockerfile" "${PROJECT_DIR}/policy_service"

# Build and push Ban service
build_and_push "ban" "${PROJECT_DIR}/ban_service/Dockerfile" "${PROJECT_DIR}/ban_service"

# Build and push Secrets service
build_and_push "secrets" "${PROJECT_DIR}/secrets_service/Dockerfile" "${PROJECT_DIR}/secrets_service"

echo "All services built and pushed successfully!"