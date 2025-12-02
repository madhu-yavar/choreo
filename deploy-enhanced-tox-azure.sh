#!/bin/bash

# Enhanced Toxicity Service Azure Deployment Script with ML Models
# Deploys the enhanced toxicity service with pre-bundled Detoxify ML models

set -e

# Configuration
ACR_REGISTRY="zinfradevv1.azurecr.io"
IMAGE_NAME="zgrid-tox"
IMAGE_TAG="enhanced-ml-v2.1.0"
NAMESPACE="z-grid"

echo "🚀 Enhanced Toxicity Service Azure Deployment with ML Models"
echo "=========================================================="

# Check prerequisites
echo "🔍 Checking prerequisites..."

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

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install it first."
    exit 1
fi

echo "✅ All prerequisites found"

# Check Azure login
echo "🔐 Checking Azure authentication..."
if ! az account show &> /dev/null; then
    echo "❌ Not logged in to Azure. Please run 'az login' first."
    exit 1
fi

echo "✅ Azure authentication verified"

# Switch to correct namespace
echo "📦 Switching to namespace: $NAMESPACE"
kubectl config set-context --current --namespace=$NAMESPACE

# Build the enhanced Docker image with ML models
echo "🏗️  Building enhanced toxicity service image with ML models..."
cd "$(dirname "$0")/.."

# Create build context directory
BUILD_DIR="build_context_enhanced_ml"
rm -rf $BUILD_DIR
mkdir -p $BUILD_DIR

# Copy necessary files to build context
cp tox_service/Dockerfile.enhanced $BUILD_DIR/
cp tox_service/requirements.enhanced.txt $BUILD_DIR/
cp tox_service/enhanced_app.py $BUILD_DIR/
cp tox_service/enhanced_toxicity_model.py $BUILD_DIR/
cp tox_service/enhanced_profanity.py $BUILD_DIR/
cp tox_service/utils.py $BUILD_DIR/
cp tox_service/init_ml_models.py $BUILD_DIR/

echo "📦 Build context prepared"

# Build the image with platform support for Azure
echo "🔨 Building Docker image: $ACR_REGISTRY/$IMAGE_NAME:$IMAGE_TAG"
docker buildx build --platform linux/amd64 \
  -f $BUILD_DIR/Dockerfile.enhanced \
  -t $ACR_REGISTRY/$IMAGE_NAME:$IMAGE_TAG \
  -t $ACR_REGISTRY/$IMAGE_NAME:latest-enhanced-ml \
  --push \
  $BUILD_DIR/

if [ $? -eq 0 ]; then
    echo "✅ Docker image built and pushed successfully"
else
    echo "❌ Docker build failed"
    exit 1
fi

# Clean up build context
rm -rf $BUILD_DIR

# Update the enhanced Kubernetes deployment file
echo "📝 Updating Kubernetes deployment configuration..."
cat > deploy/k8s/tox-service-enhanced-ml-deployment.yaml << 'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: tox-service-yavar-enhanced-ml
  labels:
    app: tox-service-yavar-enhanced-ml
    version: enhanced-ml-v2.1.0
spec:
  replicas: 2
  selector:
    matchLabels:
      app: tox-service-yavar-enhanced-ml
  template:
    metadata:
      labels:
        app: tox-service-yavar-enhanced-ml
        version: enhanced-ml-v2.1.0
    spec:
      containers:
      - name: tox-service-yavar-enhanced-ml
        image: zinfradevv1.azurecr.io/zgrid-tox:enhanced-ml-v2.1.0
        ports:
        - containerPort: 8001
        env:
        # Enhanced Detection Features
        - name: ENHANCED_DETECTION
          value: "true"
        - name: CONTEXT_AWARE_DETECTION
          value: "true"
        - name: PATTERN_BASED_DETECTION
          value: "true"
        - name: MULTILINGUAL_SUPPORT
          value: "true"
        - name: SEVERITY_CLASSIFICATION
          value: "true"

        # ML Model Configuration
        - name: DETOXIFY_MODEL
          value: "unbiased"
        - name: DETOXIFY_THRESHOLD
          value: "0.3"
        - name: ML_MODEL_CACHE_DIR
          value: "/app/models"

        # API Configuration
        - name: API_KEYS
          value: "supersecret123"
        - name: LOG_LEVEL
          value: "INFO"

        # Performance Tuning
        - name: MAX_REQUEST_SIZE
          value: "1048576"  # 1MB
        - name: REQUEST_TIMEOUT
          value: "180"

        resources:
          requests:
            memory: "2Gi"     # Increased for ML models
            cpu: "1000m"      # 1 CPU core
          limits:
            memory: "4Gi"     # Higher limit for ML processing
            cpu: "2000m"      # 2 CPU cores

        # Health checks with longer startup time for ML models
        livenessProbe:
          httpGet:
            path: /health
            port: 8001
          initialDelaySeconds: 120    # Extended for ML model loading
          periodSeconds: 30
          timeoutSeconds: 15
          failureThreshold: 3

        readinessProbe:
          httpGet:
            path: /health
            port: 8001
          initialDelaySeconds: 90     # Extended for ML model loading
          periodSeconds: 10
          timeoutSeconds: 10
          failureThreshold: 3

        # Volume for ML model cache (persistent across restarts)
        volumeMounts:
        - name: model-cache
          mountPath: /app/models
          subPath: cache

      volumes:
      - name: model-cache
        persistentVolumeClaim:
          claimName: tox-model-cache-pvc

      imagePullSecrets:
      - name: acr-secret

