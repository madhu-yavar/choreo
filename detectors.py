import json
import os
import re
from pathlib import Path
from typing import List, Dict, Any, Optional

from utils import shannon_entropy, clamp_span

CONTEXT_WORDS = re.compile(r"(?i)(secret|token|key|apikey|api_key|password|passwd|pwd|authorization|bearer|client_secret|github|openai|gpt|chatgpt)")

# Enhanced context patterns for GitHub and OpenAI specific keywords
GITHUB_CONTEXT = re.compile(r"(?i)(github|gh[pousr]_|gho_|ghr_|repo|repository|commit|pull.?request|branch|gist)")
OPENAI_CONTEXT = re.compile(r"(?i)(openai|gpt|chatgpt|assistant|api|sk-|org-|sk-proj-)")

class SecretsDetector:
    def __init__(self, patterns_dir: str,
                 enable_regex: bool = True,
                 enable_entropy: bool = True,
                 enable_context: bool = True,
                 entropy_threshold: float = 4.0,
                 min_token_len: int = 20,
                 context_window_chars: int = 40):
        self.enable_regex = enable_regex
        self.enable_entropy = enable_entropy
        self.enable_context = enable_context
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
        for m in re.finditer(r"[A-Za-z0-9_\-+/=]{%d,}" % self.min_token_len, text):
            s, e = m.span()
            token = m.group(0)
            # ignore obvious non-secret noise (e.g., long words of letters only)
            if not re.search(r"[0-9/=+_-]", token):
                continue
            H = shannon_entropy(token)
            if H >= self.entropy_threshold:
                # Enhanced context boost: look around the token for secret-ish words
                ctx_score = 0.0
                category = "GENERIC"
                severity = 4

                if self.enable_context:
                    L = max(0, s - self.context_window_chars)
                    R = min(len(text), e + self.context_window_chars)
                    context = text[L:R]

                    # GitHub specific context detection
                    if GITHUB_CONTEXT.search(context):
                        ctx_score = 0.7
                        category = "GITHUB"
                        severity = 5
                        # Check for GitHub-specific patterns that might not match regex
                        if token.startswith(('ghp_', 'gho_', 'ghu_', 'ghs_', 'ghr_')):
                            findings.append({
                                "engine": "entropy",
                                "id": "GITHUB_PAT_ENTROPY",
                                "category": "DEV",
                                "severity": 5,
                                "value": token,
                                "start": s,
                                "end": e,
                                "score": 1.0
                            })
                            continue

                    # OpenAI specific context detection
                    elif OPENAI_CONTEXT.search(context):
                        ctx_score = 0.7
                        category = "OPENAI"
                        severity = 5
                        # Check for OpenAI-specific patterns
                        if token.startswith(('sk-', 'sk-proj-', 'org-')):
                            findings.append({
                                "engine": "entropy",
                                "id": "OPENAI_KEY_ENTROPY",
                                "category": "SAAS",
                                "severity": 5,
                                "value": token,
                                "start": s,
                                "end": e,
                                "score": 1.0
                            })
                            continue

                    # Generic secret context
                    elif CONTEXT_WORDS.search(context):
                        ctx_score = 0.5

                # Only add generic entropy detection if not already caught by specific patterns
                findings.append({
                    "engine": "entropy",
                    "id": "HIGH_ENTROPY",
                    "category": category,
                    "severity": severity,
                    "value": token,
                    "start": s,
                    "end": e,
                    "score": float(min(1.0, (H - self.entropy_threshold) / 2.0 + ctx_score))
                })
        return findings

    def detect(self, text: str, categories: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        out = []
        out.extend(self.regex_scan(text, categories))
        out.extend(self.entropy_scan(text))
        # dedupe: prefer regex over entropy on overlap
        out.sort(key=lambda x: (x["start"] if x.get("start") is not None else 10**12,
                                -(x["end"]-x["start"]) if x.get("start") is not None else 0,
                                0 if x["engine"]=="regex" else 1))
        merged = []
        used = [False]*len(out)
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
                    # overlap → discard lower-priority engine (entropy) or keep first (regex)
                    if a["engine"] == "regex" and b["engine"] == "entropy":
                        used[j] = True
        return merged