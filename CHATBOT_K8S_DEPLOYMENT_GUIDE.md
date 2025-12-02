# Z-Grid Chatbot Service Kubernetes Deployment Guide

## 🚀 Overview

This guide provides step-by-step instructions for deploying the Z-Grid Chatbot service with enhanced Gateway 2 integration to Kubernetes with external IP access for testing.

## 📋 Prerequisites

### Required Tools
- **Kubernetes cluster** (v1.20+)
- **kubectl** configured and connected to your cluster
- **Docker** for building container images
- **Helm** (optional, for advanced deployments)

### Cluster Requirements
- **Namespace**: `zgrid` (will be created automatically)
- **Resource allocations**:
  - Minimum: 2 pods × 512Mi memory, 500m CPU
  - Recommended: 2 pods × 1Gi memory, 1000m CPU
- **LoadBalancer support** (for external IP access)
- **Gateway 2 endpoint** (currently: `http://134.33.132.66:8008`)

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Kubernetes Cluster                         │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌─────────────────────────────────────┐  │
│  │   Ingress       │    │        LoadBalancer Service         │  │
│  │ (Optional)      │    │       (External IP: 8010)           │  │
│  └─────────────────┘    └─────────────────────────────────────┘  │
│                                │                              │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │                Chatbot Deployment                           │  │
│  │  ┌─────────────┐  ┌─────────────┐                           │  │
│  │  │  Pod 1      │  │  Pod 2      │  (Auto-scaling: 2-10) │  │
│  │  │ Port: 8010  │  │ Port: 8010  │                           │  │
│  │  └─────────────┘  └─────────────┘                           │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                │                              │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │                    External Services                          │  │
│  │  ┌─────────────────────────────────────────────────────────┐  │
│  │  │              Gateway 2 Service                           │  │
│  │  │        (134.33.132.66:8008)                           │  │
│  │  │  • 32 PII Entity Detection                              │  │
│  │  │  • Enhanced Bias Detection                              │  │
│  │  │  • Real-time Processing                                │  │
│  │  └─────────────────────────────────────────────────────────┘  │
│  └─────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## 🛠️ Deployment Options

### Option 1: Automated Deployment Script (Recommended)

#### Quick Deploy
```bash
# Clone the repository (if not already done)
git clone <your-repo-url> z-grid
cd z-grid

# Run automated deployment
./scripts/deploy-chatbot-k8s.sh
```

#### Deploy with Registry Push
```bash
./scripts/deploy-chatbot-k8s.sh --push
```

#### Clean Previous Deployment
```bash
./scripts/deploy-chatbot-k8s.sh --cleanup
```

### Option 2: Manual Step-by-Step Deployment

#### Step 1: Build Docker Image
```bash
cd services/chatbot_service

# Build using K8s optimized Dockerfile
docker build -f Dockerfile.k8s -t zgrid/chatbot-service:gateway2-v2 .
```

#### Step 2: Push to Registry (Optional)
```bash
docker tag zgrid/chatbot-service:gateway2-v2 your-registry.com/zgrid/chatbot-service:gateway2-v2
docker push your-registry.com/zgrid/chatbot-service:gateway2-v2
```

#### Step 3: Create Namespace
```bash
kubectl create namespace zgrid --dry-run=client -o yaml | kubectl apply -f -
```

#### Step 4: Deploy Kubernetes Resources
```bash
# Apply the deployment configuration
kubectl apply -f k8s/chatbot-service-deployment-updated.yaml -n zgrid
```

#### Step 5: Wait for Deployment
```bash
# Wait for pods to be ready
kubectl wait --for=condition=ready pod -l app=zgrid-chatbot-service -n zgrid --timeout=300s
```

#### Step 6: Get External IP
```bash
# Monitor LoadBalancer service
kubectl get service zgrid-chatbot-service-external -n zgrid -w

# Or check periodically
kubectl get service zgrid-chatbot-service-external -n zgrid
```

## 🌐 Accessing the Deployed Service

### External Access (LoadBalancer)
Once the LoadBalancer IP is allocated:

```bash
# Health check
curl http://<EXTERNAL_IP>:8010/

# Test chat endpoint
curl -X POST http://<EXTERNAL_IP>:8010/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello Zee!", "user_name": "test"}'
```

### Port Forwarding (For Testing)
If LoadBalancer is not available:

```bash
# Forward local port to service
kubectl port-forward service/zgrid-chatbot-service-external 8010:8010 -n zgrid

# Access via localhost
curl http://localhost:8010/
```

### WebSocket Testing
```javascript
// WebSocket connection example
const ws = new WebSocket('ws://<EXTERNAL_IP>:8010/ws');

ws.onopen = () => {
  console.log('Connected to chatbot WebSocket');
  ws.send(JSON.stringify({
    client_id: 'test-client',
    type: 'subscribe'
  }));
};

ws.onmessage = (event) => {
  console.log('Received:', JSON.parse(event.data));
};
```

## 🔧 Configuration

### Environment Variables
- `GATEWAY_URL_V2`: Gateway 2 endpoint (default: `http://134.33.132.66:8008`)
- `GATEWAY_URL`: Fallback gateway endpoint
- `ZGRID_API_KEY`: API key for gateway authentication
- `LOG_LEVEL`: Logging level (default: `INFO`)

### ConfigMap Configuration
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: chatbot-config
  namespace: zgrid
data:
  gateway_timeout: "60"
  max_sessions: "1000"
  max_messages_per_session: "50"
  log_level: "INFO"
