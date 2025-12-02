#!/bin/bash

# Deployment script for Z-Grid Real-Time Monitoring Dashboard

echo "🚀 Deploying Z-Grid Real-Time Monitoring Dashboard..."

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl is not installed or not in PATH"
    exit 1
fi

# Check if we're connected to the cluster
if ! kubectl cluster-info &> /dev/null; then
    echo "❌ Not connected to Kubernetes cluster"
    exit 1
fi

echo "✅ Connected to Kubernetes cluster"

# Apply the ConfigMap
echo "📝 Applying ConfigMap..."
kubectl apply -f k8s/realtime-dashboard-config.yaml

# Apply ServiceAccount, ClusterRole, and ClusterRoleBinding
echo "🔐 Applying RBAC configuration..."
kubectl apply -f k8s/realtime-dashboard-deployment.yaml

# Wait for the deployment to be ready
echo "⏳ Waiting for deployment to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/realtime-monitoring-dashboard -n z-grid

# Apply Ingress
echo "🌐 Applying Ingress configuration..."
kubectl apply -f k8s/realtime-dashboard-ingress.yaml

# Get the status of all resources
echo "📊 Checking deployment status..."
echo ""
echo "Pods:"
kubectl get pods -n z-grid -l app=realtime-monitoring-dashboard
echo ""
echo "Services:"
kubectl get services -n z-grid -l app=realtime-monitoring-dashboard
echo ""
echo "Ingress:"
kubectl get ingress -n z-grid -l app=realtime-monitoring-dashboard

# Get the dashboard URL
echo ""
echo "🌍 Real-Time Dashboard URL:"
echo "http://realtime-monitoring.20.242.183.197.nip.io"

# Check if the deployment is healthy
echo ""
echo "🏥 Checking health endpoint..."
sleep 10
kubectl port-forward -n z-grid svc/realtime-monitoring-dashboard-service 5001:5000 &
PF_PID=$!
sleep 5
if curl -f http://localhost:5001/api/health &> /dev/null; then
    echo "✅ Dashboard is healthy and responding"
    curl http://localhost:5001/api/health | jq .
else
    echo "⚠️  Dashboard health check failed - checking logs..."
    kubectl logs -n z-grid -l app=realtime-monitoring-dashboard --tail=20
fi
kill $PF_PID 2>/dev/null

echo ""
echo "🎉 Real-Time Monitoring Dashboard deployment completed!"
echo "📈 Access your dashboard at: http://realtime-monitoring.20.242.183.197.nip.io"
echo ""
echo "🔍 To check logs: kubectl logs -n z-grid -l app=realtime-monitoring-dashboard -f"
echo "🔧 To check status: kubectl get pods -n z-grid -l app=realtime-monitoring-dashboard"