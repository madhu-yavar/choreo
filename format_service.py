#!/usr/bin/env python3
"""
Format Validation Service
Validates response formatting and structure
"""

import os
import json
import logging
import time
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
import re
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, ValidationError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configuration
PORT = int(os.environ.get('FORMAT_SERVICE_PORT', 8004))
API_KEY = os.environ.get('API_KEY', 'supersecret123')
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')

# Global variables
start_time = datetime.now()

class FormatValidationRequest(BaseModel):
    text: str
    response_format: Optional[str] = "json"
    schema_validation: Optional[bool] = True
    required_fields: Optional[List[str]] = None

class FormatValidationResponse(BaseModel):
    is_valid_format: bool
    format_type: str
    validation_details: Dict[str, Any]
    errors: List[str]
    processing_time_ms: float
    service_info: Dict[str, str]

def validate_json_format(text: str) -> Dict[str, Any]:
    """Validate JSON format"""
    result = {
        "is_valid": False,
        "errors": [],
        "details": {}
    }

    try:
        parsed = json.loads(text)
        result["is_valid"] = True
        result["details"] = {
            "type": "json",
            "structure": type(parsed).__name__,
            "keys": list(parsed.keys()) if isinstance(parsed, dict) else [],
            "size": len(text),
            "well_formed": True
        }
    except json.JSONDecodeError as e:
        result["errors"].append(f"JSON parsing error: {str(e)}")
        result["details"] = {
            "type": "json",
            "structure": "invalid",
            "size": len(text),
            "well_formed": False
        }
    except Exception as e:
        result["errors"].append(f"Unexpected error: {str(e)}")

    return result

def validate_xml_format(text: str) -> Dict[str, Any]:
    """Validate XML format"""
    result = {
        "is_valid": False,
        "errors": [],
        "details": {}
    }

    # Basic XML validation
    xml_pattern = r'^<[^>]+>.*</[^>]+>$'
    if re.match(xml_pattern, text.strip(), re.DOTALL):
        result["is_valid"] = True
        result["details"] = {
            "type": "xml",
            "structure": "well_formed",
            "size": len(text),
            "has_opening_tags": bool(re.search(r'<[^/][^>]*>', text)),
            "has_closing_tags": bool(re.search(r'</[^>]+>', text))
        }
    else:
        result["errors"].append("XML format appears malformed")
        result["details"] = {
            "type": "xml",
            "structure": "malformed",
            "size": len(text),
            "has_opening_tags": bool(re.search(r'<[^/][^>]*>', text)),
            "has_closing_tags": bool(re.search(r'</[^>]+>', text))
        }

    return result

def validate_csv_format(text: str) -> Dict[str, Any]:
    """Validate CSV format"""
    result = {
        "is_valid": False,
        "errors": [],
        "details": {}
    }

    try:
        lines = text.strip().split('\n')
        if len(lines) < 1:
            result["errors"].append("CSV appears to be empty")
            return result

        # Check for consistent column counts
        first_line_cols = len(lines[0].split(','))
        for i, line in enumerate(lines):
            cols = len(line.split(','))
            if cols != first_line_cols:
                result["errors"].append(f"Inconsistent column count in line {i+1}: expected {first_line_cols}, got {cols}")

        if not result["errors"]:
            result["is_valid"] = True

        result["details"] = {
            "type": "csv",
            "structure": "tabular",
            "rows": len(lines),
            "columns": first_line_cols,
            "size": len(text)
        }

    except Exception as e:
        result["errors"].append(f"CSV validation error: {str(e)}")

    return result

