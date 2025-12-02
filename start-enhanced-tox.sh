#!/bin/bash
# Script to start enhanced toxicity service

echo "🚀 Starting Enhanced Toxicity Service with ML Models..."

# Verify enhanced dependencies are installed
python -c "
try:
    import detoxify
    print('✅ Detoxify ML model imported successfully')
    import better_profanity
    print('✅ Better profanity imported successfully')
    import regex
    print('✅ Regex module imported successfully')
except ImportError as e:
    print(f'❌ Import error: {e}')
    exit(1)
"

echo "✅ All enhanced dependencies verified"

# Start the enhanced service
echo "🔄 Starting enhanced toxicity service..."
python enhanced_app.py