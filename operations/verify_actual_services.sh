#!/bin/bash
# Verify and fix actual Z-Grid services connectivity

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    local status=$1
    local message=$2

    case $status in
        "SUCCESS")
            echo -e "${GREEN}✓${NC} $message"
            ;;
        "INFO")
            echo -e "${YELLOW}ℹ${NC} $message"
            ;;
        "ERROR")
            echo -e "${RED}✗${NC} $message"
            ;;
    esac
}

echo "=================================================================="
echo "🔍 Z-Grid Service Verification & Fix"
echo "=================================================================="
echo ""

# Expected services based on your deployment files
declare -A expected_services=(
    ["working-gateway-service"]="8008"
    ["pii-service-yavar"]="8000"
    ["tox-service-yavar"]="8001"
    ["jail-service-yavar"]="8002"
    ["policy-service-external"]="8003"
    ["ban-service-yavar"]="8004"
    ["secrets-service-yavar"]="8005"
    ["format-service-yavar"]="8006"
    ["gibberish-service-yavar"]="8007"
    ["config-service-yavar"]="8009"
    ["bias-service-yavar"]="8012"
    ["simple-bias-service"]="8013"
)

print_status "INFO" "Checking Kubernetes cluster connectivity..."

# Check if we can connect to cluster
if kubectl cluster-info &>/dev/null; then
    print_status "SUCCESS" "Connected to Kubernetes cluster"
else
    print_status "ERROR" "Cannot connect to Kubernetes cluster"
    print_status "INFO" "Please run: az aks get-credentials --resource-group YOUR_RG --name YOUR_CLUSTER"
    exit 1
fi

# Check if z-grid namespace exists
if ! kubectl get namespace z-grid &>/dev/null; then
    print_status "INFO" "Creating z-grid namespace..."
    kubectl create namespace z-grid
    print_status "SUCCESS" "Created z-grid namespace"
else
    print_status "SUCCESS" "z-grid namespace exists"
fi

echo ""
echo "=================================================================="
echo "🔍 Service Analysis"
echo "=================================================================="

