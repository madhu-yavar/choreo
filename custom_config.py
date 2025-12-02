import json
import os
from pathlib import Path
from typing import List, Dict, Any

CUSTOM_FORMAT_DIR = Path("custom_configs")
CUSTOM_FORMAT_DIR.mkdir(exist_ok=True)

def save_custom_expressions(custom_expressions: List[str], service_name: str = "format_service"):
    """Save custom Cucumber expressions to a file"""
    file_path = CUSTOM_FORMAT_DIR / f"{service_name}_custom_expressions.json"
    with open(file_path, 'w') as f:
        json.dump(custom_expressions, f, indent=2)

def load_custom_expressions(service_name: str = "format_service") -> List[str]:
    """Load custom Cucumber expressions from a file"""
    file_path = CUSTOM_FORMAT_DIR / f"{service_name}_custom_expressions.json"
    if file_path.exists():
        with open(file_path, 'r') as f:
            return json.load(f)
    return []

def clear_custom_configs(service_name: str = "format_service"):
    """Clear all custom configurations"""
    expr_file = CUSTOM_FORMAT_DIR / f"{service_name}_custom_expressions.json"
    
    if expr_file.exists():
        expr_file.unlink()