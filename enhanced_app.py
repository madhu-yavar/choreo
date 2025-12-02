from __future__ import annotations
import os, json
from pathlib import Path
from typing import List, Dict, Any, Optional

# Load .env FIRST before any other imports that depend on environment variables
from dotenv import load_dotenv
load_dotenv(dotenv_path=Path(__file__).parent / ".env", override=True)

from fastapi import FastAPI, Header, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from enhanced_toxicity_model import EnhancedToxicityModel
from enhanced_profanity import EnhancedProfanityDetector
from utils import sentences_with_offsets, join_preserving_spacing, redact_ranges

app = FastAPI(title="Enhanced Toxicity & Profanity Service", version="2.0.0")

# ------------- CORS -------------
SANDBOX_ORIGIN = (os.getenv("SANDBOX_ORIGIN", "") or "").strip()
ALLOWED = os.getenv("CORS_ALLOWED_ORIGINS", "")
def _sanitize(o: str) -> str:
    return (o or "").strip().rstrip("/")

allow_origins = [_sanitize(o) for o in (ALLOWED.split(",") if ALLOWED else []) if o.strip()]
allow_origins.extend([
    "https://preview--zgrid-feature-flow.lovable.app",
    "https://zgrid-feature-flow.lovable.app",
    "http://localhost:5173",
    "http://localhost:3000",
])
if SANDBOX_ORIGIN:
    allow_origins.append(_sanitize(SANDBOX_ORIGIN))

seen = set()
allow_origins = [o for o in allow_origins if o and not (o in seen or seen.add(o))]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins or ["*"],
    allow_methods=["POST","GET","OPTIONS"],
    allow_headers=["*"],
)

@app.middleware("http")
async def allow_private_network(request, call_next):
    resp = await call_next(request)
    if request.method == "OPTIONS":
        resp.headers["Access-Control-Allow-Private-Network"] = "true"
    return resp

# ------------- API Keys -------------
_API_KEYS = set(k.strip() for k in (os.getenv("TOX_API_KEYS","")).split(",") if k.strip())
def require_api_key(
    x_api_key: Optional[str] = Header(default=None),
    authorization: Optional[str] = Header(default=None),
):
    if not _API_KEYS:
        return
    token = x_api_key
    if not token and authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()
    if not token or token not in _API_KEYS:
        raise HTTPException(status_code=401, detail="Unauthorized")

# ------------- Defaults -------------
DEFAULT_MODEL = os.getenv("DETOXIFY_MODEL", "original").strip().lower()
DEFAULT_MODE = os.getenv("TOX_MODE", "sentence").strip().lower()
DEFAULT_ACTION = os.getenv("ACTION_ON_FAIL","remove_sentences").strip().lower()

# Category-specific thresholds - addressing QA team's requirements
CATEGORY_THRESHOLDS = {
    "toxicity": float(os.getenv("THRESHOLD_TOXICITY", "0.7")),        # Increased to reduce noise
    "severe_toxicity": float(os.getenv("THRESHOLD_SEVERE_TOXICITY", "0.2")),  # Lowered for better detection
    "obscene": float(os.getenv("THRESHOLD_OBSCENE", "0.3")),
    "threat": float(os.getenv("THRESHOLD_THREAT", "0.2")),            # Lowered for high-severity content
    "insult": float(os.getenv("THRESHOLD_INSULT", "0.4")),
    "identity_attack": float(os.getenv("THRESHOLD_IDENTITY_ATTACK", "0.3")),
    "sexual_explicit": float(os.getenv("THRESHOLD_SEXUAL_EXPLICIT", "0.3")),  # Lowered for better detection
}

# Fallback threshold for backwards compatibility
DEFAULT_THRESHOLD = float(os.getenv("DETOXIFY_THRESHOLD","0.3"))

# Minimum score threshold to filter out negligible scores
MIN_CONFIDENCE_SCORE = float(os.getenv("MIN_CONFIDENCE_SCORE", "0.05"))