total_services=${#expected_services[@]}
found_services=0
missing_services=""

for service in "${!expected_services[@]}"; do
    expected_port=${expected_services[$service]}

    echo -n "Checking service: $service (port $expected_port)... "

    if kubectl get service $service -n z-grid &>/dev/null; then
        actual_port=$(kubectl get service $service -n z-grid -o jsonpath='{.spec.ports[0].port}')
        service_type=$(kubectl get service $service -n z-grid -o jsonpath='{.spec.type}')

        if [ "$actual_port" = "$expected_port" ]; then
            print_status "SUCCESS" "FOUND - Port $actual_port, Type: $service_type"
            ((found_services++))
        else
            echo -e "${RED}FOUND but wrong port (expected $expected_port, got $actual_port)${NC}"
        fi

        # Check if service has endpoints
        endpoints=$(kubectl get endpoints $service -n z-grid -o jsonpath='{.subsets[*].addresses[*].ip}' 2>/dev/null || echo "")
        if [ -z "$endpoints" ]; then
            echo -e "${YELLOW}  ⚠️  No endpoints (pods may not be running)${NC}"
        else
            echo -e "${GREEN}  ✓ Endpoints: $endpoints${NC}"
        fi

    else
        echo -e "${RED}NOT FOUND${NC}"
        missing_services="$missing_services $service"
    fi
done

echo ""
echo "=================================================================="
echo "📊 Service Summary"
echo "=================================================================="
echo "Expected services: $total_services"
echo "Found services: $found_services"
echo "Missing services: $((${#missing_services}))"

if [ $found_services -eq $total_services ]; then
    print_status "SUCCESS" "All services found! 🎉"
else
    print_status "INFO" "Missing services:$missing_services"
    print_status "INFO" "You may need to deploy the missing services first"
fi

echo ""
echo "=================================================================="
echo "🚀 Deploying Ingress Fix"
echo "=================================================================="

print_status "INFO" "Applying complete ingress configuration..."

# Apply the complete ingress fix
if kubectl apply -f k8s/complete-zgrid-ingress-fix.yaml; then
    print_status "SUCCESS" "Ingress configuration applied"
else
    print_status "ERROR" "Failed to apply ingress configuration"
    exit 1
fi

# Wait for ingress to be processed
print_status "INFO" "Waiting for ingress to be processed..."
sleep 10

# Check ingress status
echo ""
echo "=================================================================="
echo "🔍 Ingress Status"
echo "=================================================================="

if kubectl get ingress complete-zgrid-ingress -n z-grid &>/dev/null; then
    print_status "SUCCESS" "Ingress deployed"

    # Get ingress details
    ingress_ip=$(kubectl get ingress complete-zgrid-ingress -n z-grid -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "")
    if [ ! -z "$ingress_ip" ]; then
        print_status "SUCCESS" "Ingress IP: $ingress_ip"
    else
        print_status "INFO" "Waiting for external IP assignment..."
    fi

    # Show ingress rules
    echo ""
    echo "Ingress rules:"
    kubectl get ingress complete-zgrid-ingress -n z-grid -o jsonpath='{.spec.rules[*].host}' | tr ' ' '\n' | sort | uniq | head -10

else
    print_status "ERROR" "Ingress not found"
fi

echo ""
echo "=================================================================="
echo "🧪 Testing Connectivity"
echo "=================================================================="

print_status "INFO" "Testing main gateway..."

# Test main gateway
gateway_url="https://zgrid-gateway.20.242.183.197.nip.io/health"
test_result=$(curl -k -s -o /dev/null -w "%{http_code}" \
    -H "X-API-Key: supersecret123" \
    "$gateway_url" 2>/dev/null || echo "000")

if [ "$test_result" = "200" ]; then
    print_status "SUCCESS" "Gateway is accessible! 🎉"
    echo "  URL: $gateway_url"
else
    print_status "INFO" "Gateway not yet accessible (HTTP $test_result)"
    echo "  This may take a few minutes for DNS to propagate"
fi

print_status "INFO" "Testing individual services..."

# Test a few services
services_to_test=("pii" "tox" "jail" "policy")

for service in "${services_to_test[@]}"; do
    service_url="https://$service.20.242.183.197.nip.io/health"
    test_result=$(curl -k -s -o /dev/null -w "%{http_code}" \
        -H "X-API-Key: supersecret123" \
        "$service_url" 2>/dev/null || echo "000")

    if [ "$test_result" = "200" ]; then
        print_status "SUCCESS" "$service service is accessible"
    else
        print_status "INFO" "$service service not yet accessible (HTTP $test_result)"
    fi
done

echo ""
echo "=================================================================="
echo "🎯 Next Steps"
echo "=================================================================="

if [ $found_services -eq $total_services ]; then
    print_status "SUCCESS" "All services are deployed and ingress is configured!"
    echo ""
    echo "Your services should be accessible at:"
    echo "  • Main Gateway: https://zgrid-gateway.20.242.183.197.nip.io"
    echo "  • PII Service:   https://pii.20.242.183.197.nip.io"
    echo "  • Toxicity:      https://tox.20.242.183.197.nip.io"
    echo "  • Policy:        https://policy.20.242.183.197.nip.io"
    echo "  • API Gateway:   https://api.20.242.183.197.nip.io/pii"
    echo ""
    echo "Test commands:"
    echo "  curl -k -X POST \"https://zgrid-gateway.20.242.183.197.nip.io/validate\" \\"
    echo "    -H \"X-API-Key: supersecret123\" \\"
    echo "    -d '{\"text\": \"test\", \"check_pii\": true}' | jq ."
    echo ""
    echo "  ./test_all_services_connectivity.sh"
else
    print_status "INFO" "Deploy missing services first, then test connectivity"
    echo "Missing services:$missing_services"
    echo ""
    echo "Deploy with:"
    for service in $missing_services; do
        case $service in
            "pii-service-yavar")
                echo "  kubectl apply -f deploy/k8s/pii-service-deployment.yaml"
                ;;
            "tox-service-yavar")
                echo "  kubectl apply -f deploy/k8s/tox-service-deployment.yaml"
                ;;
            "jail-service-yavar")
                echo "  kubectl apply -f deploy/k8s/jail-service-deployment.yaml"
                ;;
            # Add more service deployments as needed
            *)
                echo "  # Find deployment file for $service"
                ;;
        esac
    done
fi

echo ""
print_status "SUCCESS" "Verification complete!"