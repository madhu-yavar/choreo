import os, json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

# Import the enhanced detector
from enhanced_detectors import SecretsDetector
from utils import mask_or_filter

# Load .env for local run
load_dotenv(dotenv_path=Path(__file__).parent / ".env", override=True)

app = FastAPI(title="Enhanced Secrets Detection Service", version="1.1.0")

allowed = [o.strip() for o in (os.getenv("CORS_ALLOWED_ORIGINS","")).split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed or ["*"],
    allow_methods=["GET","POST","OPTIONS"],
    allow_headers=["*"],
)

API_KEYS = [s.strip() for s in os.getenv("SECRETS_API_KEYS","").split(",") if s.strip()]
PATTERNS_DIR = os.getenv("PATTERNS_DIR", "patterns")

# Enhanced configuration options
ENABLE_REGEX = os.getenv("ENABLE_REGEX","1") not in ("0","false","False")
ENABLE_ENTROPY = os.getenv("ENABLE_ENTROPY","1") not in ("0","false","False")
ENABLE_CONTEXT = os.getenv("ENABLE_CONTEXT","1") not in ("0","false","False")
ENABLE_ENHANCED = os.getenv("ENABLE_ENHANCED","1") not in ("0","false","False")  # New option

ENTROPY_THRESHOLD = float(os.getenv("ENTROPY_THRESHOLD","3.5"))  # Lowered default
MIN_TOKEN_LEN = int(os.getenv("MIN_TOKEN_LEN","15"))  # Reduced default
CONTEXT_WINDOW_CHARS = int(os.getenv("CONTEXT_WINDOW_CHARS","50"))  # Increased default

ACTION_DEFAULT = (os.getenv("SECRETS_ACTION_ON_FAIL","refrain") or "refrain").lower()
MASK_TOKEN = os.getenv("MASK_TOKEN","***")
RETURN_SECRET_VALUES = os.getenv("RETURN_SECRET_VALUES","0") not in ("0","false","False")

_detector: Optional[SecretsDetector] = None

def get_detector() -> SecretsDetector:
    global _detector
    if _detector is None:
        _detector = SecretsDetector(
            patterns_dir=PATTERNS_DIR,
            enable_regex=ENABLE_REGEX,
            enable_entropy=ENABLE_ENTROPY,
            enable_context=ENABLE_CONTEXT,
            enable_enhanced=ENABLE_ENHANCED,  # New parameter
            entropy_threshold=ENTROPY_THRESHOLD,
            min_token_len=MIN_TOKEN_LEN,
            context_window_chars=CONTEXT_WINDOW_CHARS,
        )
    return _detector

class ValidateRequest(BaseModel):
    text: str
    categories: Optional[List[str]] = None
    action_on_fail: Optional[str] = None   # refrain|filter|mask|reask
    return_spans: Optional[bool] = True

class FlagOut(BaseModel):
    type: str                 # "secret"
    id: str                   # signature id
    category: str
    start: Optional[int] = None
    end: Optional[int] = None
    score: float
    engine: str               # regex|entropy|enhanced
    severity: int
    value: Optional[str] = None
    snippet: Optional[str] = None

class ValidateResponse(BaseModel):
    status: str               # pass|blocked|fixed
    clean_text: str
    flagged: List[FlagOut]
    steps: List[Dict[str, Any]]
    reasons: List[str]

def require_api_key(x_api_key: Optional[str]):
    if API_KEYS and (not x_api_key or x_api_key not in API_KEYS):
        raise HTTPException(status_code=401, detail="Unauthorized")

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/validate", response_model=ValidateResponse)
def validate(req: ValidateRequest, x_api_key: Optional[str] = Header(default=None)):
    require_api_key(x_api_key)

    text = (req.text or "")
    if not text.strip():
        return {"status":"pass","clean_text":"","flagged":[],"steps":[{"name":"noop","passed":True}],"reasons":["Empty text"]}

    det = get_detector()
    hits = det.detect(text, categories=req.categories)

    steps = [{
        "name":"enhanced_detection",
        "passed": len(hits) == 0,
        "details":{
            "hits": len(hits),
            "enable_regex": ENABLE_REGEX,
            "enable_entropy": ENABLE_ENTROPY,
            "enable_enhanced": ENABLE_ENHANCED,  # New detail
            "entropy_threshold": ENTROPY_THRESHOLD,
            "min_token_len": MIN_TOKEN_LEN,
            "context_window": CONTEXT_WINDOW_CHARS
        }
    }]

    if not hits:
        return {
            "status":"pass",
            "clean_text": text,
            "flagged": [],
            "steps": steps,
            "reasons": ["No secrets detected"]
        }

    # map to output
    flags: List[FlagOut] = []
    spans = []
    for h in hits:
        val_out = h.get("value") if RETURN_SECRET_VALUES else None
        flags.append(FlagOut(
            type="secret",
            id=h["id"],
            category=h["category"],
            start=h.get("start"),
            end=h.get("end"),
            score=float(h.get("score", 1.0)),
            engine=h["engine"],
            severity=int(h.get("severity", 3)),
            value=val_out,
            snippet=h.get("snippet"),
        ))
        if h.get("start") is not None and h.get("end") is not None:
            spans.append({"start":h["start"], "end":h["end"]})

    action = (req.action_on_fail or ACTION_DEFAULT).lower()
    if action == "filter":
        clean = mask_or_filter(text, spans, mode="filter")
        status, reason = "fixed", "Secrets removed"
    elif action == "mask":
        clean = mask_or_filter(text, spans, token=MASK_TOKEN, mode="mask")
        status, reason = "fixed", "Secrets masked"
    elif action == "reask":
        clean = "I can't process content containing credentials. Please remove or rotate secrets and rephrase."
        status, reason = "fixed", "Re-asked for safe content"
    else:
        clean = ""
        status, reason = "blocked", "Secrets blocked"

    return {
        "status": status,
        "clean_text": clean,
        "flagged": [] if (req.return_spans is False) else flags,
        "steps": steps,
        "reasons": [reason],
    }