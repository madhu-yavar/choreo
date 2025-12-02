# ZGrid Project Context

## Project Overview

This project implements a suite of AI-powered text analysis services for content moderation and protection:

1.  **PII Service (Port 8000)**: Detects and redacts Personally Identifiable Information (PII) using a combination of Presidio and GLiNER models.
2.  **Toxicity Service (Port 8001)**: Analyzes text for toxic or harmful content using Detoxify models and includes profanity detection.
3.  **Jailbreak Service (Port 8002)**: Identifies potential jailbreak attempts or prompts designed to bypass AI safety measures using a classifier, rule-based checks, and similarity search.
4.  **Policy Service (Port 8003)**: General safety using LLM-based policy enforcement with LlamaGuard 7B model.
5.  **Ban Service (Port 8004)**: Brand safety and bias detection through pattern matching with support for literal, regex, fuzzy, homoglyph, and leet-speak matching.
6.  **Secrets Service (Port 8005)**: Detection of sensitive information like API keys and passwords using regex-based pattern matching and entropy analysis.
7.  **Format Service (Port 8006)**: Validation and correction of text formatting using Cucumber-style expression matching.
8.  **Gibberish Service (Port 8007)**: Detection of random character sequences and nonsensical text using heuristic-based detection algorithms.
9.  **Gateway Service (Port 8008)**: Unified entry point for all ZGrid services with consolidated response format and service chaining capabilities.

These services are designed to be deployed via Docker and integrated into applications, particularly UIs, via RESTful APIs.

## Technologies

*   **Language**: Python 3.x
*   **Framework**: FastAPI
*   **Containerization**: Docker, Docker Compose
*   **Orchestration**: Kubernetes (Helm)
*   **Environment Management**: Virtual environments (likely `venv` or `virtualenv`)
*   **Key Libraries**:
    *   `presidio-analyzer`, `presidio-anonymizer`: For rule-based PII detection.
    *   `gliner`: For semantic Named Entity Recognition (NER) in PII detection.
    *   `detoxify`: For toxicity classification.
    *   `transformers`, `torch`: For underlying ML models.
    *   `python-dotenv`: For environment variable management.
    *   `fastapi`, `uvicorn`: For the web service framework.
    *   `llama.cpp`: For GGUF model inference in Policy service.
    *   `RapidFuzz`: For fuzzy matching in Ban service.

## Deployment & Running

This is a Python-based project that uses Docker Compose for deployment. It's primarily designed to run as a set of background services.

### Prerequisites

*   Docker Desktop must be installed and running.
*   At least 8GB of RAM should be allocated to Docker.
*   Ports 8000-8008 must be available.

### Docker Compose (Recommended)

This is the standard way to run the services as described in the project documentation.

1.  **Build and Start Services**:
    ```bash
    cd /Users/yavar/Documents/CoE/zGrid
    docker-compose up --build -d
    ```
2.  **Check Status**:
    ```bash
    docker-compose ps
    ```
3.  **View Logs**:
    ```bash
    docker-compose logs -f pii-service
    docker-compose logs -f tox-service
    docker-compose logs -f jail-service
    # ... similar for other services
    ```
4.  **Stop Services**:
    ```bash
    docker-compose down
    ```

### Manual (Virtual Environment)

The project can also be run directly using Python virtual environments.

1.  **Start Services**:
    ```bash
    # Each service needs to be started in its own terminal or background process
    cd /Users/yavar/Documents/CoE/zGrid/pii_service
    source ../guards/bin/activate # Assumes virtual environment is in 'guards'
    python -m uvicorn app:app --host 0.0.0.0 --port 8000 &
    
    cd /Users/yavar/Documents/CoE/zGrid/tox_service
    source ../guards311/bin/activate # Assumes virtual environment is in 'guards311'
    python -m uvicorn app:app --host 0.0.0.0 --port 8001 &
    
    # ... similar for other services
    ```
2.  **Verify Services**:
    ```bash
    curl http://localhost:8000/health
    curl http://localhost:8001/health
    curl http://localhost:8002/health
    # ... similar for other services
    ```

## Service API Endpoints

### PII Service (Port 8000)

*   `GET /health`: Returns service status.
*   `POST /validate`: Analyzes text and redacts PII.
    *   **Headers**: `Content-Type: application/json`, `X-API-Key: <key>`
    *   **Body**: `{ "text": "string", "entities": ["EMAIL_ADDRESS", ...], "return_spans": true }`