def validate_markdown_format(text: str) -> Dict[str, Any]:
    """Validate Markdown format"""
    result = {
        "is_valid": False,
        "errors": [],
        "details": {}
    }

    # Basic markdown validation
    markdown_patterns = [
        r'#+\s',  # Headers
        r'\*\*.*?\*\*',  # Bold
        r'\*.*?\*',  # Italic
        r'\[.*?\]\(.*?\)',  # Links
        r'```',  # Code blocks
        r'^\s*[-*+]\s',  # Lists
    ]

    has_markdown_features = any(re.search(pattern, text, re.MULTILINE) for pattern in markdown_patterns)

    # Consider it valid if it has markdown features or is plain text
    result["is_valid"] = True
    result["details"] = {
        "type": "markdown",
        "structure": "markup",
        "size": len(text),
        "has_headers": bool(re.search(r'#+\s', text, re.MULTILINE)),
        "has_bold": bool(re.search(r'\*\*.*?\*\*', text)),
        "has_italic": bool(re.search(r'\*.*?\*', text)),
        "has_links": bool(re.search(r'\[.*?\]\(.*?\)', text)),
        "has_code_blocks": bool(re.search(r'```', text)),
        "has_lists": bool(re.search(r'^\s*[-*+]\s', text, re.MULTILINE))
    }

    return result

def validate_text_structure(text: str) -> Dict[str, Any]:
    """General text structure validation"""
    result = {
        "is_valid": True,  # Text is generally always valid
        "errors": [],
        "details": {}
    }

    # Basic text analysis
    words = text.split()
    sentences = text.split('.')
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]

    result["details"] = {
        "type": "text",
        "structure": "plain",
        "size": len(text),
        "word_count": len(words),
        "sentence_count": len([s for s in sentences if s.strip()]),
        "paragraph_count": len(paragraphs),
        "has_formatting": bool(re.search(r'[*_#`\[\]]', text)),
        "avg_word_length": sum(len(word) for word in words) / len(words) if words else 0
    }

    return result

def authenticate_request(request):
    """Authenticate API request"""
    api_key = request.headers.get('X-API-Key')
    return api_key == API_KEY

@app.route('/')
def index():
    """Service information endpoint."""
    return jsonify({
        "service": "Format Validation Service",
        "version": "1.0.0",
        "status": "running",
        "description": "Validates response formatting and structure",
        "supported_formats": ["json", "xml", "csv", "markdown", "text"],
        "endpoints": {
            "health": "GET /health",
            "validate": "POST /validate",
            "batch_validate": "POST /batch_validate"
        }
    })

@app.route('/health')
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "uptime_seconds": (datetime.now() - start_time).total_seconds(),
        "service": "format-validation-service"
    })

@app.route('/validate', methods=['POST'])
def validate_format():
    """Validate format of a single text."""
    start_time = time.time()

    try:
        # Authentication
        if not authenticate_request(request):
            return jsonify({"error": "Unauthorized"}), 401

        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({"error": "Missing 'text' field in request"}), 400

        text = data['text']
        response_format = data.get('response_format', 'json').lower()
        schema_validation = data.get('schema_validation', True)
        required_fields = data.get('required_fields', [])

        if not isinstance(text, str) or not text.strip():
            return jsonify({"error": "Invalid text input"}), 400

        # Validate format
        validation_result = {}

        if response_format == 'json':
            validation_result = validate_json_format(text)
        elif response_format == 'xml':
            validation_result = validate_xml_format(text)
        elif response_format == 'csv':
            validation_result = validate_csv_format(text)
        elif response_format == 'markdown':
            validation_result = validate_markdown_format(text)
        elif response_format == 'text':
            validation_result = validate_text_structure(text)
        else:
            # Auto-detect format
            if text.strip().startswith('{') or text.strip().startswith('['):
                validation_result = validate_json_format(text)
                response_format = 'json'
            elif '<' in text and '>' in text:
                validation_result = validate_xml_format(text)
                response_format = 'xml'
            elif ',' in text and '\n' in text:
                validation_result = validate_csv_format(text)
                response_format = 'csv'
            elif re.search(r'#+\s|[*_`\[\]]', text):
                validation_result = validate_markdown_format(text)
                response_format = 'markdown'
            else:
                validation_result = validate_text_structure(text)
                response_format = 'text'

        # Schema validation (for JSON)
        if schema_validation and response_format == 'json' and validation_result["is_valid"]:
            try:
                parsed = json.loads(text)
                if required_fields:
                    missing_fields = [field for field in required_fields if field not in parsed]
                    if missing_fields:
                        validation_result["errors"].append(f"Missing required fields: {missing_fields}")
                        validation_result["is_valid"] = False
                    else:
                        validation_result["details"]["required_fields_present"] = True
            except:
                pass

        processing_time = (time.time() - start_time) * 1000

        response = {
            "is_valid_format": validation_result["is_valid"],
            "format_type": response_format,
            "validation_details": validation_result["details"],
            "errors": validation_result["errors"],
            "processing_time_ms": round(processing_time, 2),
            "service_info": {
                "service": "format-validation-service",
                "version": "1.0.0",
                "schema_validation_enabled": schema_validation
            },
            "timestamp": datetime.now().isoformat()
        }

        return jsonify(response)

    except Exception as e:
        logger.error(f"Error in validate_format: {e}")
        processing_time = (time.time() - start_time) * 1000
        return jsonify({
            "error": f"Internal server error: {str(e)}",
            "processing_time_ms": round(processing_time, 2)
        }), 500

