from __future__ import annotations
import os
import re
import json
from typing import List, Dict, Set, Tuple, Any
from pathlib import Path

# Load .env file to ensure environment variables are available
from dotenv import load_dotenv
load_dotenv(dotenv_path=Path(__file__).parent / ".env", override=True)

class EnhancedToxicityModel:
    """
    Enhanced toxicity detection that combines ML models with pattern-based detection
    for better coverage of edge cases and disguised toxicity.
    """

    def __init__(self):
        self.detoxify_model = None
        self._init_detoxify()
        self._init_patterns()

    def _init_detoxify(self):
        """Initialize Detoxify model if available"""
        self.detoxify_model = None
        self.model_type = None

        try:
            from detoxify import Detoxify
            import torch
            import transformers

            print("🔧 Checking system compatibility...")
            print(f"PyTorch version: {torch.__version__}")
            print(f"Transformers version: {transformers.__version__}")

            # Try each model variant in order of preference
            model_variants = ["original", "unbiased", "multilingual"]
            fam = os.getenv("DETOXIFY_MODEL", "original").strip().lower()

            if fam not in model_variants:
                fam = "original"

            # Try requested model first, then fallback to others
            models_to_try = [fam] + [m for m in model_variants if m != fam]

            for model_name in models_to_try:
                try:
                    print(f"🤖 Attempting to load Detoxify model: {model_name}")

                    # Force model download if not present
                    model = Detoxify(model_name, device='cpu')

                    # Test the model with a simple prediction
                    test_result = model.predict(["test"])
                    if test_result and isinstance(test_result, dict):
                        self.detoxify_model = model
                        self.model_type = model_name
                        print(f"✅ Detoxify model '{model_name}' loaded and tested successfully")
                        break
                    else:
                        print(f"⚠️ Model '{model_name}' loaded but failed prediction test")

                except Exception as model_error:
                    print(f"❌ Failed to load model '{model_name}': {model_error}")
                    continue

            if self.detoxify_model is None:
                print("⚠️ All Detoxify models failed, falling back to pattern-based detection only")

        except ImportError as e:
            print(f"⚠️ Required ML libraries not available: {e}")
            print("Falling back to pattern-based detection only")
        except Exception as e:
            print(f"⚠️ Detoxify initialization failed: {e}")
            print("Falling back to pattern-based detection only")

    def _init_patterns(self):
        """Initialize regex patterns for disguised toxicity"""

        # Leetspeak mappings
        self.leet_map = {
            '4': 'a', '@': 'a', '3': 'e', '1': 'i', '!': 'i', '0': 'o',
            '$': 's', '5': 's', '7': 't', '2': 'z', '8': 'b', '9': 'g'
        }

        # Toxic words patterns (including variations) with enhanced word boundary checks
        self.toxic_patterns = [
            # Direct slurs and hate speech - enhanced with word boundaries
            r'\b(?:n+i+g+e+r+s?|f+a+g+o+t+s?|k+i+k+e+s?|c+h+i+n+k+s?|s+p+i+c+s?)\b',
            r'\b(?:r+e+t+a+r+d+s?|c+r+i+p+p+l+e+d?|l+u+n+a+t+i+c+s?)\b',

            # Sexual harassment - enhanced context
            r'\b(?:r+a+p+e+s?|m+o+l+e+s+t+|g+r+o+p+e+s?|a+s+s+a+u+l+t+s?)\b',
            r'\b(?:s+e+x+u+a+l+\s+harass+|unwan+ed+\s+advance+s?)\b',

            # Threats - enhanced with context and boundaries
            r'\b(?:k+i+l+l+|m+u+r+d+e+r+|d+i+e+|d+e+a+t+h+|h+a+r+m+)\b.*\b(?:y+o+u+|u+r+|f+a+m+i+l+y+)\b',
            r'\b(?:g+o+i+n+g+\s+to\s+h+u+r+t+|teach+\s+a\s+lesson+)\b',
            r'\b(?:s+h+o+o+t+|s+t+a+b+|h+i+t+|b+e+a+t+).*(?:y+o+u+|u+r+)\b',

            # Severe profanity - enhanced boundaries
            r'\b(?:f+u+c+k+|s+h+i+t+|c+u+n+t+|b+i+t+c+h+|a+s+s+h+o+l+e+|b+a+s+t+a+r+d+)\b',

            # Self-harm encouragement - enhanced boundaries
            r'\b(?:k+i+l+l+\s*y+o+u+r+s+e+l+f+|s+l+i+t+\s*w+r+i+s+t+s?|c+o+m+m+i+t+\s*s+u+i+c+i+d+e+)\b',

            # Disguised with spaces or characters - enhanced patterns
            r'f\s*?u\s*?c\s*?k|f\*u\*c\*k|f!u!c!k|f@\$\$k',
            r's\s*?h\s*?i\s*?t|s\*h\*i\*t|s!h!i!t',
            r'f\s+?u\s+?c\s+?k|d\s+?i\s+?e\s+\b\s+?y\s+?o\s+?u',

            # Terrorism/violence - enhanced with boundaries
            r'\b(?:b+o+m+b+|t+e+r+r+o+r+|a+t+t+a+c+k+|v+i+o+l+e+n+c+e+)\b',
            r'\b(?:h+o+l+y+\s+w+a+r+|j+i+h+a+d+|e+x+t+r+e+m+i+s+t+)\b',

            # New patterns for modern threats and abuse
            r'\b(?:dox+|swat+|ddos+)\b',  # Digital threats
            r'\b(?:unalive+\s*?yourself+\s*?|k+y+s+)\b',  # Alarming content
            r'\b(?:cancel+|deplatform+|report+\s+?spam)\b',  # Coordinated harassment
        ]

        # Compile patterns
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.toxic_patterns]

        # Subtle toxicity indicators
        self.sarcastic_patterns = [
            r"\b(real|such a|quite the|what a|some)\s+\w+\s+(genius|expert|master|professional)\b",
            r"\bmust be nice to\b",
            r"\bbless your (heart|soul)\b",
            r"\bclearly\b.*\bexpert\b",
            r"\bit must be\b",
        ]

        self.passive_aggressive_patterns = [
            r"\b(perhaps|maybe|just saying|no offense but)\b",
            r"\bwith all due respect\b",
            r"\bnot to be rude but\b",
            r"\bI'm not being mean but\b",
            r"\byou realize.*right\b",
        ]

        # Contextual non-toxic patterns
        self.context_exceptions = {
            'medical': [
                r'\b(patient|medical|clinical|anatomy|examination|treatment)\b',
                r'\b(sexual organ|breast|genital|reproductive)\b',
            ],
            'academic': [
                r'\b(study|research|analysis|paper|journal)\b',
                r'\b(gender identity|sexual orientation|racial dynamics)\b',
            ],
            'news': [
                r'\b(report|according to|police said|officials|sources)\b',
                r'\b(threat was called|incident occurred|authorities report)\b',
            ],
            'literature': [
                r'\b(book|novel|story|character|author)\b',
                r'\b(fiction|literature|poetry|drama)\b',
            ]
        }

        # Compile context patterns
        self.context_patterns = {
            context: [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
            for context, patterns in self.context_exceptions.items()
        }

    def _normalize_leetspeak(self, text: str) -> str:
        """Convert leetspeak to normal text for detection"""
        normalized = text.lower()
        for leet_char, normal_char in self.leet_map.items():
            normalized = normalized.replace(leet_char, normal_char)
        return normalized

    def _detect_pattern_toxicity(self, text: str) -> List[Dict[str, Any]]:
        """Detect toxicity using regex patterns"""
        flagged = []
        normalized_text = self._normalize_leetspeak(text)

        # Check main toxicity patterns
        for i, pattern in enumerate(self.compiled_patterns):
            matches = pattern.finditer(normalized_text)
            for match in matches:
                matched_text = text[match.start():match.end()]

                # Determine category and score based on pattern index and content
                category = "toxicity"
                score = 0.9

                # Use the original pattern string for category detection
                original_pattern = self.toxic_patterns[i] if i < len(self.toxic_patterns) else ""

                # Category mapping based on pattern index and content
                if 3 <= i <= 5:  # Threat patterns indices
                    category = "threat"
                    score = 0.95
                elif 1 <= i <= 2:  # Direct slurs and hate speech
                    category = "severe_toxicity"
                    score = 0.95
                elif 6 <= i <= 7:  # Sexual harassment patterns
                    category = "sexual_explicit"
                    score = 0.95
                elif 8 <= i <= 9:  # Severe profanity patterns
                    category = "obscene"
                    score = 0.85
                elif 10 <= i <= 12:  # Disguised patterns
                    category = "obscene"
                    score = 0.85
                elif 13 <= i <= 14:  # Terrorism/violence
                    category = "threat"
                    score = 0.95
                elif 15 <= i <= 17:  # Modern threats and abuse
                    if i == 15:  # Digital threats
                        category = "threat"
                    elif i == 16:  # Alarming content (self-harm)
                        category = "severe_toxicity"
                    else:  # Coordinated harassment
                        category = "threat"
                    score = 0.95

                # Additional content-based checks as fallback
                matched_lower = matched_text.lower()
                if "kill" in matched_lower or "murder" in matched_lower or "die" in matched_lower:
                    category = "threat"
                    score = 0.95
                elif "rape" in matched_lower or "molest" in matched_lower or "sexual" in matched_lower:
                    category = "sexual_explicit"
                    score = 0.95

                flagged.append({
                    "type": "pattern_toxicity",
                    "category": category,
                    "score": score,
                    "span": [match.start(), match.end()],
                    "text": matched_text,
                    "pattern": original_pattern
                })

        # Check subtle toxicity
        for pattern_text in self.sarcastic_patterns:
            pattern = re.compile(pattern_text, re.IGNORECASE)
            match = pattern.search(text)
            if match:
                flagged.append({
                    "type": "sarcastic_insult",
                    "score": 0.7,
                    "span": [match.start(), match.end()],
                    "text": text[match.start():match.end()],
                    "pattern": pattern_text
                })

        for pattern_text in self.passive_aggressive_patterns:
            pattern = re.compile(pattern_text, re.IGNORECASE)
            match = pattern.search(text)
            if match:
                flagged.append({
                    "type": "passive_aggressive",
                    "score": 0.6,
                    "span": [match.start(), match.end()],
                    "text": text[match.start():match.end()],
                    "pattern": pattern_text
                })

        return flagged

    def _check_context_exceptions(self, text: str) -> str:
        """Check if text falls under context exceptions"""
        for context, patterns in self.context_patterns.items():
            for pattern in patterns:
                if pattern.search(text):
                    return context
        return None

    def score(self, texts: List[str]) -> List[Dict[str, float]]:
        """Enhanced scoring combining ML and pattern detection"""
        if not texts:
            return []

        results = []

        for text in texts:
            # Initialize with empty scores
            scores = {
                "toxicity": 0.0,
                "severe_toxicity": 0.0,
                "obscene": 0.0,
                "threat": 0.0,
                "insult": 0.0,
                "identity_attack": 0.0,
                "sexual_explicit": 0.0,
                "pattern_toxicity": 0.0,
                "sarcastic_insult": 0.0,
                "passive_aggressive": 0.0,
            }

            # Check context exceptions
            context = self._check_context_exceptions(text)
            if context:
                # Lower thresholds for academic/medical contexts
                base_multiplier = 0.3 if context in ['medical', 'academic'] else 0.6

            # ML-based detection if available
            if self.detoxify_model:
                try:
                    ml_result = self.detoxify_model.predict([text])
                    for label, score_list in ml_result.items():
                        if label.lower() in scores:
                            ml_score = float(score_list[0])
                            if context:
                                ml_score *= base_multiplier
                            scores[label.lower()] = max(scores[label.lower()], ml_score)
                except Exception as e:
                    print(f"Warning: ML model prediction failed: {e}")

            # Pattern-based detection
            pattern_flags = self._detect_pattern_toxicity(text)
            for flag in pattern_flags:
                flag_type = flag["type"]
                score = flag["score"]
                if context:
                    score *= base_multiplier

                # Use the improved category mapping from pattern detection
                if "category" in flag:
                    # Use the category determined by pattern detection
                    category = flag["category"]
                    if category in scores:
                        scores[category] = max(scores[category], score)
                elif flag_type in scores:
                    scores[flag_type] = max(scores[flag_type], score)
                else:
                    # Legacy mapping for backward compatibility
                    if "threat" in flag.get("pattern", "") or any(word in flag["text"].lower() for word in ["kill", "murder", "harm", "die"]):
                        scores["threat"] = max(scores["threat"], score)
                    elif any(word in flag["text"].lower() for word in ["fuck", "shit", "cunt"]):
                        scores["obscene"] = max(scores["obscene"], score)
                    elif flag_type in ["sarcastic_insult", "passive_aggressive"]:
                        scores["insult"] = max(scores["insult"], score * 0.8)
                    else:
                        scores["toxicity"] = max(scores["toxicity"], score)

            results.append(scores)

        return results

    def predict_toxicity(self, text: str) -> Dict[str, float]:
        """
        Legacy method for hybrid detection compatibility.
        Returns simplified toxicity scores.
        """
        scores_list = self.score([text])
        if scores_list:
            return scores_list[0]
        return {
            "toxicity": 0.0,
            "severe_toxicity": 0.0,
            "obscene": 0.0,
            "threat": 0.0,
            "insult": 0.0,
            "identity_attack": 0.0,
            "sexual_explicit": 0.0
        }

    def get_model_status(self) -> Dict[str, Any]:
        """
        Returns the current status of the model for health checks
        """
        return {
            "ml_model_loaded": self.detoxify_model is not None,
            "model_type": self.model_type,
            "pattern_detection_available": True,
            "context_awareness": True
        }