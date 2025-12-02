#!/usr/bin/env python3
"""
Enhanced Simple Gateway Service - External-Facing Content Moderation Gateway
Supports both legacy and Enhanced RoBERTa service response formats
"""

import os
import json
import asyncio
import httpx
from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import FastAPI, Header, HTTPException, Body
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Simple Gateway Service",
    description="External-facing gateway with enhanced RoBERTa jailbreak detection support",
    version="1.1.0"
)

@app.on_event("startup")
async def startup_client():
    limits = httpx.Limits(max_keepalive_connections=20, max_connections=100)
    timeout = httpx.Timeout(60.0, connect=30.0, read=60.0, write=30.0, pool=30.0)
    client = httpx.AsyncClient(timeout=timeout, limits=limits, follow_redirects=True, verify=False)
    app.state.http = client
    print("✅ Enhanced Simple Gateway HTTP client initialized")

@app.on_event("shutdown")
async def shutdown_client():
    client = getattr(app.state, "http", None)
    if client:
        await client.aclose()
        print("✅ Enhanced Simple Gateway HTTP client closed")

MASTER_API_KEYS = [s.strip() for s in os.getenv("SIMPLE_GATEWAY_MASTER_KEYS", "simple-gateway-master-key").split(",") if s.strip()]
SERVICE_ENDPOINTS = {
    "pii": os.getenv("PII_SERVICE_URL", "http://pii-enhanced-v3-service.z-grid:8000/validate"),
    "toxicity": os.getenv("TOXICITY_SERVICE_URL", "http://tox-service-ml-enabled.z-grid:8001/validate"),
    "jailbreak": os.getenv("JAILBREAK_SERVICE_URL", "http://jailbreak-roberta-heuristic-service.z-grid:5004/detect"),
    "ban": os.getenv("BAN_SERVICE_URL", "http://ban-service-yavar-fixed.z-grid:8004/validate"),
    "secrets": os.getenv("SECRETS_SERVICE_URL", "http://secrets-service-yavar-fixed.z-grid:8005/validate"),
    "format": os.getenv("FORMAT_SERVICE_URL", "http://format-service-yavar-fixed.z-grid:8006/validate"),
    "gibberish": os.getenv("GIBBERISH_SERVICE_URL", "http://gibberish-service.z-grid:8007/validate"),
}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

class ValidateRequest(BaseModel):
    text: str
    check_pii: bool = True
    check_toxicity: bool = True
    check_jailbreak: bool = True
    check_secrets: bool = True
    check_ban: bool = True
    check_format: bool = True
    check_gibberish: bool = True
    action_on_fail: str = "refrain"
    timeout: float = 30.0

class ModerationResult(BaseModel):
    status: str
    clean_text: str
    blocked_categories: List[str]
    results: Dict[str, Any]
    reasons: List[str]
    processing_time_ms: Optional[float] = None
    services_checked: Optional[int] = None
    gateway_version: str = "1.1.0"
    timestamp: Optional[str] = None

def require_master_api_key(x_api_key: Optional[str] = Header(default=None)):
    if not MASTER_API_KEYS:
        return
    if not x_api_key or x_api_key not in MASTER_API_KEYS:
        raise HTTPException(status_code=401, detail="Unauthorized - Invalid Master API key")

