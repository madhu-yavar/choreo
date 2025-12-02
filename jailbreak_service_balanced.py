#!/usr/bin/env python3
"""
Balanced Jailbreak Detection Service
Uses the balanced DistilBERT model trained on 52.9%/47.1% jailbreak/benign data
"""

import os
import torch
import logging
import json
from datetime import datetime
from flask import Flask, request, jsonify
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from typing import Dict, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# API Configuration
API_KEYS = os.environ.get('JAILBREAK_API_KEYS', 'supersecret123,jailvalyavar').split(',')

# Model configuration - using our balanced model
MODEL_PATH = os.environ.get('BALANCED_MODEL_PATH', './jailbreak_model_balanced_retrained/checkpoint-49')
TOKENIZER_NAME = os.environ.get('TOKENIZER_NAME', 'distilbert-base-uncased')
CONFIDENCE_THRESHOLD = float(os.environ.get('CONFIDENCE_THRESHOLD', '0.5'))
MAX_SEQUENCE_LENGTH = int(os.environ.get('MAX_SEQUENCE_LENGTH', '512'))

# Global variables for model
model = None
tokenizer = None

def authenticate_request(request):
    """Authenticate API request"""
    api_key = request.headers.get('X-API-Key')
    return api_key in API_KEYS

def load_balanced_model():
    """Load the balanced DistilBERT model"""
    global model, tokenizer
    try:
        logger.info(f"Loading balanced model from: {MODEL_PATH}")
        logger.info(f"Loading tokenizer: {TOKENIZER_NAME}")

        # Load tokenizer (will download if not in cache)
        tokenizer = AutoTokenizer.from_pretrained(TOKENIZER_NAME)

        # Load our trained model
        model = AutoModelForSequenceClassification.from_pretrained(MODEL_PATH)
        model.eval()

        if torch.cuda.is_available():
            model = model.cuda()
            logger.info("Using GPU for inference")
        else:
            logger.info("Using CPU for inference")

        logger.info("✅ Balanced model loaded successfully!")
        return True

    except Exception as e:
        logger.error(f"❌ Error loading balanced model: {e}")
        return False

def predict_jailbreak(text: str) -> Dict:
    """Make prediction using the balanced model"""
    try:
        # Tokenize input
        inputs = tokenizer(
            text,
            return_tensors='pt',
            truncation=True,
            padding=True,
            max_length=MAX_SEQUENCE_LENGTH
        )

        # Move to GPU if available
        if torch.cuda.is_available():
            inputs = {k: v.cuda() for k, v in inputs.items()}

        # Make prediction
        with torch.no_grad():
            outputs = model(**inputs)
            probs = torch.softmax(outputs.logits, dim=-1)

        # Extract probabilities
        jailbreak_prob = probs[0][1].item() if probs.shape[0] > 1 else probs[1].item()
        benign_prob = probs[0][0].item() if probs.shape[0] > 1 else probs[0].item()

        # Determine prediction
        prediction = "jailbreak" if jailbreak_prob > CONFIDENCE_THRESHOLD else "benign"
        confidence = max(jailbreak_prob, benign_prob)

        return {
            "text": text,
            "prediction": prediction,
            "confidence": round(confidence, 4),
            "probabilities": {
                "benign": round(benign_prob, 4),
                "jailbreak": round(jailbreak_prob, 4)
            },
            "threshold_used": CONFIDENCE_THRESHOLD,
            "model_type": "balanced_distilbert",
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error making prediction: {e}")
        return {
            "text": text,
            "prediction": "error",
            "confidence": 0.0,
            "error": str(e),
            "model_type": "balanced_distilbert",
            "timestamp": datetime.now().isoformat()
        }

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint - no authentication required"""
    status = "healthy" if model is not None else "unhealthy"
    model_loaded = model is not None

    return jsonify({
        "status": status,
        "model_loaded": model_loaded,
        "model_type": "balanced_distilbert" if model_loaded else None,
        "timestamp": datetime.now().isoformat()
    })

@app.route('/detect', methods=['POST'])
def detect_jailbreak():
    """Main detection endpoint"""
    if not authenticate_request(request):
        return jsonify({"error": "Unauthorized"}), 401

    if model is None:
        return jsonify({"error": "Model not loaded"}), 503

    try:
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({"error": "Missing 'text' field in request"}), 400

        text = data['text']
        if not isinstance(text, str) or not text.strip():
            return jsonify({"error": "Invalid text input"}), 400

        # Make prediction
        result = predict_jailbreak(text)

        # Add request metadata
        result["request_id"] = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(text) % 10000:04d}"

        return jsonify(result)

    except Exception as e:
        logger.error(f"Error in detect_jailbreak: {e}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

@app.route('/batch_detect', methods=['POST'])
def batch_detect_jailbreak():
    """Batch detection endpoint"""
    if not authenticate_request(request):
        return jsonify({"error": "Unauthorized"}), 401

    if model is None:
        return jsonify({"error": "Model not loaded"}), 503

    try:
        data = request.get_json()
        if not data or 'texts' not in data:
            return jsonify({"error": "Missing 'texts' field in request"}), 400

        texts = data['texts']
        if not isinstance(texts, list) or not texts:
            return jsonify({"error": "Invalid texts input - must be non-empty list"}), 400

        if len(texts) > 100:  # Limit batch size
            return jsonify({"error": "Batch size too large - maximum 100 texts"}), 400

        results = []
        for text in texts:
            if not isinstance(text, str) or not text.strip():
                results.append({
                    "text": text,
                    "prediction": "error",
                    "confidence": 0.0,
                    "error": "Invalid text input"
                })
            else:
                results.append(predict_jailbreak(text))

        return jsonify({
            "results": results,
            "batch_size": len(texts),
            "model_type": "balanced_distilbert",
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error in batch_detect_jailbreak: {e}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

@app.route('/model_info', methods=['GET'])
def model_info():
    """Model information endpoint"""
    if not authenticate_request(request):
        return jsonify({"error": "Unauthorized"}), 401

    # Load model info from deployment file if exists
    model_info_file = "/app/deployment_model_info.json"
    default_info = {
        "model_type": "balanced_distilbert",
        "base_model": "distilbert-base-uncased",
        "training_dataset": "balanced_dataset_52.9_jailbreak_47.1_benign",
        "confidence_threshold": CONFIDENCE_THRESHOLD,
        "max_sequence_length": MAX_SEQUENCE_LENGTH,
        "model_loaded": model is not None
    }

    try:
        if os.path.exists(model_info_file):
            with open(model_info_file, 'r') as f:
                info = json.load(f)
                default_info.update(info)
        return jsonify(default_info)
    except Exception as e:
        logger.warning(f"Could not load model info file: {e}")
        return jsonify(default_info)

if __name__ == '__main__':
    logger.info("🚀 Starting Balanced Jailbreak Detection Service")

    # Load model
    if load_balanced_model():
        logger.info("✅ Service ready to handle requests")
    else:
        logger.error("❌ Failed to load model - service will start but cannot process requests")

    # Start Flask app
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)