DEFAULT_LABELS = [s.strip() for s in os.getenv("DETOXIFY_LABELS","").split(",") if s.strip()]

PROF_ENABLED = os.getenv("PROFANITY_ENABLED","1") in ("1","true","True")
PROF_ACTION = os.getenv("PROFANITY_ACTION","mask").strip().lower()

# ------------- Schemas -------------
class ValidateRequest(BaseModel):
    text: str
    mode: Optional[str] = None                     # sentence | text
    tox_threshold: Optional[float] = None
    labels: Optional[List[str]] = None             # subset
    action_on_fail: Optional[str] = None           # remove_sentences | remove_all | redact
    profanity_enabled: Optional[bool] = None
    profanity_action: Optional[str] = None         # mask | remove
    return_spans: Optional[bool] = True
    enhanced_detection: Optional[bool] = True      # Use enhanced detection
    context_aware: Optional[bool] = True           # Consider context exceptions

class Flagged(BaseModel):
    type: str
    score: float
    span: Optional[List[int]] = None
    sentence: Optional[str] = None
    token: Optional[str] = None
    severity: Optional[str] = None                 # For profanity
    pattern: Optional[str] = None                 # For pattern matches

class ValidateResponse(BaseModel):
    status: str                                    # pass | fixed
    clean_text: str
    flagged: List[Flagged]
    scores: Dict[str,float]                        # aggregate (max per label)
    steps: List[Dict[str, Any]]
    reasons: List[str]
    context: Optional[str] = None                  # Detected context
    stats: Optional[Dict[str, int]] = None         # Profanity severity stats

# ------------- Enhanced Models -------------
tox_model = EnhancedToxicityModel()
profanity_detector = EnhancedProfanityDetector()

def check_category_thresholds(scores: Dict[str, float], labels: List[str],
                             use_category_specific: bool = True) -> Dict[str, Any]:
    """
    Check thresholds with category-specific logic.
    This fixes the QA team's concern about general toxicity masking specific categories.
    """
    breached_categories = []
    threshold_details = {}

    for category in labels:
        score = scores.get(category, 0.0)

        # Filter out negligible scores
        if score < MIN_CONFIDENCE_SCORE:
            threshold_details[category] = {
                "score": score,
                "threshold": CATEGORY_THRESHOLDS.get(category, DEFAULT_THRESHOLD),
                "breached": False,
                "reason": "Below minimum confidence threshold"
            }
            continue

        if use_category_specific:
            category_threshold = CATEGORY_THRESHOLDS.get(category, DEFAULT_THRESHOLD)
        else:
            category_threshold = DEFAULT_THRESHOLD

        is_breached = score >= category_threshold
        threshold_details[category] = {
            "score": score,
            "threshold": category_threshold,
            "breached": is_breached,
            "category_specific": use_category_specific
        }

        if is_breached:
            breached_categories.append(category)

    # Important change: Don't let general toxicity mask specific categories
    # Each category is evaluated independently
    has_toxicity = "toxicity" in breached_categories
    has_specific = any(cat in breached_categories for cat in ["severe_toxicity", "threat", "sexual_explicit", "identity_attack"])

    # Consider it a breach if ANY category is breached, not just general toxicity
    overall_breach = len(breached_categories) > 0

    return {
        "breached": overall_breach,
        "breached_categories": breached_categories,
        "has_toxicity": has_toxicity,
        "has_specific_threats": has_specific,
        "threshold_details": threshold_details,
        "max_score": max(scores.values()) if scores else 0.0
    }

@app.get("/health")
def health():
    return {"ok": True, "version": "2.0.0", "enhanced": True}

