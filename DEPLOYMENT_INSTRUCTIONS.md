# Optimized K8s Deployment Instructions for Inetuned Gibbrish Model

## Overview
This optimized deployment eliminates PyTorch downloads during pod startup by:
- Pre-building PyTorch into Docker image
- Using PVC for model storage
- Fast startup (45-60 seconds vs 3-5 minutes)

## Prerequisites
- Docker Desktop or container registry access
- kubectl configured for your K8s cluster
- Existing `gibberish-model-pvc` PVC (5Gi capacity)

## Step 1: Build Optimized Docker Image

```bash
# Build the optimized image
cd gibberish_service
docker build -t inetuned-gibberish:latest .

# For production, push to your registry
# docker tag inetuned-gibberish:latest your-registry/inetuned-gibberish:latest
# docker push your-registry/inetuned-gibberish:latest
```

## Step 2: Copy Model Files to PVC

### Option A: Using kubectl cp (Recommended for testing)

```bash
# Create temporary pod to copy files
kubectl run temp-model-copier --image=busybox --rm -i --tty --restart=Never -n z-grid -- /bin/sh

# In the pod shell:
mkdir -p /model_volume/inetuned_gibbrish_model
exit

# Copy model files from local to PVC
kubectl cp models/hf_space_efficient/inetuned_gibbrish_model/ temp-model-copier:/model_volume/inetuned_gibbrish_model/ -n z-grid

# Delete temp pod if not using --rm
kubectl delete pod temp-model-copier -n z-grid
```

### Option B: Using Model Copy Job

```bash
# Apply model copy job
kubectl apply -f ../k8s/gibberish-model-copy-optimized.yaml -n z-grid

# Monitor job progress
kubectl get jobs -n z-grid -w

# Check logs
kubectl logs job/copy-inetuned-model-optimized -n z-grid

# Manual copy required (job only creates directory structure)
# Use Option A for actual file copying
```

## Step 3: Deploy Optimized Service

```bash
# Update the image reference in deployment if needed
# Edit the line: image: your-registry/inetuned-gibberish:latest

# Apply optimized deployment
kubectl apply -f ../k8s/gibberish-service-optimized-deployment.yaml -n z-grid

# Monitor deployment
kubectl get deployments -n z-grid -w
kubectl get pods -n z-grid -l app=gibberish-service-optimized -w
```

## Step 4: Verify Deployment

```bash
# Check pod logs
kubectl logs -l app=gibberish-service-optimized -n z-grid

# Test the service
kubectl port-forward svc/gibberish-service-optimized 8007:8007 -n z-grid

# In another terminal, test the API:
curl http://localhost:8007/health
curl -X POST http://localhost:8007/detect \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello world"}'
```

## Expected Performance

**Before Optimization:**
- Image size: 2.5-3GB (with runtime PyTorch install)
- Pod startup: 3-5 minutes (PyTorch download)
- Memory usage: 2-4GB

**After Optimization:**
- Image size: 800MB-1GB (pre-built PyTorch)
- Pod startup: 45-60 seconds (no downloads)
- Memory usage: 1-2GB

## Troubleshooting

### Pod fails to start
```bash
# Check pod status and events
kubectl describe pod -l app=gibberish-service-optimized -n z-grid

# Check if PVC is bound
kubectl get pvc gibberish-model-pvc -n z-grid
```

### Model loading fails
```bash
# Check if model files exist in PVC
kubectl exec -it deployment/gibberish-service-optimized -n z-grid -- ls -la /model_volume/inetuned_gibbrish_model/

# Verify model file permissions
kubectl exec -it deployment/gibberish-service-optimized -n z-grid -- ls -la /model_volume/
```

### Service not responding
```bash
# Check service endpoints
kubectl get endpoints gibberish-service-optimized -n z-grid

# Test internal connectivity
kubectl exec -it deployment/gibberish-service-optimized -n z-grid -- curl http://localhost:8007/health
```

## Production Considerations

1. **Image Registry**: Use a proper container registry (Docker Hub, AWS ECR, Azure Container Registry)
2. **Resource Limits**: Adjust memory/CPU limits based on actual usage
3. **Replicas**: Increase replicas for high availability
4. **Monitoring**: Add metrics collection and alerting
5. **Security**: Use read-only PVC and non-root containers (already configured)

## Cleanup (if needed)

```bash
# Delete optimized deployment
kubectl delete -f ../k8s/gibberish-service-optimized-deployment.yaml -n z-grid

# Delete old deployment (if still running)
kubectl delete deployment gibberish-service-inetuned -n z-grid
kubectl delete service gibberish-service-inetuned -n z-grid
```