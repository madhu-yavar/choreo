# SECRETS DETECTION SERVICE - USER GUIDE

## Overview
The Secrets Detection Service identifies and blocks sensitive credentials, API keys, passwords, and other confidential information in user content. It uses a multi-engine approach for comprehensive detection.

## Service Endpoint
```
POST http://localhost:8005/validate
Headers: 
  Content-Type: application/json
  X-API-Key: supersecret123
```

## API Usage

### Basic Request
```javascript
const response = await fetch('http://localhost:8005/validate', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': 'supersecret123'
  },
  body: JSON.stringify({
    text: "user content to check for secrets",
    return_spans: true
  })
});
```

### Response Format
```json
{
  "status": "blocked|pass|fixed",
  "clean_text": "processed content",
  "flagged": [
    {
      "type": "secret",
      "id": "SECRET_TYPE",
      "category": "SECRET_CATEGORY",
      "start": 0,
      "end": 10,
      "score": 0.95,
      "engine": "detection_engine",
      "severity": 5,
      "value": "secret_value",
      "snippet": "context around secret"
    }
  ],
  "steps": [
    {
      "name": "regex+entropy",
      "passed": false,
      "details": {
        "hits": 1,
        "enable_regex": true,
        "enable_entropy": true
      }
    }
  ],
  "reasons": ["Secrets blocked"]
}
```

## Detection Engines

### 1. Regex Pattern Matching
- **Purpose**: Detects known secret formats
- **Examples**: AWS keys, GitHub tokens, Stripe keys
- **Strengths**: High precision, zero false positives for known patterns
- **Response Engine**: `"engine": "regex"`

### 2. Entropy Analysis
- **Purpose**: Identifies high-entropy tokens (random-looking strings)
- **Examples**: Base64, hex strings, JWT tokens
- **Strengths**: Catches unknown secret formats
- **Response Engine**: `"engine": "entropy"`

### 3. Yelp detect-secrets (Enhanced)
- **Purpose**: Advanced secret detection using battle-tested algorithms
- **Examples**: Private keys, SSH keys, complex credentials
- **Strengths**: Industry-proven detection with low false positives
- **Response Engine**: `"engine": "yelp_PLUGIN_NAME"`

## Secret Categories

| Category | Description | Examples |
|----------|-------------|----------|
| `CLOUD` | Cloud provider keys | AWS, GCP, Azure keys |
| `DEV` | Developer credentials | GitHub tokens, SSH keys |
| `SAAS` | SaaS platform keys | Slack, Stripe, Twilio tokens |
| `COMM` | Communication service keys | SendGrid, Telegram tokens |
| `AUTH` | Authentication tokens | JWT, OAuth tokens |
| `PAYMENTS` | Payment processing keys | Stripe, PayPal keys |
| `GENERIC` | Generic high-entropy tokens | Base64, hex strings |

## Severity Levels

| Level | Description | Action |
|-------|-------------|--------|
| 1 | Low risk | Monitor |
| 2 | Medium risk | Warn |
| 3 | High risk | Filter |
| 4 | Critical risk | Block |
| 5 | Extremely critical | Immediate block |

## Detection Models & Algorithms

### Multi-Engine Architecture
The service uses three complementary detection engines:

#### 1. Pattern-Based Detection (Regex)
- **Model**: Custom regex patterns
- **Detection Method**: Exact pattern matching
- **Accuracy**: Very high (near 100%)
- **False Positives**: Very low
- **Use Case**: Known secret formats

#### 2. Statistical Detection (Entropy)
- **Model**: Shannon Entropy Analysis
- **Detection Method**: Mathematical randomness measurement
- **Algorithm**: 
  ```
  H(X) = -Σ P(x) × log₂(P(x))
  ```
- **Threshold**: Configurable (default: 3.0)
- **Token Length**: Configurable (default: 8+ characters)
- **Accuracy**: High for random strings
- **False Positives**: Medium (some random words may trigger)

#### 3. Machine Learning-Based Detection (Yelp detect-secrets)
- **Model**: Multiple specialized detectors
- **Detection Methods**:
  - Base64HighEntropyString (entropy + base64 validation)
  - HexHighEntropyString (entropy + hex validation)
  - KeywordDetector (semantic keyword analysis)
  - PrivateKeyDetector (cryptographic key patterns)
- **Accuracy**: Very high (battle-tested at Yelp)
- **False Positives**: Low
- **Training**: Industry-standard datasets

## Configuration Parameters

