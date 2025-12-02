# Pure K8s Deployment - No Mac Docker Required!

## Overview
This deployment strategy handles everything in Kubernetes, eliminating Mac/Linux compatibility issues:
- **Init Container**: Downloads PyTorch and dependencies in the cluster
- **ConfigMap**: Contains application code (no local Docker build needed)
- **PVC**: Shared storage for model files
- **EmptyDir**: Shared volume for PyTorch between init and main containers

## 🚀 Quick Start (No Docker Required!)

### Step 1: Set Up Model Files in PVC
```bash
# Run model setup job
kubectl apply -f ../k8s/model-setup-job.yaml -n z-grid

# Wait for job to complete
kubectl get jobs -n z-grid -w

# Get the pod name
POD_NAME=$(kubectl get pods -n z-grid -l job-name=inetuned-model-setup -o jsonpath='{.items[0].metadata.name}')

# Copy your actual model files to the PVC
kubectl cp models/hf_space_efficient/inetuned_gibbrish_model/model.safetensors \
  ${POD_NAME}:/model_volume/inetuned_gibbrish_model/ -n z-grid

kubectl cp models/hf_space_efficient/inetuned_gibbrish_model/tokenizer.json \
  ${POD_NAME}:/model_volume/inetuned_gibbrish_model/ -n z-grid

# Copy any other model files you have
kubectl cp models/hf_space_efficient/inetuned_gibbrish_model/ \
  ${POD_NAME}:/model_volume/inetuned_gibbrish_model/ -n z-grid

# Verify files are copied
kubectl exec ${POD_NAME} -n z-grid -- ls -la /model_volume/inetuned_gibbrish_model/

# Clean up the setup job
kubectl delete job inetuned-model-setup -n z-grid
```

### Step 2: Deploy the Service
```bash
# Deploy the K8s-native service
kubectl apply -f ../k8s/gibberish-service-k8s-native.yaml -n z-grid

# Monitor deployment progress
kubectl get deployments -n z-grid -w
kubectl get pods -n z-grid -l app=gibberish-service-k8s-native -w

# Check logs (watch init container install PyTorch)
kubectl logs -l app=gibberish-service-k8s-native -c pytorch-downloader -n z-grid -f
```

### Step 3: Test the Service
```bash
# Port forward to test locally
kubectl port-forward svc/gibberish-service-k8s-native 8007:8007 -n z-grid

# Test health check
curl http://localhost:8007/health

# Test gibberish detection
curl -X POST http://localhost:8007/detect \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello world"}'

curl -X POST http://localhost:8007/detect \
  -H "Content-Type: application/json" \
  -d '{"text": "asdfghjklqwertyuiop"}'
```

## 🏗️ Architecture

### Init Container (pytorch-downloader)
- Runs first, downloads PyTorch (~1.5GB) to shared volume
- Sets up application code from ConfigMap
- One-time download per deployment

### Main Container (gibberish-service)
- Reuses PyTorch from shared volume (no download needed)
- Loads model from PVC
- Serves API requests

### Shared Storage
- **EmptyDir**: Temporary storage for PyTorch and app code
- **PVC**: Persistent storage for model files

## 📊 Performance Benefits

**vs Traditional Approach:**
- ✅ No Mac/Linux compatibility issues
- ✅ No local Docker building required
- ✅ PyTorch download happens once in cluster
- ✅ Faster subsequent pod restarts (PyTorch in shared volume)
- ✅ Consistent Linux environment

**Expected Performance:**
- **First deployment**: 3-5 minutes (PyTorch download in init container)
- **Subsequent deployments**: 1-2 minutes (PyTorch already in PVC)
- **Pod restart**: 30-60 seconds
- **Memory usage**: 2-3GB (vs 4-5GB with per-pod downloads)

## 🔧 Configuration Options

### Custom PyTorch Version
Edit the init container command in `gibberish-service-k8s-native.yaml`:
```yaml
command: ["/bin/bash", "-c"]
args:
- |
  pip install --no-cache-dir torch==2.1.0 transformers==4.35.0
```

### Adjust Resource Limits
```yaml
resources:
  requests:
    memory: "3Gi"    # Increase if needed
    cpu: "1500m"
  limits:
    memory: "6Gi"    # Increase if needed
    cpu: "3000m"
```

### Model Path Configuration
```yaml
env:
- name: MODEL_PATH
  value: "/model_volume/your_custom_model_path"
```

## 🔍 Troubleshooting

### Init Container Fails
```bash
# Check init container logs
kubectl logs -l app=gibberish-service-k8s-native -c pytorch-downloader -n z-grid

# Common issues:
# - Network connectivity for PyTorch download
# - Insufficient storage in EmptyDir
# - Memory constraints
```

### Model Loading Fails
```bash
# Check if model files exist in PVC
kubectl exec -it deployment/gibberish-service-k8s-native -n z-grid -- \
  ls -la /model_volume/inetuned_gibbrish_model/

# Check main container logs
kubectl logs -l app=gibberish-service-k8s-native -c gibberish-service -n z-grid
```

### Service Not Responding
```bash
# Check pod status
kubectl describe pods -l app=gibberish-service-k8s-native -n z-grid

# Check service endpoints
kubectl get endpoints gibberish-service-k8s-native -n z-grid

# Test internal connectivity
kubectl exec -it deployment/gibberish-service-k8s-native -n z-grid -- \
  curl http://localhost:8007/health
```

## 🎯 Production Considerations

1. **Model Registry**: Use artifact registry for model files instead of manual copying
2. **Resource Management**: Adjust memory/CPU based on actual usage
3. **Scaling**: Increase replicas for high availability
4. **Monitoring**: Add metrics and logging
5. **Security**: Use read-only volumes and non-root containers (configured)

## 🧹 Cleanup
```bash
# Delete the deployment
kubectl delete -f ../k8s/gibberish-service-k8s-native.yaml -n z-grid

# Keep PVC if you want to reuse model files
kubectl delete pvc gibberish-model-pvc -n z-grid
```

This approach eliminates all Mac compatibility issues and leverages Kubernetes for a truly cloud-native deployment!