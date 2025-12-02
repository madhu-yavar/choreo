#!/bin/bash
# Script to enhance the Secrets Service with better detection capabilities

echo "Enhancing Secrets Service detection capabilities..."

# Copy enhanced files to the secrets service directory
cp enhanced_detectors.py ../secrets_service/detectors.py
cp enhanced_signatures.json ../secrets_service/patterns/signatures.json

# Update the app.py to use enhanced configuration
# We'll modify the environment variables to make detection more sensitive

# Create a backup of the original .env file
cp ../secrets_service/.env ../secrets_service/.env.backup

# Update the .env file with enhanced settings
cat > ../secrets_service/.env << EOF
# Auth & CORS
SECRETS_API_KEYS=supersecret123,secretsvalyavar
CORS_ALLOWED_ORIGINS=https://zgrid-feature-flow.lovable.app,http://localhost:5173,http://localhost:3000

# Enhanced Detection toggles
ENABLE_REGEX=1
ENABLE_ENTROPY=1
ENABLE_CONTEXT=1
ENABLE_ENHANCED=1

# Enhanced Heuristics (more sensitive)
ENTROPY_THRESHOLD=3.5             # Lowered from 4.0 for better detection
MIN_TOKEN_LEN=15                  # Reduced from 20 for shorter secrets
CONTEXT_WINDOW_CHARS=50           # Increased from 40 for better context detection

# Action on match: refrain | filter | mask | reask
SECRETS_ACTION_ON_FAIL=refrain
MASK_TOKEN=***                    # used when action == mask

# Where to load patterns from (mounted in Docker)
PATTERNS_DIR=patterns

# Return full secret value in response? (0 hides; 1 returns)
RETURN_SECRET_VALUES=0
EOF

echo "Enhanced files copied and configuration updated."
echo "Restarting Secrets Service..."

# Kill the current secrets service process
pkill -f "localhost:8005" || true

# Wait a moment
sleep 2

# Start the enhanced secrets service
cd ../secrets_service && source ../format_service/new_env/bin/activate && python -m uvicorn app:app --host 0.0.0.0 --port 8005 --log-level info &

echo "Secrets Service restarted with enhanced detection capabilities."
echo "Testing enhanced detection..."

# Wait for service to start
sleep 5

# Test the enhanced detection
echo "Testing: 'sk - 1234567788900008bnghygdyt55656 and pwd is 123456'"
curl -X POST http://localhost:8005/validate \
  -H "Content-Type: application/json" \
  -H "X-API-Key: supersecret123" \
  -d '{"text":"sk - 1234567788900008bnghygdyt55656 and pwd is 123456","return_spans":true}'

echo ""
echo "Testing: 'password: mySecret123'"
curl -X POST http://localhost:8005/validate \
  -H "Content-Type: application/json" \
  -H "X-API-Key: supersecret123" \
  -d '{"text":"password: mySecret123","return_spans":true}'

echo ""
echo "Enhancement complete!"