#!/usr/bin/env python3
"""
Production-ready Gibberish Detection API with Inetuned Gibbrish Model
"""

from flask import Flask, request, jsonify
import os
import sys
import time
import signal
from inetuned_gibbrish_detector import InetunedGibbrishDetector

app = Flask(__name__)

# Global detector instance
detector = None

def load_model():
    """Load the Inetuned Gibbrish Model"""
    global detector
    try:
        print('🚀 Loading Inetuned Gibbrish Model...')
        checkpoint_path = os.environ.get('MODEL_PATH', '/app/models/hf_space_efficient/inetuned_gibbrish_model')
        detector = InetunedGibbrishDetector(model_name=None, local_model_path=checkpoint_path)

        if not detector.is_loaded:
            print('❌ Failed to load model')
            return False

        print('✅ Inetuned Gibbrish Model loaded successfully!')
        print('📊 Training accuracy: 96.7%')
        print('🎯 Model: inetuned_gibbrish_model')
        return True
    except Exception as e:
        print(f'❌ Error loading model: {e}')
        return False

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        'service': 'Gibberish Detection API',
        'model': 'Inetuned Gibbrish Model',
        'model_version': 'v1.0',
        'training_accuracy': '96.7%',
        'f1_score': '0.944',
        'dataset_size': '298 samples',
        'checkpoint': 'inetuned_gibbrish_model',
        'endpoints': {
            'detect': 'POST /detect - Single text detection',
            'batch_detect': 'POST /batch_detect - Multiple texts',
            'health': 'GET /health - Health check',
            'model_info': 'GET /model_info - Model details'
        },
        'status': 'ready'
    })

@app.route('/detect', methods=['POST'])
def detect_gibberish():
    """Detect gibberish in a single text"""
    try:
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({'error': 'Missing text field'}), 400

        text = data['text']
        if not isinstance(text, str):
            return jsonify({'error': 'Text must be a string'}), 400

        start_time = time.time()
        result = detector.detect(text)
        inference_time = time.time() - start_time

        result['inference_time_ms'] = round(inference_time * 1000, 2)
        result['model_type'] = 'fine-tuned-huggingface'

        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/batch_detect', methods=['POST'])
def batch_detect():
    """Detect gibberish in multiple texts"""
    try:
        data = request.get_json()
        if not data or 'texts' not in data:
            return jsonify({'error': 'Missing texts field'}), 400

        texts = data['texts']
        if not isinstance(texts, list):
            return jsonify({'error': 'Texts must be an array'}), 400

        start_time = time.time()
        results = []

        for i, text in enumerate(texts):
            if not isinstance(text, str):
                results.append({
                    'index': i,
                    'text': text,
                    'error': 'Text must be a string',
                    'is_gibberish': False,
                    'confidence': 0.0
                })
            else:
                result = detector.detect(text)
                result['index'] = i
                results.append(result)

        inference_time = time.time() - start_time

        return jsonify({
            'results': results,
            'total_texts': len(texts),
            'inference_time_ms': round(inference_time * 1000, 2),
            'model_type': 'fine-tuned-huggingface'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy' if detector and detector.is_loaded else 'unhealthy',
        'model_loaded': detector.is_loaded if detector else False,
        'model_path': '/app/models/hf_space_efficient/inetuned_gibbrish_model',
        'model_type': 'inetuned',
        'model_version': 'v1.0',
        'training_accuracy': '96.7%'
    })

@app.route('/model_info', methods=['GET'])
def model_info():
    """Get detailed model information"""
    return jsonify({
        'model_type': 'inetuned',
        'model_version': 'v1.0',
        'checkpoint_path': '/app/models/hf_space_efficient/inetuned_gibbrish_model',
        'training_dataset_size': 298,
        'training_accuracy': 0.967,
        'training_f1_score': 0.944,
        'training_epochs': 10,
        'space_efficient': True,
        'labels_supported': ['clean', 'mild gibberish', 'word salad', 'noise'],
        'device': 'cpu'
    })

if __name__ == '__main__':
    def signal_handler(sig, frame):
        print('\n🛑 Shutting down server...')
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Load model before starting server
    if not load_model():
        print('❌ Failed to start server - model loading failed')
        sys.exit(1)

    print('\n🌐 Starting Production Gibberish Detection API Server...')
    print('=' * 60)
    port = int(os.environ.get('FLASK_RUN_PORT', 8007))
    print(f'📍 Server: http://localhost:{port}')
    print(f'📍 Health: http://localhost:{port}/health')
    print(f'📍 Model Info: http://localhost:{port}/model_info')
    print(f'📍 Detect: POST http://localhost:{port}/detect')
    print()
    print('💡 EXAMPLE CURL COMMANDS:')
    print()
    print(f'# Single text detection:')
    print(f'curl -X POST http://localhost:{port}/detect \\')
    print('  -H "Content-Type: application/json" \\')
    print('  -d \'{"text": "your test text here"}\'')
    print()
    print('# Batch detection:')
    print(f'curl -X POST http://localhost:{port}/batch_detect \\')
    print('  -H "Content-Type: application/json" \\')
    print('  -d \'{"texts": ["text 1", "text 2", "text 3"]}\'')
    print()
    print('# Health check:')
    print(f'curl -X GET http://localhost:{port}/health')
    print()
    print('🎯 Press Ctrl+C to stop the server')
    print('=' * 60)

    app.run(host='0.0.0.0', port=port, debug=False)