```

### Resource Limits
```yaml
resources:
  requests:
    memory: "512Mi"
    cpu: "500m"
  limits:
    memory: "1Gi"
    cpu: "1000m"
```

## 📊 Monitoring and Scaling

### Horizontal Pod Autoscaler (HPA)
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: zgrid-chatbot-service-hpa
  namespace: zgrid
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: zgrid-chatbot-service
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### Health Checks
- **Liveness Probe**: Every 30 seconds (after 45s initial delay)
- **Readiness Probe**: Every 5 seconds (after 10s initial delay)
- **Health Endpoint**: `GET /`

## 🧪 Testing the Deployment

### Basic Health Check
```bash
curl http://<EXTERNAL_IP>:8010/
```

### Chat Functionality Test
```bash
curl -X POST http://<EXTERNAL_IP>:8010/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello Zee! How are you today?",
    "user_name": "test_user"
  }'
```

### PII Detection Test
```bash
curl -X POST http://<EXTERNAL_IP>:8010/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "My email is john.doe@example.com and phone is 123-456-7890",
    "user_name": "test_pii"
  }'
```

### Comprehensive PII Test (32 entities)
```bash
curl -X POST http://<EXTERNAL_IP>:8010/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "John Does full name, living at 123 Main Street, Chennai, Tamil Nadu, 600001, born on 15/05/1985 with mobile +91-9876543210 and email john.doe@example.com, has Aadhaar 1234 5678 9012, PAN ABCDE1234F, passport G1234567, bank account 9876543210, and GSTIN 33ABCDE1234F1Z5",
    "user_name": "test_comprehensive"
  }'
```

## 🔍 Troubleshooting

### Common Issues

#### 1. External IP Not Allocated
```bash
# Check LoadBalancer service status
kubectl describe service zgrid-chatbot-service-external -n zgrid

# Check if cloud provider supports LoadBalancer
kubectl get nodes -o wide
```

#### 2. Pod Crashing or Not Ready
```bash
# Check pod logs
kubectl logs -l app=zgrid-chatbot-service -n zgrid

# Check pod events
kubectl describe pod -l app=zgrid-chatbot-service -n zgrid

# Check resource usage
kubectl top pods -l app=zgrid-chatbot-service -n zgrid
```

#### 3. Gateway Connection Issues
```bash
# Test Gateway 2 connectivity from pod
kubectl exec -it <pod-name> -n zgrid -- curl -v http://134.33.132.66:8008/

# Check environment variables
kubectl get pod <pod-name> -n zgrid -o yaml | grep -A 10 env
```

#### 4. WebSocket Issues
```bash
# Test WebSocket connection
wscat -c ws://<EXTERNAL_IP>:8010/ws

# Check service endpoints
kubectl get endpoints zgrid-chatbot-service-external -n zgrid
```

### Logs and Debugging
```bash
# View real-time logs
kubectl logs -f deployment/zgrid-chatbot-service -n zgrid

# View logs for specific pod
kubectl logs -f <pod-name> -n zgrid

# View pod events
kubectl get events -n zgrid --field-selector involvedObject.name=<pod-name>
```

## 📈 Performance Optimization

### Resource Tuning
1. **Memory**: Gateway 2 processing requires more memory (512Mi minimum)
2. **CPU**: PII and bias detection are CPU-intensive (500m minimum)
3. **Timeouts**: Increased to 60s for Gateway 2 processing time

### Scaling Considerations
- **Replicas**: Start with 2, scale based on load
- **HPA**: Auto-scale 2-10 pods based on CPU/memory utilization
- **LoadBalancer**: Ensure adequate bandwidth for API traffic

### Gateway 2 Optimization
- **Timeout**: Set to 60 seconds for complex PII processing
- **Connection Pooling**: Consider connection pooling for high traffic
- **Caching**: Implement response caching where appropriate

## 🔄 CI/CD Integration

### GitHub Actions Example
```yaml
name: Deploy Chatbot Service

on:
  push:
    paths:
      - 'services/chatbot_service/**'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Build and Push Docker Image
        run: |
          docker build -f services/chatbot_service/Dockerfile.k8s -t ${{ secrets.REGISTRY }}/chatbot-service:${{ github.sha }}
          docker push ${{ secrets.REGISTRY }}/chatbot-service:${{ github.sha }}

      - name: Deploy to Kubernetes
        run: |
          kubectl set image deployment/zgrid-chatbot-service chatbot-service=${{ secrets.REGISTRY }}/chatbot-service:${{ github.sha }} -n zgrid
          kubectl rollout status deployment/zgrid-chatbot-service -n zgrid
```

## 📚 Additional Resources

### Documentation
- [Z-Grid Architecture Overview](../README.md)
- [Gateway 2 Integration Guide](../GATEWAY_2_INTEGRATION.md)
- [PII Detection Documentation](../PII_DETECTION_GUIDE.md)

### Kubernetes Resources
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [LoadBalancer Services](https://kubernetes.io/docs/concepts/services-networking/service/#loadbalancer)
- [Horizontal Pod Autoscaling](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/)

### Monitoring and Observability
- [Prometheus Monitoring](https://prometheus.io/)
- [Grafana Dashboards](https://grafana.com/)
- [Kubernetes Metrics Server](https://kubernetes.io/docs/tasks/debug-application-cluster-resource-usage/metrics-resource-utilization/)

## 🆘 Support

For deployment issues or questions:
1. Check this documentation for common solutions
2. Review Kubernetes and pod logs
3. Verify Gateway 2 connectivity
4. Test with simpler configurations first

---

*Last Updated: November 2025*
*Version: Gateway 2 Enhanced*