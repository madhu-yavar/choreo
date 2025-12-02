#!/usr/bin/env python3
"""
Semi-full PII service with GLiNER ML models (without waiting for Presidio spaCy to finish building)
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

# Try to import GLiNER (ML-based NER)
try:
    import pii_gliner
    GLINER_AVAILABLE = True
    print("✓ GLiNER (ML-based NER) available")
except Exception as e:
    print(f"✗ GLiNER not available: {e}")
    GLINER_AVAILABLE = False

# FastAPI app
app = FastAPI(title="PII Semi-Full Service", version="1.1.0")

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
    gliner_labels: Optional[List[str]] = None
    gliner_threshold: Optional[float] = None
    thresholds: Optional[Dict[str, float]] = None
    return_spans: Optional[bool] = True
    language: Optional[str] = None

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

# PII detection functions
def detect_pii_regex(text: str, entities: List[str]) -> List[Dict]:
    """Simple regex-based PII detection"""
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

def detect_pii_gliner(text: str, gliner_labels: List[str], threshold: float = 0.5) -> List[Dict]:
    """ML-based PII detection using GLiNER"""
    if not GLINER_AVAILABLE or not gliner_labels:
        return []

    try:
        # Initialize GLiNER
        gliner_detector = pii_gliner.GlinerDetector()
        predictions = gliner_detector.detect(text, labels=gliner_labels, threshold=threshold)

        detected = []
        for pred in predictions:
            raw = text[pred["start"]:pred["end"]]

            # Skip generic spans using utils
            if hasattr(utils, 'is_generic_preface_span') and utils.is_generic_preface_span(raw):
                continue

            # Map GLiNER labels to PII types
            label_upper = pred.get("label", "").upper()
            if "PERSON" in label_upper:
                pii_type = "PERSON"
            elif "LOC" in label_upper:
                pii_type = "LOCATION"
            elif "ORG" in label_upper:
                pii_type = "ORGANIZATION"
            else:
                pii_type = label_upper or "PERSON"

            # Enhanced validation using utils
            if hasattr(utils, 'is_valid_entity') and not utils.is_valid_entity(raw, pii_type):
                continue

            detected.append({
                "type": pii_type,
                "value": raw,
                "start": int(pred["start"]),
                "end": int(pred["end"]),
                "score": float(pred.get("score", 0.0)),
                "replacement": f"[{pii_type}]"
            })

        return detected
    except Exception as e:
        print(f"GLiNER detection error: {e}")
        return []

def merge_spans(text: str, regex_spans: List[Dict], gliner_spans: List[Dict]) -> List[Dict]:
    """Merge spans from regex and GLiNER detection"""
    all_spans = regex_spans + gliner_spans

    if not all_spans:
        return []

    # Sort by start position
    all_spans.sort(key=lambda x: x["start"])

    # Merge overlapping spans
    merged = []
    for span in all_spans:
        if not merged:
            merged.append(span)
        else:
            last = merged[-1]
            if span["start"] <= last["end"]:
                # Overlap - keep the one with higher score
                if span["score"] > last["score"]:
                    merged[-1] = span
            else:
                merged.append(span)

    return merged

def apply_redactions(text: str, spans: List[Dict]) -> str:
    """Apply redactions to text"""
    if not spans:
        return text

    redacted = text
    for span in sorted(spans, key=lambda x: x["start"], reverse=True):
        redacted = redacted[:span["start"]] + span["replacement"] + redacted[span["end"]:]

    return redacted

# Endpoints
@app.get("/health")
def health():
    return {
        "ok": True,
        "message": "PII Service with ML-powered GLiNER",
        "gliner_available": GLINER_AVAILABLE,
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

    # Default entities to check
    base_entities = req.entities or ["EMAIL_ADDRESS", "PHONE_NUMBER", "US_SSN", "PERSON", "LOCATION", "ORGANIZATION"]

    # Add custom entities
    try:
        custom_entities = custom_config.load_custom_entities()
        custom_entity_types = [entity["type"] for entity in custom_entities if entity.get("type")]
        entities = list(set(base_entities + custom_entity_types))
    except Exception as e:
        print(f"Error loading custom entities: {e}")
        entities = base_entities

    # ---------- Regex Detection ----------
    regex_spans = detect_pii_regex(text, [e for e in entities if e in ["EMAIL_ADDRESS", "PHONE_NUMBER", "US_SSN", "CREDIT_CARD"]])

    # ---------- GLiNER ML Detection ----------
    gliner_labels = req.gliner_labels or ["person", "location", "organization"]
    gliner_threshold = req.gliner_threshold or 0.5
    gliner_spans = detect_pii_gliner(text, gliner_labels, gliner_threshold)

    # ---------- Merge and Redact ----------
    merged_spans = merge_spans(text, regex_spans, gliner_spans)

    steps = [
        {"name": "regex_detection", "passed": True, "details": {"count": len(regex_spans)}},
        {"name": "gliner_ml_detection", "passed": True, "details": {"count": len(gliner_spans), "labels": gliner_labels}},
        {"name": "utils_validation", "passed": True, "details": {"utils_available": hasattr(utils, 'is_valid_entity') and hasattr(utils, 'is_generic_preface_span')}},
    ]

    if not merged_spans:
        return {
            "status": "pass",
            "redacted_text": text,
            "entities": [],
            "steps": steps,
            "reasons": ["No PII detected"],
        }

    redacted_text = apply_redactions(text, merged_spans)
    return {
        "status": "refrain",
        "redacted_text": redacted_text,
        "entities": merged_spans if req.return_spans else [],
        "steps": steps,
        "reasons": ["PII detected and redacted using ML and patterns"],
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)