#!/usr/bin/env python3
"""
Inetuned Gibbrish Model Service
Production-ready gibberish detection with 96.7% accuracy
"""

import os
import json
import logging
import time
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configuration
PORT = int(os.environ.get('FLASK_RUN_PORT', 8007))
MODEL_PATH = os.environ.get('MODEL_PATH', '/app/models/inetuned_gibbrish_model')
CONFIDENCE_THRESHOLD = float(os.environ.get('CONFIDENCE_THRESHOLD', 0.5))
MAX_SEQUENCE_LENGTH = int(os.environ.get('MAX_SEQUENCE_LENGTH', 512))
DEVICE = os.environ.get('DEVICE', 'cpu')

# Global variables
model = None
tokenizer = None
start_time = datetime.now()

class GibberishRequest:
    def __init__(self, data):
        self.text = data.get('text', '')
        self.threshold = data.get('threshold', CONFIDENCE_THRESHOLD)

class GibberishResponse:
    def __init__(self, text, is_gibberish, confidence, processing_time, model_info):
        self.text = text
        self.is_gibberish = is_gibberish
        self.confidence = confidence
        self.processing_time_ms = processing_time
        self.model_info = model_info
        self.timestamp = datetime.now().isoformat()

def load_model():
    """Load the inetuned gibberish model."""
    global model, tokenizer

    try:
        logger.info(f"Loading model from: {MODEL_PATH}")

        # Load tokenizer and model
        tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
        model = AutoModelForSequenceClassification.from_pretrained(MODEL_PATH)
        model.eval()

        # Device configuration
        if DEVICE == 'cuda' and torch.cuda.is_available():
            model = model.cuda()
            logger.info("✅ Using CUDA GPU")
        elif DEVICE == 'mps' and torch.backends.mps.is_available():
            model = model.to(torch.device("mps"))
            logger.info("✅ Using MPS (Apple Silicon)")
        else:
            logger.info("✅ Using CPU")

        logger.info("✅ Model loaded successfully!")
        return True

    except Exception as e:
        logger.error(f"❌ Error loading model: {e}")
        return False

def predict_gibberish(text):
    """Predict if text is gibberish."""
    try:
        if not model or not tokenizer:
            return None

        # Tokenize input
        inputs = tokenizer(
            text,
            return_tensors='pt',
            truncation=True,
            padding=True,
            max_length=MAX_SEQUENCE_LENGTH
        )

        # Move to device
        if DEVICE == 'cuda' and torch.cuda.is_available():
            inputs = {k: v.cuda() for k, v in inputs.items()}
        elif DEVICE == 'mps' and torch.backends.mps.is_available():
            inputs = {k: v.to(torch.device("mps")) for k, v in inputs.items()}

        # Predict
        with torch.no_grad():
            outputs = model(**inputs)
            probs = torch.softmax(outputs.logits, dim=-1)

            # Assuming binary classification: [not_gibberish, gibberish]
            gibberish_prob = probs[0][1].item()
            is_gibberish = gibberish_prob > CONFIDENCE_THRESHOLD

            return {
                'is_gibberish': is_gibberish,
                'confidence': gibberish_prob,
                'not_gibberish_prob': probs[0][0].item()
            }

    except Exception as e:
        logger.error(f"Error in prediction: {e}")
        return None

@app.route('/')
def index():
    """Service information endpoint."""
    return jsonify({
        "service": "Inetuned Gibbrish Detection Service",
        "version": "v2.0",
        "model_type": "inetuned",
        "training_accuracy": "96.7%",
        "f1_score": "0.944",
        "dataset_size": "298 samples",
        "status": "running" if model is not None else "loading",
        "endpoints": {
            "health": "GET /health",
            "detect": "POST /detect",
            "batch_detect": "POST /batch_detect",
            "model_info": "GET /model_info"
        }
    })

@app.route('/health')
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy" if model is not None else "unhealthy",
        "model_loaded": model is not None,
        "timestamp": datetime.now().isoformat(),
        "uptime_seconds": (datetime.now() - start_time).total_seconds()
    })

@app.route('/model_info')
def model_info():
    """Model information endpoint."""
    return jsonify({
        "service": "Inetuned Gibbrish Detection Service",
        "version": "v2.0",
        "model_type": "inetuned",
        "model_path": MODEL_PATH,
        "training_accuracy": "96.7%",
        "f1_score": "0.944",
        "dataset_size": "298 samples",
        "architecture": "Fine-tuned transformer",
        "device": DEVICE,
        "max_sequence_length": MAX_SEQUENCE_LENGTH,
        "confidence_threshold": CONFIDENCE_THRESHOLD
    })

@app.route('/detect', methods=['POST'])
def detect_gibberish():
    """Detect gibberish in text."""
    start = time.time()

    try:
        if not model:
            return jsonify({"error": "Model not loaded"}), 503

        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({"error": "Missing 'text' field in request"}), 400

        text = data['text']
        if not isinstance(text, str) or not text.strip():
            return jsonify({"error": "Invalid text input"}), 400

        # Predict
        result = predict_gibberish(text.strip())
        if not result:
            return jsonify({"error": "Prediction failed"}), 500

        processing_time = (time.time() - start) * 1000

        response = {
            "text": text.strip(),
            "is_gibberish": result['is_gibberish'],
            "confidence": round(result['confidence'], 4),
            "not_gibberish_prob": round(result['not_gibberish_prob'], 4),
            "processing_time_ms": round(processing_time, 2),
            "threshold_used": CONFIDENCE_THRESHOLD,
            "model_info": {
                "model_type": "inetuned",
                "accuracy": "96.7%"
            },
            "timestamp": datetime.now().isoformat()
        }

        return jsonify(response)

    except Exception as e:
        logger.error(f"Error in detect_gibberish: {e}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

@app.route('/batch_detect', methods=['POST'])
def batch_detect_gibberish():
    """Batch detect gibberish in multiple texts."""
    start = time.time()

    try:
        if not model:
            return jsonify({"error": "Model not loaded"}), 503

        data = request.get_json()
        if not data or 'texts' not in data:
            return jsonify({"error": "Missing 'texts' field in request"}), 400

        texts = data['texts']
        if not isinstance(texts, list):
            return jsonify({"error": "'texts' must be an array"}), 400

        if len(texts) > 100:  # Limit batch size
            return jsonify({"error": "Batch size too large (max 100)"}), 400

        results = []
        for text in texts:
            if isinstance(text, str) and text.strip():
                result = predict_gibberish(text.strip())
                if result:
                    results.append({
                        "text": text.strip(),
                        "is_gibberish": result['is_gibberish'],
                        "confidence": round(result['confidence'], 4),
                        "not_gibberish_prob": round(result['not_gibberish_prob'], 4)
                    })
                else:
                    results.append({
                        "text": text.strip(),
                        "error": "Prediction failed"
                    })
            else:
                results.append({
                    "text": str(text) if text else "",
                    "error": "Invalid text input"
                })

        processing_time = (time.time() - start) * 1000

        return jsonify({
            "results": results,
            "batch_size": len(results),
            "processing_time_ms": round(processing_time, 2),
            "model_info": {
                "model_type": "inetuned",
                "accuracy": "96.7%"
            },
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error in batch_detect_gibberish: {e}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

if __name__ == '__main__':
    logger.info("🚀 Starting Inetuned Gibbrish Detection Service")

    # Load model
    if load_model():
        logger.info("✅ Service ready to handle requests")
    else:
        logger.error("❌ Failed to load model - service will start but cannot process requests")

    # Start Flask app
    app.run(host='0.0.0.0', port=PORT, debug=False)