@app.post("/validate", response_model=ValidateResponse, dependencies=[Depends(require_api_key)])
def validate(req: ValidateRequest):
    text = req.text or ""
    if not text.strip():
        return {
            "status": "pass",
            "clean_text": text,
            "flagged": [],
            "scores": {},
            "steps": [{"name":"noop","passed":True}],
            "reasons": ["Empty text"],
        }

    mode = (req.mode or DEFAULT_MODE).lower()
    threshold = float(req.tox_threshold if req.tox_threshold is not None else DEFAULT_THRESHOLD)
    labels = [l.strip().lower() for l in (req.labels or DEFAULT_LABELS or
              ["toxicity","severe_toxicity","obscene","threat","insult","identity_attack","sexual_explicit"])]
    action = (req.action_on_fail or DEFAULT_ACTION).lower()
    profanity_enabled = PROF_ENABLED if req.profanity_enabled is None else bool(req.profanity_enabled)
    profanity_action = (req.profanity_action or PROF_ACTION).lower()
    enhanced_detection = req.enhanced_detection if req.enhanced_detection is not None else True
    context_aware = req.context_aware if req.context_aware is not None else True

    flagged: List[Dict[str,Any]] = []
    aggregate_scores: Dict[str,float] = {lab:0.0 for lab in labels}
    steps = []

    # Detect context if context-aware
    detected_context = None
    if context_aware and enhanced_detection:
        detected_context = tox_model._check_context_exceptions(text)
        steps.append({"name": "context_detection", "passed": True, "details": {"context": detected_context}})

    keep_ranges: List[tuple] = []
    bad_ranges: List[tuple] = []

    # Enhanced toxicity detection with category-specific thresholds
    if mode == "text":
        scores_list = tox_model.score([text])
        scores = {k.lower(): float(v) for k,v in scores_list[0].items() if k.lower() in set(labels)}
        for k,v in scores.items():
            aggregate_scores[k] = max(aggregate_scores.get(k,0.0), v)

        # Use category-specific threshold checking
        threshold_result = check_category_thresholds(scores, labels, use_category_specific=enhanced_detection)

        if threshold_result["breached"]:
            bad_ranges.append((0, len(text)))
            # Create detailed flagged entries for each breached category
            for breached_category in threshold_result["breached_categories"]:
                flagged.append({
                    "type": breached_category,
                    "score": scores[breached_category],
                    "span": [0, len(text)],
                    "sentence": text,
                    "threshold_used": threshold_result["threshold_details"][breached_category]["threshold"]
                })
        else:
            keep_ranges.append((0, len(text)))

        # Add threshold details to steps for debugging
        steps.append({
            "name": "category_threshold_check",
            "passed": True,
            "details": {
                "threshold_analysis": threshold_result,
                "category_specific_enabled": enhanced_detection
            }
        })

    else:  # sentence mode
        sents = sentences_with_offsets(text)
        if not sents:
            sents = [(0, len(text), text)]
        sent_texts = [s[2] for s in sents]
        scores_list = tox_model.score(sent_texts)

        for idx, (start, end, stext) in enumerate(sents):
            scores = {k.lower(): float(v) for k,v in scores_list[idx].items() if k.lower() in set(labels)}
            for k,v in scores.items():
                if v > aggregate_scores.get(k,0.0):
                    aggregate_scores[k] = v

            # Use category-specific threshold checking for each sentence
            threshold_result = check_category_thresholds(scores, labels, use_category_specific=enhanced_detection)

            if threshold_result["breached"]:
                bad_ranges.append((start, end))
                # Create detailed flagged entries for each breached category in this sentence
                for breached_category in threshold_result["breached_categories"]:
                    flagged.append({
                        "type": breached_category,
                        "score": scores[breached_category],
                        "span": [start, end],
                        "sentence": stext,
                        "threshold_used": threshold_result["threshold_details"][breached_category]["threshold"]
                    })
            else:
                keep_ranges.append((start, end))

    steps.append({"name": "enhanced_toxicity_detection", "passed": True, "details": {
        "mode": mode,
        "threshold": threshold,
        "category_thresholds": CATEGORY_THRESHOLDS if enhanced_detection else {"all": threshold},
        "labels": labels,
        "toxic_spans": len(bad_ranges),
        "enhanced": enhanced_detection,
        "context_aware": context_aware,
        "min_confidence_score": MIN_CONFIDENCE_SCORE
    }})

    # Apply action for toxicity
    changed = False
    if bad_ranges:
        changed = True
        if action == "remove_all":
            out_text = ""
        elif action == "redact":
            out_text = redact_ranges(text, bad_ranges, token="[TOXIC]")
        else:  # remove_sentences (default)
            out_text = join_preserving_spacing(text, keep_ranges)
    else:
        out_text = text

    # Enhanced profanity detection
    prof_spans = []
    prof_stats = None
    if profanity_enabled and out_text and enhanced_detection:
        if enhanced_detection:
            # Use enhanced profanity detector
            out2, spans = profanity_detector.detect_and_apply(out_text, action=profanity_action)
            prof_stats = profanity_detector.get_severity_stats(out_text)
        else:
            # Fallback to basic detection (would need import of original profanity module)
            out2, spans = out_text, []

        if spans:
            changed = True
            prof_spans = [{
                "type": "profanity",
                "token": s["token"],
                "score": 0.9 if s.get("severity") == "high" else 0.6,
                "span": [s["start"], s["end"]],
                "severity": s.get("severity", "medium")
            } for s in spans]
        out_text = out2

        steps.append({"name": "enhanced_profanity_detection", "passed": True, "details": {
            "hits": len(spans),
            "action": profanity_action,
            "enhanced": enhanced_detection,
            "stats": prof_stats
        }})
    else:
        steps.append({"name": "enhanced_profanity_detection", "passed": True, "details": {
            "hits": 0,
            "action": profanity_action,
            "enhanced": enhanced_detection,
            "stats": None
        }})

    # Generate reasons
    reasons = []
    if bad_ranges:
        if action == "remove_all":
            reasons.append("Toxic content removed (entire text).")
        elif action == "redact":
            reasons.append("Toxic sentences redacted.")
        else:
            reasons.append("Toxic sentences removed.")
    if prof_spans:
        if profanity_action == "remove":
            reasons.append(f"{len(prof_spans)} profanities removed.")
        else:
            reasons.append(f"{len(prof_spans)} profanities masked.")

    status = "fixed" if changed else "pass"
    return {
        "status": status,
        "clean_text": out_text,
        "flagged": flagged + prof_spans,
        "scores": aggregate_scores,
        "steps": steps,
        "reasons": reasons or (["No toxicity or profanity detected"] if not changed else []),
        "context": detected_context,
        "stats": prof_stats
    }