---
apiVersion: v1
kind: Service
metadata:
  name: tox-service-yavar-enhanced-ml
  labels:
    app: tox-service-yavar-enhanced-ml
spec:
  selector:
    app: tox-service-yavar-enhanced-ml
  ports:
    - protocol: TCP
      port: 8001
      targetPort: 8001
  type: ClusterIP

---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: tox-model-cache-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 5Gi  # Space for ML model cache
  storageClassName: default
EOF

echo "✅ Kubernetes deployment configuration updated"

# Create PVC for model cache if it doesn't exist
echo "💾 Creating persistent volume claim for model cache..."
kubectl apply -f - << 'EOF'
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: tox-model-cache-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 5Gi
  storageClassName: default
EOF

# Deploy to Kubernetes
echo "🚀 Deploying enhanced toxicity service with ML models to Kubernetes..."
kubectl apply -f deploy/k8s/tox-service-enhanced-ml-deployment.yaml

# Wait for deployment to be ready
echo "⏳ Waiting for deployment to be ready (this may take a few minutes for ML models to load)..."
kubectl wait --for=condition=available --timeout=600s deployment/tox-service-yavar-enhanced-ml

if [ $? -eq 0 ]; then
    echo "✅ Deployment successful!"
else
    echo "❌ Deployment failed or timed out"
    echo "📋 Checking deployment status..."
    kubectl get deployment tox-service-yavar-enhanced-ml
    echo "📋 Checking pod status..."
    kubectl get pods -l app=tox-service-yavar-enhanced-ml
    exit 1
fi

# Verify the deployment
echo "🔍 Verifying deployment..."
kubectl get pods -l app=tox-service-yavar-enhanced-ml
kubectl get services | grep tox-service-yavar-enhanced-ml

# Test the service
echo "🧪 Testing enhanced toxicity service with ML models..."
SERVICE_IP=$(kubectl get service tox-service-yavar-enhanced-ml -o jsonpath='{.spec.clusterIP}')

if [ -n "$SERVICE_IP" ]; then
    echo "🏥 Testing health endpoint..."
    kubectl run test-pod --image=curlimages/curl --rm -i --restart=Never -- \
        curl -f -H "X-API-Key: supersecret123" \
        http://$SERVICE_IP:8001/health

    echo "📊 Testing stats endpoint..."
    kubectl run test-pod --image=curlimages/curl --rm -i --restart=Never -- \
        curl -f -H "X-API-Key: supersecret123" \
        http://$SERVICE_IP:8001/stats

    echo "🧪 Testing enhanced validation with ML..."
    kubectl run test-pod --image=curlimages/curl --rm -i --restart=Never -- \
        curl -X POST -H "Content-Type: application/json" \
        -H "X-API-Key: supersecret123" \
        -d '{
            "text": "You are a fucking idiot and should go to hell",
            "enhanced_detection": true,
            "context_aware": true,
            "return_spans": true
        }' \
        http://$SERVICE_IP:8001/validate
else
    echo "⚠️  Could not get service IP for testing"
fi

# Update gateway to point to enhanced ML service
echo "🔗 Updating gateway to use enhanced ML toxicity service..."
kubectl patch deployment gateway-service -p '{"spec":{"template":{"spec":{"containers":[{"name":"gateway-service","env":[{"name":"TOXICITY_SERVICE_URL","value":"http://tox-service-yavar-enhanced-ml:8001/validate"}]}]}}}}'

echo "🔄 Restarting gateway to use enhanced toxicity service..."
kubectl rollout restart deployment gateway-service

# Wait for gateway to be ready
echo "⏳ Waiting for gateway to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/gateway-service

echo ""
echo "🎉 Enhanced Toxicity Service Deployment Complete!"
echo "================================================="
echo "✅ Features Deployed:"
echo "   - Hybrid ML + Pattern-Based Detection"
echo "   - Pre-bundled Detoxify ML Models"
echo "   - Context-Aware Processing"
echo "   - Multilingual Profanity Detection"
echo "   - Enhanced Pattern Matching"
echo "   - Persistent Model Cache"
echo ""
echo "📊 Service Details:"
echo "   - Service: tox-service-yavar-enhanced-ml"
echo "   - Image: $ACR_REGISTRY/$IMAGE_NAME:$IMAGE_TAG"
echo "   - Namespace: $NAMESPACE"
echo "   - Gateway Integration: ✅ Updated"
echo ""
echo "🧪 To test the service:"
echo "   kubectl port-forward service/tox-service-yavar-enhanced-ml 8001:8001"
echo "   curl -X POST http://localhost:8001/validate \\"
echo "     -H \"Content-Type: application/json\" \\"
echo "     -H \"X-API-Key: supersecret123\" \\"
echo "     -d '{\"text\": \"test content\", \"enhanced_detection\": true}'"
echo ""
echo "📈 To check logs:"
echo "   kubectl logs -f deployment/tox-service-yavar-enhanced-ml"