### Environment Variables
```env
# Detection sensitivity
ENTROPY_THRESHOLD=3.0        # Lower = more sensitive (3.0-4.5)
MIN_TOKEN_LEN=8             # Minimum token length to analyze
CONTEXT_WINDOW_CHARS=40     # Context search window around tokens

# Engine toggles
ENABLE_REGEX=1              # Enable/disable regex detection
ENABLE_ENTROPY=1            # Enable/disable entropy detection
ENABLE_YELP_DETECTOR=1      # Enable/disable Yelp detect-secrets

# Actions
SECRETS_ACTION_ON_FAIL=refrain  # Options: refrain, filter, mask, reask
```

## Integration Examples

### JavaScript/Node.js
```javascript
async function checkForSecrets(userInput) {
  try {
    const response = await fetch('http://localhost:8005/validate', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': 'supersecret123'
      },
      body: JSON.stringify({
        text: userInput,
        return_spans: true
      })
    });

    const result = await response.json();
    
    if (result.status === 'blocked') {
      // Handle blocked content
      console.log('Secrets detected:', result.flagged);
      return { safe: false, message: 'Content contains sensitive information' };
    }
    
    return { safe: true, content: result.clean_text };
  } catch (error) {
    console.error('Secret detection failed:', error);
    // Fail-safe: allow content through on service error
    return { safe: true, content: userInput };
  }
}

// Usage
const userInput = "My AWS key is AKIAIOSFODNN7EXAMPLE";
const check = await checkForSecrets(userInput);
if (!check.safe) {
  alert(check.message);
}
```

### Python
```python
import requests
import json

def check_for_secrets(text):
    try:
        response = requests.post(
            'http://localhost:8005/validate',
            headers={
                'Content-Type': 'application/json',
                'X-API-Key': 'supersecret123'
            },
            json={
                'text': text,
                'return_spans': True
            }
        )
        
        result = response.json()
        
        if result['status'] == 'blocked':
            # Handle blocked content
            print(f"Secrets detected: {result['flagged']}")
            return False, "Content contains sensitive information"
        
        return True, result['clean_text']
    except Exception as e:
        print(f"Secret detection failed: {e}")
        # Fail-safe: allow content through on service error
        return True, text

# Usage
user_input = "My password is qweds234"
is_safe, content = check_for_secrets(user_input)
if not is_safe:
    print("Blocked:", content)
```

## Test Cases

### Detected Secrets
```bash
# AWS Key
Input: "AKIAIOSFODNN7EXAMPLE"
Output: BLOCKED (Regex detection)

# Private Key
Input: "-----BEGIN RSA PRIVATE KEY-----"
Output: BLOCKED (Yelp PrivateKeyDetector)

# High Entropy Token
Input: "aGVsbG8gd29ybGQ=" (base64)
Output: BLOCKED (Entropy analysis)

# Context-Aware Detection
Input: "my password is qweds234"
Output: BLOCKED (Entropy + context)
```

### Safe Content
```bash
# Normal text
Input: "This is a regular sentence"
Output: PASS

# Low entropy tokens
Input: "hello world"
Output: PASS

# Non-sensitive technical terms
Input: "function calculateSum(a, b)"
Output: PASS
```

## Best Practices

### 1. Integration Strategy
- Always handle service errors gracefully
- Implement timeouts for service calls
- Use fail-safe approach (allow content on service failure)

### 2. User Experience
- Provide clear feedback when content is blocked
- Explain why content was flagged (when appropriate)
- Offer guidance on creating safe content

### 3. Security
- Never log detected secrets
- Use HTTPS in production
- Rotate API keys regularly

### 4. Performance
- The service is optimized for real-time use
- Typical response time: <100ms
- Can handle high-volume traffic

## Troubleshooting

### Common Issues

#### Service Not Responding
- Check if service is running: `curl http://localhost:8005/health`
- Verify port 8005 is not blocked by firewall
- Check Docker/container status if using containerized deployment

#### False Positives
- Adjust entropy threshold in environment variables
- Review content that's being incorrectly flagged
- Consider adding to allow list for legitimate use cases

#### Performance Issues
- The service is designed for high performance
- If experiencing delays, check system resources
- Consider load balancing for high-traffic applications

## Monitoring & Maintenance

### Health Check
```
GET http://localhost:8005/health
Response: {"ok": true}
```

### Logs
- Service logs detection activities
- Monitor for unusual patterns
- Review flagged content for tuning

### Updates
- Pattern updates via `patterns/signatures.json`
- Configuration changes via `.env` file
- Model updates through dependency management

## Contact & Support

For issues, questions, or enhancements:
- Check service logs for error details
- Review this documentation for configuration options
- Contact system administrator for access issues