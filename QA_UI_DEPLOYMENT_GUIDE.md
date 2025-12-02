# 🚀 QA UI Deployment Guide

This guide explains how to deploy the zGrid QA Testing UI as a microservice in Kubernetes.

## 📋 Overview

The QA UI is a React-based web application that provides a user-friendly interface for testing zGrid content moderation services. It follows the same deployment pattern as other zGrid services using Helm charts.

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   User Browser  │───▶│  QA UI Service  │───▶│ Gateway Service │
│                 │    │  (React/Vite)   │    │  (Port 8008)    │
│ qa.20.242.183.  │    │  Port 80       │    │                 │
│ 197.nip.io      │    │  Nginx/Node.js │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📦 Components Created

### 1. Docker Configuration
- **Dockerfile**: Multi-stage build with Nginx
- **nginx.conf**: Optimized Nginx configuration
- **.env.production**: Production environment variables

### 2. Helm Templates
- **qa-ui-deployment.yaml**: Kubernetes deployment manifest
- **qa-ui-service.yaml**: Kubernetes service manifest
- **Updated ingress.yaml**: Added QA UI route
- **Updated _helpers.tpl**: Added QA UI selector labels

### 3. Configuration Files
- **values.yaml**: Added QA UI service configuration
- **all-services-values.yaml**: Production-ready values
- **build-qa-ui-acr.sh**: Build and push script

## 🚀 Deployment Steps

### Prerequisites
- Docker Desktop installed and running
- kubectl configured for your AKS cluster
- Azure CLI logged in with ACR access

### Step 1: Build and Push Docker Image

```bash
# Navigate to QA UI directory
cd QA_testing/

# Build and push to ACR
./deployment/scripts/build-qa-ui-acr.sh

# Or manually:
docker build -t zinfradevv1.azurecr.io/zgrid-qa-ui:latest .
docker push zinfradevv1.azurecr.io/zgrid-qa-ui:latest
```

### Step 2: Deploy with Helm

```bash
# Deploy QA UI along with all services
helm upgrade --install zgrid deployment/helm/zgrid-chart/ \
  --namespace z-grid \
  --create-namespace \
  --values deploy/all-services-values.yaml

# Or deploy only QA UI (if other services are already running)
helm upgrade --install zgrid deployment/helm/zgrid-chart/ \
  --namespace z-grid \
  --set qaUiService.enabled=true \
  --set ingress.enabled=true
```

### Step 3: Verify Deployment

```bash
# Check pod status
kubectl get pods -n z-grid | grep qa-ui

# Check service
kubectl get svc -n z-grid | grep qa-ui

# Check logs
kubectl logs -n z-grid deployment/zgrid-chart-qa-ui

# Check ingress
kubectl get ingress -n z-grid
```

## 🔧 Configuration

### Environment Variables
- `VITE_GATEWAY_ENDPOINT`: Gateway service URL
- `VITE_GATEWAY_API_KEY`: API key (from secret)
- `VITE_APP_NAME`: Application name
- `VITE_APP_VERSION`: Application version

### Resource Allocation
- **CPU**: 100m - 500m
- **Memory**: 128Mi - 512Mi
- **Replicas**: 2 (for high availability)

### Health Checks
- **Liveness Probe**: `/health` endpoint
- **Readiness Probe**: `/health` endpoint
- **Timeout**: 30s liveness, 5s readiness

## 🌐 Access URLs

Once deployed, the QA UI will be available at:

**Production**: https://qa.20.242.183.197.nip.io

## 🔍 Features

### Testing Interface
- **Text Input**: Test any text content
- **Service Selection**: Choose which zGrid services to test
- **Real-time Results**: See responses from each service
- **Response Analysis**: View detailed breakdown of results

### Test Scenarios
- **PII Detection**: Test personal information removal
- **Toxicity Filtering**: Test profanity and hate speech detection
- **Policy Violations**: Test harmful content detection
- **Jailbreak Attempts**: Test prompt injection detection
- **Secret Detection**: Test API key and credential detection
- **Format Validation**: Test text format requirements
- **Gibberish Detection**: Test nonsense text filtering

## 🛠️ Troubleshooting

### Common Issues

**Pod not starting:**
```bash
kubectl describe pod -n z-grid <pod-name>
kubectl logs -n z-grid <pod-name>
```

**Service not accessible:**
```bash
kubectl get svc -n z-grid
kubectl get endpoints -n z-grid
```

**Ingress not working:**
```bash
kubectl get ingress -n z-grid
kubectl describe ingress -n z-grid zgrid-chart-zgrid
```

**Build issues:**
- Ensure Docker is running
- Check Dockerfile paths
- Verify ACR permissions

### Health Check
```bash
# Test health endpoint
curl http://<service-ip>/health

# Should return: "healthy"
```

## 📊 Monitoring

The QA UI includes built-in monitoring:
- **Health checks**: Automatic pod health monitoring
- **Resource usage**: CPU and memory metrics
- **Access logs**: Nginx access logs
- **Error tracking**: Application error logs

## 🔄 Updates

To update the QA UI:

```bash
# Build new version
docker build -t zinfradevv1.azurecr.io/zgrid-qa-ui:v1.1.0 .
docker push zinfradevv1.azurecr.io/zgrid-qa-ui:v1.1.0

# Update deployment
helm upgrade zgrid deployment/helm/zgrid-chart/ \
  --namespace z-grid \
  --set qaUiService.image.tag=v1.1.0 \
  --values deploy/all-services-values.yaml
```

## 📞 Support

For issues with QA UI deployment:
1. Check the troubleshooting section above
2. Review Kubernetes logs and events
3. Verify ACR image availability
4. Check network connectivity to Gateway service

---

*For general zGrid deployment issues, see the main [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md).*