@app.post("/analyze")
def analyze_text(text: str, enhanced: bool = True):
    """
    Analyze text for toxicity patterns without filtering
    Returns detailed analysis including detected patterns and context
    """
    scores = tox_model.score([text])[0]
    profanity_spans = profanity_detector.detect_profanity(text) if enhanced else []
    context = tox_model._check_context_exceptions(text) if enhanced else None

    return {
        "scores": scores,
        "profanity": profanity_spans,
        "context": context,
        "enhanced_features": {
            "pattern_detection": enhanced,
            "context_aware": enhanced,
            "multilingual_support": enhanced
        }
    }

@app.get("/stats")
def get_service_stats():
    """Get service statistics and capabilities"""
    return {
        "version": "2.0.0",
        "enhanced": True,
        "features": {
            "ml_toxicity_detection": tox_model.detoxify_model is not None,
            "pattern_based_detection": True,
            "disguised_toxicity_detection": True,
            "context_aware_detection": True,
            "multilingual_profanity": True,
            "severity_classification": True,
            "subtle_toxicity_detection": True
        },
        "supported_languages": ["en", "es", "fr", "de", "pl", "it"],  # Basic multilingual support
        "detection_types": [
            "toxicity", "severe_toxicity", "obscene", "threat", "insult",
            "identity_attack", "sexual_explicit", "pattern_toxicity",
            "sarcastic_insult", "passive_aggressive"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)