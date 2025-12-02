#!/usr/bin/env python3
"""
Minimal PII service for testing your changes without heavy dependencies
"""

import os
import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, Header, HTTPException, Depends
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment
load_dotenv(dotenv_path=Path(__file__).parent / ".env", override=True)

# Import our custom modules
import utils
import custom_config

# FastAPI app
app = FastAPI(title="PII Test Service", version="1.0.0")

# API Key setup
_API_KEYS = set(k.strip() for k in (os.getenv("PII_API_KEYS", "")).split(",") if k.strip())

def require_api_key(
    x_api_key: Optional[str] = Header(default=None),
    authorization: Optional[str] = Header(default=None),
):
    if not _API_KEYS:
        return  # No auth if no keys configured
    token = x_api_key
    if not token and authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()
    if not token or token not in _API_KEYS:
        raise HTTPException(status_code=401, detail="Unauthorized")

# Schemas
class ValidateRequest(BaseModel):
    text: str
    entities: Optional[List[str]] = None
    return_spans: Optional[bool] = True

class EntityOut(BaseModel):
    type: str
    value: str
    start: int
    end: int
    score: float
    replacement: str

class ValidateResponse(BaseModel):
    status: str
    redacted_text: str
    entities: List[EntityOut]
    steps: List[Dict[str, Any]]
    reasons: List[str]

# Simple regex-based PII detection for testing
def detect_pii_simple(text: str, entities: List[str]) -> List[Dict]:
    """Simple regex-based PII detection for testing purposes"""
    pii_patterns = {
        "EMAIL_ADDRESS": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        "PHONE_NUMBER": r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
        "US_SSN": r'\b\d{3}-\d{2}-\d{4}\b',
        "CREDIT_CARD": r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
    }

    detected = []
    for entity_type in entities:
        if entity_type in pii_patterns:
            pattern = pii_patterns[entity_type]
            for match in re.finditer(pattern, text):
                detected.append({
                    "type": entity_type,
                    "value": match.group(),
                    "start": match.start(),
                    "end": match.end(),
                    "score": 0.9,  # High confidence for regex matches
                    "replacement": f"[{entity_type}]"
                })
    return detected

# Endpoints
@app.get("/health")
def health():
    return {
        "ok": True,
        "message": "Minimal PII service for testing",
        "utils_loaded": True,
        "custom_config_loaded": True,
        "api_keys_configured": len(_API_KEYS) > 0
    }

@app.post("/validate", response_model=ValidateResponse, dependencies=[Depends(require_api_key)])
def validate(req: ValidateRequest):
    text = req.text or ""
    if not text.strip():
        return {
            "status": "pass",
            "redacted_text": text,
            "entities": [],
            "steps": [{"name": "noop", "passed": True}],
            "reasons": ["Empty text"],
        }

    # Load custom entities if available
    base_entities = req.entities or ["EMAIL_ADDRESS", "PHONE_NUMBER", "US_SSN"]

    try:
        custom_entities = custom_config.load_custom_entities()
        custom_entity_types = [entity["type"] for entity in custom_entities if entity.get("type")]
        entities = list(set(base_entities + custom_entity_types))
    except Exception as e:
        print(f"Error loading custom entities: {e}")
        entities = base_entities

    # Simple PII detection
    detected = detect_pii_simple(text, entities)

    # Apply utils validation if available
    validated_entities = []
    for pii in detected:
        if hasattr(utils, 'is_valid_entity'):
            if utils.is_valid_entity(pii["value"], pii["type"]):
                validated_entities.append(pii)
        else:
            validated_entities.append(pii)

    # Redact text
    redacted_text = text
    for pii in sorted(validated_entities, key=lambda x: x["start"], reverse=True):
        redacted_text = redacted_text[:pii["start"]] + pii["replacement"] + redacted_text[pii["end"]:]

    steps = [
        {"name": "regex_detection", "passed": True, "details": {"count": len(validated_entities)}},
        {"name": "utils_validation", "passed": True, "details": {"utils_available": hasattr(utils, 'is_valid_entity')}}
    ]

    if not validated_entities:
        return {
            "status": "pass",
            "redacted_text": text,
            "entities": [],
            "steps": steps,
            "reasons": ["No PII detected"],
        }

    return {
        "status": "refrain",
        "redacted_text": redacted_text,
        "entities": validated_entities if req.return_spans else [],
        "steps": steps,
        "reasons": ["PII detected and redacted"],
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)