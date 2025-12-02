#!/bin/bash
# Quick script to install enhanced dependencies in existing toxicity pod

echo "🔧 Installing enhanced toxicity detection packages..."

# Install enhanced packages
pip install --no-cache-dir better-profanity==0.7.0
pip install --no-cache-dir regex==2023.10.3

# Try to install detoxify (may fail gracefully)
pip install --no-cache-dir detoxify==0.5.0 || echo "⚠️ Detoxify install failed, will use pattern-based detection"

echo "✅ Enhanced dependencies installation complete"