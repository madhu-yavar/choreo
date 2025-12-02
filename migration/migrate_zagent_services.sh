#!/bin/bash

# Script to migrate z-agent services to z-grid namespace

ZAGENT_SERVICES=("z-agent-app" "z-agent-web-service")
ZAGENT_DEPLOYMENTS=("z-agent-app" "z-agent-auth" "z-agent-web")

echo "Migrating z-agent services and deployments..."

# Migrate services first
for service in "${ZAGENT_SERVICES[@]}"; do
    echo "Migrating service $service..."

    # Get service configuration from default namespace
    kubectl get service $service -n default -o yaml > "/tmp/${service}-service.yaml"

    # Create service YAML for z-grid namespace (these are ClusterIP)
    cat > "/Users/yavar/Documents/CoE/z_grid/${service}-zgrid.yaml" << EOF
apiVersion: v1
kind: Service
metadata:
  name: $service
  namespace: z-grid
  labels:
    app: $service
spec:
  ports:
EOF

    # Handle multi-port service for z-agent-web-service
    if [ "$service" == "z-agent-web-service" ]; then
        cat >> "/Users/yavar/Documents/CoE/z_grid/${service}-zgrid.yaml" << EOF
  - port: 80
    protocol: TCP
    targetPort: 80
  - port: 443
    protocol: TCP
    targetPort: 443
EOF
    else
        cat >> "/Users/yavar/Documents/CoE/z_grid/${service}-zgrid.yaml" << EOF
  - port: $(kubectl get service $service -n default -o jsonpath='{.spec.ports[0].port}')
    protocol: TCP
    targetPort: $(kubectl get service $service -n default -o jsonpath='{.spec.ports[0].targetPort}')
EOF
    fi

    cat >> "/Users/yavar/Documents/CoE/z_grid/${service}-zgrid.yaml" << EOF
  selector:
    app: $service
  type: ClusterIP
EOF

    echo "  Created service config for $service"
done

# Migrate deployments
for deployment in "${ZAGENT_DEPLOYMENTS[@]}"; do
    echo "Migrating deployment $deployment..."

    # Get deployment configuration from default namespace
    kubectl get deployment $deployment -n default -o yaml > "/tmp/${deployment}-deployment.yaml"

    # Create deployment YAML for z-grid namespace
    cat > "/Users/yavar/Documents/CoE/z_grid/${deployment}-zgrid.yaml" << EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: $deployment
  namespace: z-grid
  labels:
    app: $deployment
spec:
  replicas: $(kubectl get deployment $deployment -n default -o jsonpath='{.spec.replicas}')
  selector:
    matchLabels:
      app: $deployment
  template:
    metadata:
      labels:
        app: $deployment
    spec:
      containers:
EOF

    # Get container information
    CONTAINER_COUNT=$(kubectl get deployment $deployment -n default -o jsonpath='{.spec.template.spec.containers | length}')

    for ((i=0; i<CONTAINER_COUNT; i++)); do
        CONTAINER_NAME=$(kubectl get deployment $deployment -n default -o jsonpath="{.spec.template.spec.containers[$i].name}")
        CONTAINER_IMAGE=$(kubectl get deployment $deployment -n default -o jsonpath="{.spec.template.spec.containers[$i].image}")

        cat >> "/Users/yavar/Documents/CoE/z_grid/${deployment}-zgrid.yaml" << EOF
      - name: $CONTAINER_NAME
        image: $CONTAINER_IMAGE
        ports:
EOF

        # Get ports for this container
        PORT_COUNT=$(kubectl get deployment $deployment -n default -o jsonpath="{.spec.template.spec.containers[$i].ports | length}")
        if [ "$PORT_COUNT" -gt 0 ]; then
            for ((j=0; j<PORT_COUNT; j++)); do
                PORT=$(kubectl get deployment $deployment -n default -o jsonpath="{.spec.template.spec.containers[$i].ports[$j].containerPort}")
                cat >> "/Users/yavar/Documents/CoE/z_grid/${deployment}-zgrid.yaml" << EOF
        - containerPort: $PORT
EOF
            done
        fi

        # Add environment variables if they exist
        ENV_COUNT=$(kubectl get deployment $deployment -n default -o jsonpath="{.spec.template.spec.containers[$i].env | length}")
        if [ "$ENV_COUNT" -gt 0 ]; then
            cat >> "/Users/yavar/Documents/CoE/z_grid/${deployment}-zgrid.yaml" << EOF
        env:
EOF
            for ((k=0; k<ENV_COUNT; k++)); do
                ENV_NAME=$(kubectl get deployment $deployment -n default -o jsonpath="{.spec.template.spec.containers[$i].env[$k].name}")
                ENV_VALUE=$(kubectl get deployment $deployment -n default -o jsonpath="{.spec.template.spec.containers[$i].env[$k].value}")
                cat >> "/Users/yavar/Documents/CoE/z_grid/${deployment}-zgrid.yaml" << EOF
        - name: $ENV_NAME
          value: "$ENV_VALUE"
EOF
            done
        fi

        # Add resources if they exist
        HAS_RESOURCES=$(kubectl get deployment $deployment -n default -o jsonpath="{.spec.template.spec.containers[$i].resources}" | tr -d '[:space:]')
        if [ "$HAS_RESOURCES" != "map[]" ]; then
            cat >> "/Users/yavar/Documents/CoE/z_grid/${deployment}-zgrid.yaml" << EOF
        resources:
          limits:
            cpu: $(kubectl get deployment $deployment -n default -o jsonpath="{.spec.template.spec.containers[$i].resources.limits.cpu}")
            memory: $(kubectl get deployment $deployment -n default -o jsonpath="{.spec.template.spec.containers[$i].resources.limits.memory}")
          requests:
            cpu: $(kubectl get deployment $deployment -n default -o jsonpath="{.spec.template.spec.containers[$i].resources.requests.cpu}")
            memory: $(kubectl get deployment $deployment -n default -o jsonpath="{.spec.template.spec.containers[$i].resources.requests.memory}")
EOF
        fi
    done

    echo "  Created deployment config for $deployment"
done

echo "Applying z-agent services and deployments to z-grid namespace..."

# Apply services
for service in "${ZAGENT_SERVICES[@]}"; do
    echo "Applying service $service to z-grid namespace..."
    kubectl apply -f "/Users/yavar/Documents/CoE/z_grid/${service}-zgrid.yaml"
done

# Apply deployments
for deployment in "${ZAGENT_DEPLOYMENTS[@]}"; do
    echo "Applying deployment $deployment to z-grid namespace..."
    kubectl apply -f "/Users/yavar/Documents/CoE/z_grid/${deployment}-zgrid.yaml"
done

echo "Z-agent service migration completed!"