### Toxicity Service (Port 8001)

*   `GET /health`: Returns service status.
*   `POST /validate`: Analyzes text for toxicity and profanity.
    *   **Headers**: `Content-Type: application/json`, `X-API-Key: <key>`
    *   **Body**: `{ "text": "string", "tox_threshold": 0.5, "mode": "sentence", "action_on_fail": "remove_sentences", "return_spans": true }`

### Jailbreak Service (Port 8002)

*   `GET /health`: Returns service status.
*   `POST /validate`: Analyzes text for jailbreak attempts.
    *   **Headers**: `Content-Type: application/json`, `X-API-Key: <key>`
    *   **Body**: `{ "text": "string", "threshold": 0.5, "action_on_fail": "refrain", "enable_similarity": true, "return_spans": true }`

### Policy Service (Port 8003)

*   `GET /health`: Returns service status.
*   `POST /validate`: Analyzes text for policy violations using LLM.
    *   **Headers**: `Content-Type: application/json`, `X-API-Key: <key>`
    *   **Body**: `{ "text": "string", "return_spans": true }`

### Ban Service (Port 8004)

*   `GET /health`: Returns service status.
*   `POST /validate`: Analyzes text for banned patterns (bias, competitors, etc.).
    *   **Headers**: `Content-Type: application/json`, `X-API-Key: <key>`
    *   **Body**: `{ "text": "string", "categories": ["BIAS"], "action_on_fail": "refrain", "return_spans": true }`

### Secrets Service (Port 8005)

*   `GET /health`: Returns service status.
*   `POST /validate`: Detects secrets like API keys in text.
    *   **Headers**: `Content-Type: application/json`, `X-API-Key: <key>`
    *   **Body**: `{ "text": "string", "return_spans": true }`

### Format Service (Port 8006)

*   `GET /health`: Returns service status.
*   `POST /validate`: Validates text formatting.
    *   **Headers**: `Content-Type: application/json`, `X-API-Key: <key>`
    *   **Body**: `{ "text": "string", "return_spans": true }`

### Gibberish Service (Port 8007)

*   `GET /health`: Returns service status.
*   `POST /validate`: Detects gibberish text.
    *   **Headers**: `Content-Type: application/json`, `X-API-Key: <key>`
    *   **Body**: `{ "text": "string", "return_spans": true }`

### Gateway Service (Port 8008)

*   `GET /health`: Returns service status.
*   `POST /validate`: Orchestrates all services for comprehensive content moderation.
    *   **Headers**: `Content-Type: application/json`, `X-API-Key: <key>`
    *   **Body**: `{ "text": "string", "check_bias": true, "check_toxicity": true, ... }`

## Development Conventions

*   **Environment Variables**: Configuration is managed via `.env` files located in each service directory (e.g., `pii_service/.env`).
*   **API Authentication**: Services use API keys passed via the `X-API-Key` header.
*   **CORS**: Cross-Origin Resource Sharing is configured via the `CORS_ALLOWED_ORIGINS` environment variable.
*   **Model Management**: ML models are stored in service-specific `models` directories and mounted as volumes in Docker.
*   **Code Structure**: Each service follows a consistent structure with `app.py` as the main application file, Dockerfile for containerization, and requirements.txt for dependencies.

## Services Architecture

### PII Service (`/pii_service`)
- Built with FastAPI and Python
- Uses Presidio for rule-based PII detection
- Integrates GLiNER for semantic NER (Named Entity Recognition)
- Supports detection of various entities:
  - EMAIL_ADDRESS, PHONE_NUMBER, CREDIT_CARD, US_SSN, PERSON, LOCATION, etc.
- Redacts detected PII with configurable placeholders

### Toxicity Service (`/tox_service`)
- Built with FastAPI and Python
- Uses Detoxify for ML-based toxicity detection
- Integrates profanity filtering
- Supports sentence-level or text-level analysis
- Configurable actions: remove_sentences, remove_all, or redact

### Jailbreak Service (`/jail_service`)
- Built with FastAPI and Python
- Uses a transformer-based jailbreak classifier
- Implements rule-based detection
- Includes similarity search for known attack patterns
- Configurable actions: filter, refrain, or reask

### Policy Service (`/policy_service`)
- Built with FastAPI and Python
- Uses LlamaGuard 7B model for general safety
- Implements LLM-based policy enforcement
- Uses GGUF model format for efficient inference
- Configurable actions: filter, refrain, or reask

