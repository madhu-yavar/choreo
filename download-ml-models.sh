#!/bin/bash

echo "🤖 Pre-downloading Detoxify ML models..."

# Create HF cache directory
mkdir -p /app/models/hf_cache
export HUGGINGFACE_HUB_CACHE=/app/models/hf_cache

python3 -c "
import os
os.environ['HUGGINGFACE_HUB_CACHE'] = '/app/models/hf_cache'
print('Cache directory:', os.environ['HUGGINGFACE_HUB_CACHE'])
try:
    print('Downloading Detoxify original model...')
    from detoxify import Detoxify
    model = Detoxify('original')
    print('✅ Detoxify original model downloaded successfully')
    result = model.predict('test sentence')
    print('✅ Model prediction test successful')
    print('Available labels:', list(result.keys()))
except Exception as e:
    print(f'❌ Model download failed: {e}')
    exit(1)
"

if [ $? -eq 0 ]; then
    echo "✅ ML models successfully downloaded and tested"
else
    echo "❌ ML model setup failed"
    exit 1
fi