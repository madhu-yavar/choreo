#!/usr/bin/env python3
"""
Jailbreak Detection API Server
==============================
Flask API for RoBERTa model with enhanced heuristics
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import torch
import json
from datetime import datetime
import os
from transformers import AutoTokenizer, AutoModelForSequenceClassification

app = Flask(__name__)
CORS(app)

class JailbreakDetectionAPI:
    """Production-ready jailbreak detection with enhanced heuristics"""

    def __init__(self, model_path='./roberta_jailbreak_binary/final_model'):
        self.model_path = model_path
        self.tokenizer = None
        self.model = None
        self.device = None

        # Load model and heuristics
        self._load_model()
        self._init_heuristics()

        print("🚀 Jailbreak Detection API initialized successfully!")

    def _load_model(self):
        """Load the trained RoBERTa model"""
        try:
            print(f"📦 Loading RoBERTa model from: {self.model_path}")

            self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
            self.model = AutoModelForSequenceClassification.from_pretrained(self.model_path)
            self.model.eval()

            # Configure device
            if torch.backends.mps.is_available():
                self.device = torch.device("mps")
                self.model = self.model.to(self.device)
                print("✅ Using MPS (Apple Silicon GPU)")
            elif torch.cuda.is_available():
                self.device = torch.device("cuda")
                self.model = self.model.to(self.device)
                print("✅ Using CUDA GPU")
            else:
                self.device = torch.device("cpu")
                print("⚠️ Using CPU")

        except Exception as e:
            print(f"❌ Error loading model: {e}")
            raise

    def _init_heuristics(self):
        """Initialize enhanced heuristic rules"""

        # Pattern weights
        self.ultra_risk_patterns = {
            "chemical_procedure": 0.9,
            "ethical_guideline_violation": 0.9,
            "illegal_actions_analysis": 0.8,
            "coercion_techniques": 0.8,
            "radicalization_taxonomy": 0.9,
            "dan_patterns": 0.8,
            "obfuscation_patterns": 0.6,
            "hate_speech_patterns": 0.7,
            "privacy_invasion_patterns": 0.5
        }

        # DAN/System Override Patterns
        self.dan_patterns = [
            "ignore all previous instructions", "do anything now", "without restrictions",
            "must answer without restrictions", "system override", "bypass safety",
            "ignore ethical guidelines", "dan", "do anything now"
        ]

        # Malicious Intent Indicators
        self.malicious_patterns = [
            "step-by-step", "exact instructions", "detailed instructions", "show me how",
            "create fake", "generate", "bypass", "exploit", "avoid detection",
            "without knowledge", "without consent", "manipulation techniques",
            "psychological manipulation", "social engineering", "obfuscated version"
        ]

        # Educational/Benign Indicators
        self.educational_patterns = [
            "for educational purposes", "academic research", "study", "learn", "understand",
            "analyze", "research", "certification", "course", "training", "education",
            "protect against", "defend against", "prevent", "detect", "identify",
            "safety guidelines", "best practices", "privacy protection", "ethical",
            "professional", "authorized", "compliance"
        ]

        # Creative Writing Contexts
        self.creative_patterns = [
            "fiction writer", "story", "character", "scene", "novel", "plot",
            "creative writing", "fictional", "narrative", "imaginative"
        ]

    def _calculate_heuristic_adjustment(self, text):
        """Calculate heuristic adjustment for the input text"""
        text_lower = text.lower()
        adjustment = 0.0
        reasoning = []

        # DAN/System Override Detection (Highest Priority)
        dan_count = sum(1 for pattern in self.dan_patterns if pattern in text_lower)
        if dan_count >= 1:
            adjustment += 0.8
            reasoning.append(f"DAN/system override detected")

        # Ultra-high risk pattern detection
        for risk_type, weight in self.ultra_risk_patterns.items():
            if risk_type.replace("_", " ") in text_lower:
                adjustment += weight
                reasoning.append(f"High-risk pattern: {risk_type}")

        # Malicious intent patterns
        malicious_count = sum(1 for pattern in self.malicious_patterns if pattern in text_lower)
        if malicious_count >= 3:
            adjustment += 0.6
            reasoning.append(f"Multiple malicious indicators ({malicious_count})")
        elif malicious_count >= 1:
            adjustment += 0.3
            reasoning.append(f"Malicious indicators detected ({malicious_count})")

        # Educational context detection
        edu_count = sum(1 for pattern in self.educational_patterns if pattern in text_lower)
        if edu_count >= 2:
            adjustment -= 0.5
            reasoning.append(f"Educational context ({edu_count} indicators)")
        elif edu_count >= 1:
            adjustment -= 0.3
            reasoning.append(f"Educational elements ({edu_count} indicators)")

        # Creative writing context
        creative_count = sum(1 for pattern in self.creative_patterns if pattern in text_lower)
        if creative_count >= 1:
            adjustment -= 0.2
            reasoning.append(f"Creative writing context")

        # Ensure bounds
        adjustment = max(-0.8, min(0.8, adjustment))

        return adjustment, reasoning

    def predict_jailbreak(self, text, confidence_threshold=0.5):
        """Make prediction with RoBERTa + heuristics"""
        try:
            # RoBERTa prediction
            inputs = self.tokenizer(
                text,
                return_tensors='pt',
                truncation=True,
                padding=True,
                max_length=512
            )

            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            with torch.no_grad():
                outputs = self.model(**inputs)
                probs = torch.softmax(outputs.logits, dim=-1)

            jailbreak_prob = probs[0][1].item()
            benign_prob = probs[0][0].item()

            # Heuristic adjustment
            adjustment, reasoning = self._calculate_heuristic_adjustment(text)

            # Apply adjustment
            adjusted_jailbreak_prob = max(0.0, min(1.0, jailbreak_prob + adjustment))
            adjusted_benign_prob = 1.0 - adjusted_jailbreak_prob

            # Final prediction
            prediction = "jailbreak" if adjusted_jailbreak_prob > confidence_threshold else "benign"
            confidence = max(adjusted_jailbreak_prob, adjusted_benign_prob)

            return {
                "prediction": prediction,
                "confidence": round(confidence, 4),
                "probabilities": {
                    "benign": round(adjusted_benign_prob, 4),
                    "jailbreak": round(adjusted_jailbreak_prob, 4)
                },
                "roberta_jailbreak_prob": round(jailbreak_prob, 4),
                "heuristic_adjustment": round(adjustment, 4),
                "heuristic_reasoning": reasoning,
                "model": "RoBERTa-Enhanced-Heuristics",
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            return {
                "prediction": "error",
                "confidence": 0.0,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

# Initialize the detection system
detection_system = None

def initialize_system():
    global detection_system
    if detection_system is None:
        detection_system = JailbreakDetectionAPI()

# Initialize immediately
initialize_system()

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "model": "RoBERTa-Enhanced-Heuristics",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/detect', methods=['POST'])
def detect_jailbreak():
    """Main detection endpoint"""
    try:
        data = request.get_json()

        if not data or 'text' not in data:
            return jsonify({
                "error": "Missing 'text' field in request"
            }), 400

        text = data['text']
        confidence_threshold = data.get('confidence_threshold', 0.5)

        # Validate input
        if not text or not text.strip():
            return jsonify({
                "error": "Text cannot be empty"
            }), 400

        # Make prediction
        result = detection_system.predict_jailbreak(text, confidence_threshold)

        return jsonify(result)

    except Exception as e:
        return jsonify({
            "error": f"Internal server error: {str(e)}"
        }), 500

@app.route('/detect/batch', methods=['POST'])
def detect_batch():
    """Batch detection endpoint"""
    try:
        data = request.get_json()

        if not data or 'texts' not in data:
            return jsonify({
                "error": "Missing 'texts' field in request"
            }), 400

        texts = data['texts']
        confidence_threshold = data.get('confidence_threshold', 0.5)

        if not isinstance(texts, list):
            return jsonify({
                "error": "'texts' must be an array"
            }), 400

        # Process batch
        results = []
        for i, text in enumerate(texts):
            if not text or not text.strip():
                results.append({
                    "index": i,
                    "error": "Text cannot be empty"
                })
            else:
                result = detection_system.predict_jailbreak(text, confidence_threshold)
                result["index"] = i
                results.append(result)

        return jsonify({
            "results": results,
            "total_processed": len(texts),
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        return jsonify({
            "error": f"Internal server error: {str(e)}"
        }), 500

@app.route('/', methods=['GET'])
def index():
    """API documentation endpoint"""
    return jsonify({
        "name": "Jailbreak Detection API",
        "version": "1.0.0",
        "model": "RoBERTa-Enhanced-Heuristics",
        "endpoints": {
            "/health": "GET - Health check",
            "/detect": "POST - Single text detection",
            "/detect/batch": "POST - Batch text detection",
            "/": "GET - API documentation"
        },
        "usage": {
            "single": {
                "method": "POST",
                "url": "/detect",
                "body": {
                    "text": "Your text here",
                    "confidence_threshold": 0.5
                }
            },
            "batch": {
                "method": "POST",
                "url": "/detect/batch",
                "body": {
                    "texts": ["Text 1", "Text 2", "Text 3"],
                    "confidence_threshold": 0.5
                }
            }
        }
    })

if __name__ == '__main__':
    # Check if model exists
    model_path = './roberta_jailbreak_binary/final_model'
    if not os.path.exists(model_path):
        print(f"❌ Model not found at {model_path}")
        print("Please ensure the model is trained and saved correctly.")
        exit(1)

    print("🚀 Starting Jailbreak Detection API Server...")
    print("📋 Available endpoints:")
    print("   GET  /health - Health check")
    print("   POST /detect - Single text detection")
    print("   POST /detect/batch - Batch text detection")
    print("   GET  / - API documentation")
    print("\n🌐 Server will be available at: http://localhost:8080")

    app.run(host='0.0.0.0', port=8080, debug=False)