### Ban Service (`/ban_service`)
- Built with FastAPI and Python
- Pattern matching for brand safety and bias detection
- Supports literal, regex, fuzzy, homoglyph, and leet-speak matching
- Configurable severity levels
- Customizable ban lists

### Secrets Service (`/secrets_service`)
- Built with FastAPI and Python
- Regex-based pattern matching for secrets
- Entropy analysis for random strings
- Context-aware detection
- Configurable thresholds

### Format Service (`/format_service`)
- Built with FastAPI and Python
- Cucumber-style expression matching
- Case sensitivity options
- Formatting validation
- Configurable action modes

### Gibberish Service (`/gibberish_service`)
- Built with FastAPI and Python
- Heuristic-based detection algorithms
- Pattern recognition for keyboard mashing
- Repeated character detection
- Vowel frequency analysis

### Gateway Service (`/gateway_service`)
- Built with FastAPI and Python
- Unified entry point for all ZGrid services
- Service orchestration and chaining
- Consolidated response format
- Load balancing and failover

## Key Technologies

- **Framework**: FastAPI (Python)
- **Containerization**: Docker
- **Orchestration**: Docker Compose, Kubernetes (Helm)
- **ML Libraries**: 
  - Presidio (PII detection)
  - Detoxify (Toxicity detection)
  - Transformers (Jailbreak detection)
  - GLiNER (Semantic NER)
  - Llama.cpp (Policy service)
- **Infrastructure**: Azure Container Registry for image storage

## Environment Configuration

Each service uses environment variables for configuration, defined in:
- `docker-compose.yml` for Docker deployments
- `values.yaml` for Helm chart deployments
- `.env` files for local development

Key configuration options include:
- API keys for authentication
- Model thresholds for detection sensitivity
- CORS settings for web integration
- Action behaviors for content filtering

## Integration Examples

The services can be integrated via HTTP requests:

```javascript
// Gateway Service (recommended for comprehensive moderation)
const gatewayResponse = await fetch('http://localhost:8008/validate', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': 'supersecret123'
  },
  body: JSON.stringify({
    text: "Contact me at john@email.com. This is terrible!",
    check_pii: true,
    check_toxicity: true
  })
});

// Individual service example (PII Service)
const piiResponse = await fetch('http://localhost:8000/validate', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': 'supersecret123'
  },
  body: JSON.stringify({
    text: "Contact me at john@email.com",
    return_spans: true
  })
});
```

## Common Issues and Troubleshooting

1. **Port conflicts**: Ensure ports 8000-8008 are available
2. **Memory issues**: ML models require significant RAM (2GB+ per service)
3. **API key errors**: Verify X-API-Key header is set correctly
4. **CORS issues**: Update CORS_ALLOWED_ORIGINS in environment configuration
5. **Model download failures**: Check internet connectivity and disk space

## Monitoring and Logs

```bash
# Docker Compose logs
docker-compose logs -f pii-service
docker-compose logs -f tox-service
# ... similar for other services

# Health checks
curl http://localhost:8000/health
curl http://localhost:8001/health
# ... similar for other services
```

## Guidelines for Future Projects

### Project Structure

When creating new services, follow this consistent structure:
```
project-root/
├── service_name/
│   ├── app.py              # Main application file
│   ├── Dockerfile          # Docker configuration
│   ├── requirements.txt    # Python dependencies
│   ├── models/             # ML models directory
│   └── README.md           # Service-specific documentation
├── scripts/
│   └── build_and_push.sh   # Docker build and push script
├── zgrid-chart/            # Helm chart for Kubernetes deployment
│   ├── Chart.yaml          # Chart metadata
│   ├── values.yaml         # Default configuration values
│   └── templates/          # Kubernetes resource templates
└── docker-compose.yml      # Docker Compose configuration
```

### Docker Build and Push Process

