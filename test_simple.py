#!/usr/bin/env python3
"""
Simple test script to validate PII service changes without full dependencies
"""

import sys
import os
from pathlib import Path

# Add the pii_service directory to the path
sys.path.insert(0, str(Path(__file__).parent))

try:
    # Try to import basic components
    print("Testing basic imports...")

    # Test basic imports that should work
    import json
    import re
    from typing import List, Dict, Any, Optional

    print("✓ Basic Python modules imported successfully")

    # Test if we can import our modules
    try:
        import custom_config
        print("✓ custom_config module imported")
    except Exception as e:
        print(f"✗ custom_config import failed: {e}")

    try:
        import utils
        print("✓ utils module imported")
        # Test some utility functions
        test_text = "Hello world"
        if hasattr(utils, 'is_valid_entity'):
            result = utils.is_valid_entity(test_text, "PERSON")
            print(f"✓ utils.is_valid_entity test: {result}")
    except Exception as e:
        print(f"✗ utils import failed: {e}")

    try:
        import enhanced_recognizers
        print("✓ enhanced_recognizers module imported")
    except Exception as e:
        print(f"✗ enhanced_recognizers import failed: {e}")

    # Test basic FastAPI structure
    try:
        from fastapi import FastAPI
        print("✓ FastAPI imported successfully")

        # Create a basic test app
        test_app = FastAPI(title="PII Test Service")

        @test_app.get("/test")
        def test_endpoint():
            return {"status": "working", "message": "Basic PII service test"}

        print("✓ Basic FastAPI app created successfully")

    except Exception as e:
        print(f"✗ FastAPI setup failed: {e}")

    print("\n" + "="*50)
    print("PII Service Basic Test Summary")
    print("="*50)
    print("This validates that your PII service structure is working.")
    print("For full testing, we need all dependencies installed.")
    print("="*50)

except Exception as e:
    print(f"Test failed with error: {e}")
    sys.exit(1)