def normalize_jailbreak_response(response_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize jailbreak service response to consistent format.
    Handles both legacy format and Enhanced RoBERTa format.
    """
    # Enhanced RoBERTa format: {"prediction": "jailbreak", "confidence": 1.0, ...}
    if "prediction" in response_data:
        prediction = response_data.get("prediction", "benign")
        confidence = response_data.get("confidence", 0.0)

        # Convert prediction to status
        if prediction == "jailbreak":
            status = "blocked"
        elif prediction == "benign":
            status = "pass"
        else:
            status = "error"

        # Create normalized response
        normalized = {
            "status": status,
            "confidence": confidence,
            "prediction": prediction,
            "roberta_score": response_data.get("roberta_score", 0.0),
            "heuristic_adjustment": response_data.get("heuristic_adjustment", 0.0),
            "adjusted_score": response_data.get("adjusted_score", confidence),
            "reasoning": response_data.get("reasoning", "no_specific_patterns"),
            "model_type": response_data.get("model_type", "unknown"),
            "text": response_data.get("text", ""),
            "timestamp": response_data.get("timestamp", datetime.utcnow().isoformat()),
            "probabilities": response_data.get("probabilities", {}),
            "threshold_used": response_data.get("threshold_used", 0.5),
            "request_id": response_data.get("request_id", ""),
            "processing_time_ms": response_data.get("processing_time_ms", 0.0)
        }

        # Add any additional fields from original response
        for key, value in response_data.items():
            if key not in normalized:
                normalized[key] = value

        return normalized

    # Legacy format: {"status": "blocked", "confidence": 1.0, ...}
    elif "status" in response_data:
        return response_data

    # Unknown format - create error response
    return {
        "status": "error",
        "confidence": 0.0,
        "error": "Unknown response format",
        "processing_time_ms": 0.0
    }

async def call_service(service_name: str, text: str, timeout: float = 30.0, **kwargs) -> Dict[str, Any]:
    """Call service with enhanced response handling for jailbreak service"""
    if service_name not in SERVICE_ENDPOINTS:
        return {"status": "error", "error": f"Unknown service: {service_name}", "processing_time_ms": 0}

    url = SERVICE_ENDPOINTS[service_name]
    headers = {"Content-Type": "application/json", "X-API-Key": "supersecret123"}
    payload = {"text": text}
    payload.update(kwargs)
    client = app.state.http

    try:
        start_time = datetime.now()
        response = await client.post(url, headers=headers, json=payload, timeout=timeout)
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds() * 1000

        if response.status_code == 200:
            result = response.json()
            result["processing_time_ms"] = processing_time

            # Special handling for jailbreak service to normalize response format
            if service_name == "jailbreak":
                result = normalize_jailbreak_response(result)

            return result
        else:
            return {
                "status": "error",
                "error": f"Service {service_name} returned {response.status_code}",
                "processing_time_ms": processing_time
            }
    except Exception as e:
        return {
            "status": "error",
            "error": f"Failed to call {service_name}",
            "details": str(e),
            "processing_time_ms": 0.0
        }

@app.get("/")
async def root():
    return {
        "service": "Enhanced Simple Gateway Service",
        "version": "1.1.0",
        "status": "running",
        "enhanced_roberta_support": True
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "Enhanced Simple Gateway Service",
        "version": "1.1.0",
        "enhanced_roberta_support": True,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/services")
async def get_services():
    return {
        "gateway_version": "1.1.0",
        "total_services": len(SERVICE_ENDPOINTS),
        "services": list(SERVICE_ENDPOINTS.keys()),
        "excluded_services": ["bias", "policy"],
        "enhanced_roberta_jailbreak": True
    }

@app.post("/validate", response_model=ModerationResult)
async def validate_content(request: ValidateRequest, x_api_key: Optional[str] = Header(default=None)):
    """Enhanced content validation with Enhanced RoBERTa jailbreak detection"""
    require_master_api_key(x_api_key)
    start_time = datetime.now()
    text = request.text or ""

    if not text.strip():
        return ModerationResult(
            status="pass",
            clean_text=text,
            blocked_categories=[],
            results={},
            reasons=["Empty text"],
            processing_time_ms=0,
            services_checked=0,
            timestamp=datetime.utcnow().isoformat()
        )

    results = {}
    blocked_categories = []
    reasons = []
    clean_text = text
    services_checked = 0

    task_configs = {}
    if request.check_pii: task_configs["pii"] = {}
    if request.check_toxicity: task_configs["toxicity"] = {}
    if request.check_jailbreak: task_configs["jailbreak"] = {}
    if request.check_ban: task_configs["ban"] = {}
    if request.check_secrets: task_configs["secrets"] = {}
    if request.check_format: task_configs["format"] = {}
    if request.check_gibberish: task_configs["gibberish"] = {}

    if task_configs:
        tasks = {
            service_name: asyncio.create_task(call_service(service_name, text, request.timeout or 30.0, **params))
            for service_name, params in task_configs.items()
        }
        task_results = await asyncio.gather(*tasks.values(), return_exceptions=True)
        service_names = list(tasks.keys())

        for i, service_name in enumerate(service_names):
            try:
                if isinstance(task_results[i], Exception):
                    results[service_name] = {
                        "status": "error",
                        "error": "Service call failed",
                        "details": str(task_results[i])
                    }
                else:
                    results[service_name] = task_results[i]

                services_checked += 1

                # Check if service detected issues
                service_result = results[service_name]
                if service_result.get("status") in ("blocked", "refrain", "fixed"):
                    blocked_categories.append(service_name)
                    reason_map = {
                        "pii": "PII detected",
                        "toxicity": "Toxic content detected",
                        "jailbreak": "Jailbreak attempt detected",
                        "ban": "Content banned",
                        "secrets": "Secrets detected",
                        "format": "Format issues detected",
                        "gibberish": "Gibberish detected"
                    }
                    reasons.append(reason_map.get(service_name, f"{service_name} detected"))

                    action = request.action_on_fail or "refrain"
                    if action == "refrain":
                        clean_text = ""
                    elif action == "filter":
                        clean_text = f"[{service_name.upper()} DETECTED]"
                    elif action == "mask":
                        clean_text = "*" * len(text)

            except Exception as e:
                results[service_name] = {
                    "status": "error",
                    "error": "Failed to process service result",
                    "details": str(e)
                }

    end_time = datetime.now()
    processing_time = (end_time - start_time).total_seconds() * 1000

    # Determine overall status
    if not blocked_categories:
        overall_status = "pass"
    elif clean_text == "":
        overall_status = "blocked"
    elif clean_text != text:
        overall_status = "fixed"
    else:
        overall_status = "blocked"

    if not reasons:
        reasons = ["Content complies with all policies"]

    return ModerationResult(
        status=overall_status,
        clean_text=clean_text,
        blocked_categories=blocked_categories,
        results=results,
        reasons=reasons,
        processing_time_ms=processing_time,
        services_checked=services_checked,
        timestamp=datetime.utcnow().isoformat()
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8010)