import json
import os
import re
from pathlib import Path
from typing import List, Dict, Any, Optional

from utils import shannon_entropy, clamp_span

# Enhanced context words regex to catch more secret-related terms
CONTEXT_WORDS = re.compile(r"(?i)(secret|token|key|apikey|api_key|password|passwd|pwd|authorization|bearer|client_secret|auth|credential|login|pin|passphrase|signature)")

# Enhanced regex to detect potential secrets with spaces or formatting
ENHANCED_SECRET_PATTERNS = [
    re.compile(r"(?i)(?:secret|token|key|password|pwd|pass)\s*[:\-]?\s*['\"]?([A-Za-z0-9_\-+/=]{8,})['\"]?", re.IGNORECASE),
    re.compile(r"(?i)(?:sk|pk|ak|sk-|pk-|ak-)[A-Za-z0-9_\-+/=]{10,}", re.IGNORECASE),
    re.compile(r"(?i)(?:[a-z]{2,}_)?(?:api[_-]?)?(?:secret|key)[_-]?(?:key)?\s*[:\-]?\s*['\"]?([A-Za-z0-9_\-+/=]{15,})['\"]?", re.IGNORECASE)
]

class SecretsDetector:
    def __init__(self, patterns_dir: str,
                 enable_regex: bool = True,
                 enable_entropy: bool = True,
                 enable_context: bool = True,
                 enable_enhanced: bool = True,  # New feature
                 entropy_threshold: float = 3.5,  # Lowered threshold for better detection
                 min_token_len: int = 15,  # Reduced minimum length
                 context_window_chars: int = 50):  # Increased context window
        self.enable_regex = enable_regex
        self.enable_entropy = enable_entropy
        self.enable_context = enable_context
        self.enable_enhanced = enable_enhanced  # New parameter
        self.entropy_threshold = entropy_threshold
        self.min_token_len = min_token_len
        self.context_window_chars = context_window_chars

        self.signatures: List[Dict[str, Any]] = []
        self._load_patterns(patterns_dir)
        self._compile()

    def _load_patterns(self, patterns_dir: str):
        p = Path(patterns_dir) / "signatures.json"
        if not p.exists():
            raise FileNotFoundError(f"patterns file not found: {p}")
        self.signatures = json.loads(p.read_text())

    def _compile(self):
        for s in self.signatures:
            if s.get("type") == "regex":
                s["_re"] = re.compile(s["pattern"])

    def regex_scan(self, text: str, categories: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        if not self.enable_regex:
            return []
        cats = {c.upper() for c in categories} if categories else None
        matches = []
        for sig in self.signatures:
            if sig.get("type") != "regex":
                continue
            if cats and sig["category"].upper() not in cats:
                continue
            rx = sig.get("_re")
            if not rx:
                continue
            for m in re.finditer(rx, text):
                s, e = m.span()
                n = len(text)
                s, e = clamp_span(s, e, n)
                snippet = text[max(0, s-16):min(n, e+16)]
                matches.append({
                    "engine": "regex",
                    "id": sig["id"],
                    "category": sig["category"],
                    "severity": int(sig.get("severity", 3)),
                    "value": m.group(0),
                    "start": s,
                    "end": e,
                    "score": 1.0,
                    "snippet": snippet
                })
        return matches

    def entropy_scan(self, text: str) -> List[Dict[str, Any]]:
        if not self.enable_entropy:
            return []
        findings = []
        # Heuristic token candidates: long base64/hex/URL-safe runs
        # Enhanced to better handle potential secrets
        for m in re.finditer(r"[A-Za-z0-9_\-+/=]{%d,}" % self.min_token_len, text):
            s, e = m.span()
            token = m.group(0)
            # ignore obvious non-secret noise (e.g., long words of letters only)
            if not re.search(r"[0-9/=+_-]", token):
                continue
            H = shannon_entropy(token)
            if H >= self.entropy_threshold:
                # Context boost: look around the token for secret-ish words
                ctx_score = 0.0
                if self.enable_context:
                    L = max(0, s - self.context_window_chars)
                    R = min(len(text), e + self.context_window_chars)
                    context = text[L:R]
                    if CONTEXT_WORDS.search(context):
                        ctx_score = 0.5
                findings.append({
                    "engine": "entropy",
                    "id": "HIGH_ENTROPY",
                    "category": "GENERIC",
                    "severity": 4,
                    "value": token,
                    "start": s,
                    "end": e,
                    "score": float(min(1.0, (H - self.entropy_threshold) / 2.0 + ctx_score))
                })
        return findings

    def enhanced_scan(self, text: str) -> List[Dict[str, Any]]:
        """New enhanced scanning method to detect secrets with spaces or formatting"""
        if not self.enable_enhanced:
            return []
        
        findings = []
        
        # 1. Look for common secret patterns with spaces or formatting
        for pattern in ENHANCED_SECRET_PATTERNS:
            for m in re.finditer(pattern, text):
                # Get the full match and potential secret value
                full_match = m.group(0)
                secret_value = m.group(1) if len(m.groups()) > 0 else full_match
                
                # If we have a captured group, use it as the secret value
                if len(m.groups()) > 0 and m.group(1):
                    secret_value = m.group(1)
                
                s, e = m.span()
                n = len(text)
                s, e = clamp_span(s, e, n)
                
                # Calculate entropy for the potential secret
                H = shannon_entropy(secret_value)
                
                # Even if entropy is low, if it matches a strong pattern, flag it
                if H >= self.entropy_threshold * 0.7 or len(secret_value) >= self.min_token_len * 1.5:
                    # Context check
                    ctx_score = 0.0
                    if self.enable_context:
                        L = max(0, s - self.context_window_chars)
                        R = min(len(text), e + self.context_window_chars)
                        context = text[L:R]
                        if CONTEXT_WORDS.search(context):
                            ctx_score = 0.5
                    
                    score = float(min(1.0, (H - (self.entropy_threshold * 0.7)) / 2.0 + 0.3 + ctx_score))
                    
                    findings.append({
                        "engine": "enhanced",
                        "id": "POTENTIAL_SECRET",
                        "category": "GENERIC",
                        "severity": 3,
                        "value": secret_value,
                        "start": s,
                        "end": e,
                        "score": score
                    })
        
        # 2. Look for common password patterns
        password_patterns = [
            (r"(?i)(?:password|pwd|pass)\s*[:\-]?\s*['\"]([^\s\"']{6,})['\"]?", "PASSWORD_PATTERN"),
            (r"(?i)(?:key|token|secret)\s*[:\-]?\s*['\"]([^\s\"']{8,})['\"]?", "KEY_PATTERN")
        ]
        
        for pattern, pattern_id in password_patterns:
            for m in re.finditer(pattern, text):
                if len(m.groups()) > 0 and m.group(1):
                    secret_value = m.group(1)
                    s, e = m.span(1)  # Get span of the captured group
                    n = len(text)
                    s, e = clamp_span(s, e, n)
                    
                    # Even simple passwords should be flagged
                    findings.append({
                        "engine": "enhanced",
                        "id": pattern_id,
                        "category": "GENERIC",
                        "severity": 3,
                        "value": secret_value,
                        "start": s,
                        "end": e,
                        "score": 0.8
                    })
        
        return findings

    def detect(self, text: str, categories: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        out = []
        out.extend(self.regex_scan(text, categories))
        out.extend(self.entropy_scan(text))
        out.extend(self.enhanced_scan(text))  # Added enhanced scanning
        
        # dedupe: prefer regex over others on overlap, then enhanced over entropy
        out.sort(key=lambda x: (
            x["start"] if x.get("start") is not None else 10**12,
            -(x["end"]-x["start"]) if x.get("start") is not None else 0,
            0 if x["engine"] == "regex" else (1 if x["engine"] == "enhanced" else 2)
        ))
        
        merged = []
        used = [False] * len(out)
        for i, a in enumerate(out):
            if used[i]:
                continue
            merged.append(a)
            if a.get("start") is None:  # entropy without span shouldn't block others
                continue
            for j in range(i+1, len(out)):
                b = out[j]
                if used[j] or b.get("start") is None:
                    continue
                if not (b["end"] <= a["start"] or b["start"] >= a["end"]):
                    # overlap → discard lower-priority engine
                    if (a["engine"] == "regex" and b["engine"] in ["enhanced", "entropy"]) or \
                       (a["engine"] == "enhanced" and b["engine"] == "entropy"):
                        used[j] = True
        return merged