@app.route('/batch_validate', methods=['POST'])
def batch_validate_format():
    """Validate format of multiple texts."""
    start_time = time.time()

    try:
        # Authentication
        if not authenticate_request(request):
            return jsonify({"error": "Unauthorized"}), 401

        data = request.get_json()
        if not data or 'texts' not in data:
            return jsonify({"error": "Missing 'texts' field in request"}), 400

        texts = data['texts']
        response_format = data.get('response_format', 'auto')
        schema_validation = data.get('schema_validation', True)
        required_fields = data.get('required_fields', [])

        if not isinstance(texts, list):
            return jsonify({"error": "'texts' must be an array"}), 400

        if len(texts) > 50:  # Limit batch size
            return jsonify({"error": "Batch size too large (max 50)"}), 400

        results = []
        for i, text in enumerate(texts):
            if isinstance(text, str) and text.strip():
                # Create individual validation request
                validation_data = {
                    'text': text,
                    'response_format': response_format,
                    'schema_validation': schema_validation,
                    'required_fields': required_fields
                }

                # Validate (simplified version for batch)
                try:
                    if response_format == 'json' or (response_format == 'auto' and text.strip().startswith(('{', '['))):
                        validation_result = validate_json_format(text)
                        fmt_type = 'json'
                    elif response_format == 'xml' or (response_format == 'auto' and '<' in text):
                        validation_result = validate_xml_format(text)
                        fmt_type = 'xml'
                    elif response_format == 'csv' or (response_format == 'auto' and ',' in text and '\n' in text):
                        validation_result = validate_csv_format(text)
                        fmt_type = 'csv'
                    else:
                        validation_result = validate_text_structure(text)
                        fmt_type = 'text'

                    results.append({
                        "index": i,
                        "text": text[:100] + "..." if len(text) > 100 else text,
                        "is_valid_format": validation_result["is_valid"],
                        "format_type": fmt_type,
                        "validation_details": validation_result["details"],
                        "errors": validation_result["errors"]
                    })
                except Exception as e:
                    results.append({
                        "index": i,
                        "text": text[:100] + "..." if len(text) > 100 else text,
                        "error": str(e),
                        "is_valid_format": False
                    })
            else:
                results.append({
                    "index": i,
                    "text": str(text) if text else "",
                    "error": "Invalid text input",
                    "is_valid_format": False
                })

        processing_time = (time.time() - start_time) * 1000

        return jsonify({
            "results": results,
            "batch_size": len(results),
            "processing_time_ms": round(processing_time, 2),
            "service_info": {
                "service": "format-validation-service",
                "version": "1.0.0"
            },
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error in batch_validate_format: {e}")
        processing_time = (time.time() - start_time) * 1000
        return jsonify({
            "error": f"Internal server error: {str(e)}",
            "processing_time_ms": round(processing_time, 2)
        }), 500

if __name__ == '__main__':
    logger.info("🚀 Starting Format Validation Service")
    logger.info(f"🔑 API Key configured: {'Yes' if API_KEY else 'No'}")
    logger.info(f"📊 Log level: {LOG_LEVEL}")

    app.run(host='0.0.0.0', port=PORT, debug=False)