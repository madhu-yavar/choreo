#!/bin/bash

# Script to migrate bias detection services to z-grid namespace

BIAS_SERVICES=("bias-service-yavar" "simple-bias-service")

for service in "${BIAS_SERVICES[@]}"; do
    echo "Migrating $service..."

    # Get service configuration from default namespace
    kubectl get service $service -n default -o yaml > "/tmp/${service}-service.yaml"

    # Extract external IP if it's a LoadBalancer
    EXTERNAL_IP=$(kubectl get service $service -n default -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

    # Create service YAML for z-grid namespace
    cat > "/Users/yavar/Documents/CoE/z_grid/${service}-zgrid.yaml" << EOF
apiVersion: v1
kind: Service
metadata:
  name: $service
  namespace: z-grid
  labels:
    app: $service
EOF

    if [ ! -z "$EXTERNAL_IP" ]; then
        echo "  Preserving external IP: $EXTERNAL_IP"
        cat >> "/Users/yavar/Documents/CoE/z_grid/${service}-zgrid.yaml" << EOF
  annotations:
    service.beta.kubernetes.io/aws-load-balancer-eip-allocations: "$EXTERNAL_IP"
spec:
  loadBalancerIP: "$EXTERNAL_IP"
EOF
    else
        cat >> "/Users/yavar/Documents/CoE/z_grid/${service}-zgrid.yaml" << EOF
spec:
EOF
    fi

    cat >> "/Users/yavar/Documents/CoE/z_grid/${service}-zgrid.yaml" << EOF
  ports:
  - port: $(kubectl get service $service -n default -o jsonpath='{.spec.ports[0].port}')
    protocol: TCP
    targetPort: $(kubectl get service $service -n default -o jsonpath='{.spec.ports[0].targetPort}')
  selector:
    app: $service
  type: $(kubectl get service $service -n default -o jsonpath='{.spec.type}')
EOF

    # Get deployment name for this service
    DEPLOYMENT_NAME=$(kubectl get deployments -n default -l app=$service -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")

    if [ ! -z "$DEPLOYMENT_NAME" ]; then
        echo "  Found deployment: $DEPLOYMENT_NAME"
        kubectl get deployment $DEPLOYMENT_NAME -n default -o yaml > "/tmp/${DEPLOYMENT_NAME}-deployment.yaml"

        # Create deployment YAML for z-grid namespace (simplified)
        cat > "/Users/yavar/Documents/CoE/z_grid/${DEPLOYMENT_NAME}-zgrid.yaml" << EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: $DEPLOYMENT_NAME
  namespace: z-grid
  labels:
    app: $service
spec:
  replicas: 1
  selector:
    matchLabels:
      app: $service
  template:
    metadata:
      labels:
        app: $service
    spec:
      containers:
      - name: $service
        image: $(kubectl get deployment $DEPLOYMENT_NAME -n default -o jsonpath='{.spec.template.spec.containers[0].image}')
        ports:
        - containerPort: $(kubectl get deployment $DEPLOYMENT_NAME -n default -o jsonpath='{.spec.template.spec.containers[0].ports[0].containerPort}')
EOF
    fi

    echo "  Created service config for $service"
done

echo "Bias service migration configurations created. Applying to cluster..."

for service in "${BIAS_SERVICES[@]}"; do
    echo "Applying $service to z-grid namespace..."
    kubectl apply -f "/Users/yavar/Documents/CoE/z_grid/${service}-zgrid.yaml"

    DEPLOYMENT_NAME=$(kubectl get deployments -n default -l app=$service -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")
    if [ ! -z "$DEPLOYMENT_NAME" ]; then
        echo "Applying deployment $DEPLOYMENT_NAME to z-grid namespace..."
        kubectl apply -f "/Users/yavar/Documents/CoE/z_grid/${DEPLOYMENT_NAME}-zgrid.yaml"
    fi
done

echo "Bias service migration completed!"