1. **Standardized Build Script**: Use the `scripts/build_and_push.sh` script as a template for building and pushing Docker images:
   ```bash
   #!/bin/bash
   
   # Exit on any error
   set -e
   
   # Define variables
   ACR_NAME="your-acr-name"
   ACR_REGISTRY="${ACR_NAME}.azurecr.io"
   IMAGE_TAG="latest"  # Consider using git commit hash or semantic versioning
   PLATFORM="linux/amd64"
   
   # Function to build and push a service
   build_and_push() {
     local SERVICE_NAME=$1
     local DOCKERFILE_PATH=$2
     local CONTEXT_PATH=$3
     local IMAGE_NAME="${ACR_REGISTRY}/project-${SERVICE_NAME}:${IMAGE_TAG}"
   
     echo "Building ${SERVICE_NAME} service for ${PLATFORM}..."
     docker build --platform ${PLATFORM} -t ${IMAGE_NAME} -f ${DOCKERFILE_PATH} ${CONTEXT_PATH}
   
     echo "Pushing ${SERVICE_NAME} service to ${ACR_REGISTRY}..."
     docker push ${IMAGE_NAME}
   
     echo "Completed ${SERVICE_NAME} service deployment."
   }
   
   # Login to ACR
   echo "Logging into Azure Container Registry..."
   az acr login --name ${ACR_NAME}
   
   # Build and push each service
   build_and_push "service1" "./service1/Dockerfile" "./service1"
   build_and_push "service2" "./service2/Dockerfile" "./service2"
   # ... similar for other services
   
   echo "All services built and pushed successfully!"
   ```

2. **Dockerfile Best Practices**:
   - Use multi-stage builds when possible to reduce image size
   - Install system dependencies in a single RUN command to reduce layers
   - Copy requirements.txt first for better caching
   - Create non-root users for security
   - Set proper health checks
   - Use environment variables for configuration

### Helm Chart Creation Guidelines

1. **Chart Structure**:
   - Maintain separate templates for deployments and services
   - Use helper templates for common labels and selectors
   - Parameterize all configurable values in values.yaml
   - Include ingress configuration for external access

2. **Template Organization**:
   ```
   templates/
   ├── _helpers.tpl           # Helper templates for labels, names, etc.
   ├── namespace.yaml         # Namespace creation
   ├── service-name-deployment.yaml  # Deployment for each service
   ├── service-name-service.yaml     # Service for each service
   └── ingress.yaml           # Ingress controller configuration
   ```

3. **Values Configuration**:
   - Separate configuration sections for each service
   - Include image, resources, environment variables, and probe configurations
   - Use appropriate defaults for resource limits and requests
   - Parameterize all environment-specific values

4. **Deployment Commands**:
   ```bash
   # Install/upgrade the chart
   helm upgrade --install release-name ./zgrid-chart -f values.yaml
   
   # Deploy with custom values
   helm upgrade --install release-name ./zgrid-chart -f custom-values.yaml
   
   # Check deployment status
   helm status release-name
   
   # View deployed resources
   kubectl get all -n namespace
   ```

### Kubernetes Ingress Configuration

1. **Subdomain-based Routing**: Configure separate subdomains for each service:
   ```yaml
   ingress:
     enabled: true
     className: "nginx"
     annotations:
       kubernetes.io/ingress.class: nginx
       nginx.ingress.kubernetes.io/ssl-redirect: "true"
       cert-manager.io/cluster-issuer: letsencrypt-prod
     hosts:
       - host: service1.example.com
         paths:
           - path: /
             pathType: ImplementationSpecific
       - host: service2.example.com
         paths:
           - path: /
             pathType: ImplementationSpecific
     tls:
       - hosts:
           - service1.example.com
           - service2.example.com
         secretName: services-tls
   ```

2. **Path-based Routing**: Alternative approach using paths:
   ```yaml
   ingress:
     enabled: true
     className: "nginx"
     annotations:
       kubernetes.io/ingress.class: nginx
       nginx.ingress.kubernetes.io/ssl-redirect: "true"
       cert-manager.io/cluster-issuer: letsencrypt-prod
     hosts:
       - host: services.example.com
         paths:
           - path: /service1
             pathType: ImplementationSpecific
           - path: /service2
             pathType: ImplementationSpecific
     tls:
       - hosts:
           - services.example.com
         secretName: services-tls
   ```

### CI/CD Integration Recommendations

1. **Automated Building**: Set up CI pipelines to automatically build and push images on code changes
2. **Versioning Strategy**: Use git tags or commit hashes for image tagging
3. **Security Scanning**: Integrate vulnerability scanning in the CI pipeline
4. **Automated Deployment**: Configure CD pipelines to deploy to staging/production environments
5. **Testing**: Include integration tests in the deployment pipeline

### Scaling and Monitoring

1. **Resource Management**: Set appropriate CPU and memory requests/limits
2. **Horizontal Scaling**: Configure replica counts based on expected load
3. **Health Checks**: Implement proper liveness and readiness probes
4. **Monitoring**: Add Prometheus metrics and Grafana dashboards
5. **Logging**: Centralize logs with tools like ELK or similar stack