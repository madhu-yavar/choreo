# zGrid Services Test Scripts

This directory contains comprehensive test scripts for all zGrid services running on ports 8000-8006.

## Test Scripts Overview

1. **Individual Service Tests**:
   - `test_pii_service.py` - Tests PII Service (Port 8000)
   - `test_toxicity_service.py` - Tests Toxicity Service (Port 8001)
   - `test_jailbreak_service.py` - Tests Jailbreak Service (Port 8002)
   - `test_policy_service.py` - Tests Policy Service (Port 8003)
   - `test_ban_service.py` - Tests Ban Service (Port 8004)
   - `test_secrets_service.py` - Tests Secrets Service (Port 8005)
   - `test_format_service.py` - Tests Format Service (Port 8006)

2. **Combined Tests**:
   - `test_all_services.py` - Tests health endpoints of all services
   - `run_all_tests.sh` - Shell script to run all individual tests

3. **Curl Command Tests**:
   - `curl_tests.sh` - Execute all curl commands to test services
   - `show_curl_commands.sh` - Display curl commands without executing them
   - `CURL_COMMANDS.md` - Markdown file with all curl commands for reference

## How to Run Tests

### Run Individual Service Test
```bash
# Activate the virtual environment
source new_env/bin/activate

# Run a specific test
python test_pii_service.py
```

### Run All Services Health Check
```bash
# Activate the virtual environment
source new_env/bin/activate

# Run the combined health check
python test_all_services.py
```

### Run All Individual Tests
```bash
# Make sure the shell script is executable
chmod +x run_all_tests.sh

# Run all tests
./run_all_tests.sh
```

### Run Curl Tests
```bash
# Execute all curl commands and see results
./curl_tests.sh

# Display curl commands without executing them
./show_curl_commands.sh

# Or refer to the markdown file
cat CURL_COMMANDS.md
```

## Prerequisites

1. All zGrid services must be running on their respective ports
2. Python 3.11 virtual environment with all dependencies installed
3. `requests` library (should be installed in the virtual environment)
4. `curl` command-line tool (usually pre-installed on macOS and Linux)

## What the Tests Cover

Each test script performs the following checks:

1. **Health Check**: Verifies the service is running and responsive
2. **Functionality Tests**: Tests the main validation endpoints with sample data
3. **Error Handling**: Checks how the service handles various inputs

The tests provide clear output indicating whether each check passed or failed, along with details for any failures.

## Curl Command Examples

For quick testing from the terminal, you can use curl commands. Here are some examples:

### PII Service
```bash
# Health check
curl -X GET http://localhost:8000/health

# PII detection
curl -X POST http://localhost:8000/validate \
  -H "Content-Type: application/json" \
  -H "X-API-Key: supersecret123" \
  -d '{"text":"Contact me at john.doe@example.com or call me at 555-123-4567","entities":["EMAIL_ADDRESS","PHONE_NUMBER"],"return_spans":true}'
```

### Toxicity Service
```bash
# Health check
curl -X GET http://localhost:8001/health

# Toxicity detection
curl -X POST http://localhost:8001/validate \
  -H "Content-Type: application/json" \
  -H "X-API-Key: supersecret123" \
  -d '{"text":"This is a normal sentence.","return_spans":true}'
```

Refer to `CURL_COMMANDS.md` for a complete list of curl commands for all services.

## Customizing Tests

You can modify the test scripts to:
1. Change the test data
2. Add more test cases
3. Adjust timeout values
4. Modify the expected results

All test scripts use the default API key `supersecret123` which should work with the default service configurations.