import json
import os
import re
from pathlib import Path
from typing import Dict, List, Tuple, Any

from rapidfuzz import fuzz

import utils
import custom_config

class BanMatcher:
    def __init__(self, lists_dir: str,
                 enable_regex: bool = True,
                 enable_fuzzy: bool = True,
                 fuzzy_default: int = 85,
                 enable_homoglyph: bool = True,
                 enable_leet: bool = True,
                 service_name: str = "ban_service"):
        self.enable_regex = enable_regex
        self.enable_fuzzy = enable_fuzzy
        self.fuzzy_default = fuzzy_default
        self.enable_homoglyph = enable_homoglyph
        self.enable_leet = enable_leet
        self.service_name = service_name

        self.ban_entries: List[Dict[str, Any]] = []
        self.allow_phrases: List[str] = []
        self._load_lists(lists_dir)
        self._load_custom_configs()
        self._prepare()

    def _load_lists(self, lists_dir: str):
        p = Path(lists_dir)
        base = p / "banlist.base.json"
        brand = p / "banlist.brand.json"
        allow = p / "allow.json"

        print(f"Loading lists from directory: {p.absolute()}")
        print(f"Base file exists: {base.exists()}")
        print(f"Brand file exists: {brand.exists()}")
        print(f"Allow file exists: {allow.exists()}")

        if base.exists():
            content = base.read_text()
            print(f"Base file content: {content}")
            self.ban_entries.extend(json.loads(content))
        if brand.exists():
            content = brand.read_text()
            print(f"Brand file content: {content}")
            self.ban_entries.extend(json.loads(content))
        if allow.exists():
            content = allow.read_text()
            print(f"Allow file content: {content}")
            self.allow_phrases = json.loads(content)
            
        # Load all other banlist.*.json files
        for banlist_file in p.glob("banlist.*.json"):
            if banlist_file.name not in ["banlist.base.json", "banlist.brand.json"]:
                try:
                    content = banlist_file.read_text()
                    print(f"Loading {banlist_file.name}: {content}")
                    self.ban_entries.extend(json.loads(content))
                except Exception as e:
                    print(f"Warning: Could not load {banlist_file}: {e}")

    def _load_custom_configs(self):
        # Load custom ban entries
        custom_bans = custom_config.load_custom_bans(self.service_name)
        self.ban_entries.extend(custom_bans)
        
        # Load custom allow phrases
        custom_allow = custom_config.load_custom_allow(self.service_name)
        self.allow_phrases.extend(custom_allow)

    def _prepare(self):
        # precompile regex
        for e in self.ban_entries:
            e.setdefault("category", "GENERAL")
            e.setdefault("type", "literal")  # literal | regex
            e.setdefault("severity", 3)
            e.setdefault("fuzzy", None)
            if e["type"] == "regex":
                e["_re"] = re.compile(e["pattern"], flags=re.IGNORECASE)

        # normalized patterns for fuzzy
        for e in self.ban_entries:
            e["_norm"] = utils.normalize_text(e["pattern"], self.enable_homoglyph, self.enable_leet)

        # normalized allowlist
        self._allow_norm = [utils.normalize_text(x, self.enable_homoglyph, self.enable_leet) for x in self.allow_phrases]

    def _in_allow_context(self, text: str, span: Tuple[int,int]) -> bool:
        if not self.allow_phrases:
            return False
        window = text[max(0, span[0]-30): span[1]+30].lower()
        return any(a.lower() in window for a in self.allow_phrases)

    def find(self, text: str, categories: List[str] = None) -> List[Dict[str,Any]]:
        categories = set([c.upper() for c in categories]) if categories else None
        findings: List[Dict[str,Any]] = []

        # 1) exact (phrase) using regex-escaped literals (case-insensitive)
        for e in self.ban_entries:
            if categories and e["category"].upper() not in categories:
                continue
            if e["type"] == "literal":
                # Use word boundaries but exclude possessive forms
                # This regex looks for the pattern as a whole word that is NOT followed by 's or 'S
                pattern = r'\b' + re.escape(e["pattern"]) + r"\b(?!\s*'s\b)(?!\s*'S\b)"
                pat = re.compile(pattern, flags=re.IGNORECASE)
                for m in pat.finditer(text):
                    span = (m.start(), m.end())
                    if self._in_allow_context(text, span):
                        continue
                    findings.append({
                        "engine": "exact",
                        "value": m.group(0),
                        "pattern": e["pattern"],
                        "category": e["category"],
                        "severity": e["severity"],
                        "score": 100,
                        "start": span[0],
                        "end": span[1],
                    })

        # 2) explicit regex patterns
        if self.enable_regex:
            for e in self.ban_entries:
                if e["type"] != "regex":
                    continue
                if categories and e["category"].upper() not in categories:
                    continue
                rx = e.get("_re")
                if not rx:
                    continue
                for m in rx.finditer(text):
                    span = (m.start(), m.end())
                    if self._in_allow_context(text, span):
                        continue
                    findings.append({
                        "engine": "regex",
                        "value": m.group(0),
                        "pattern": e["pattern"],
                        "category": e["category"],
                        "severity": e["severity"],
                        "score": 100,
                        "start": span[0],
                        "end": span[1],
                    })

        # 3) fuzzy / normalized (no precise spans)
        if self.enable_fuzzy:
            tnorm = utils.normalize_text(text, self.enable_homoglyph, self.enable_leet)
            # Also get the original text with spaces normalized for possessive form checking
            text_for_possessive_check = re.sub(r"[^0-9a-zA-Z']+", " ", text).strip()
            
            for e in self.ban_entries:
                if categories and e["category"].upper() not in categories:
                    continue
                norm_pat = e.get("_norm") or ""
                if not norm_pat or len(norm_pat) < 3:
                    continue
                thr = int(e.get("fuzzy") or self.fuzzy_default)
                score = fuzz.partial_ratio(norm_pat, tnorm)
                if score >= thr:
                    # Check if this might be a possessive form match
                    # If the pattern is a competitor name and we find it followed by 's or 'S in the original text,
                    # we should exclude it
                    is_possessive_form = False
                    if e.get("category") == "COMPETITOR":
                        # Look for the original pattern followed by 's or 'S in the original text
                        pattern_escaped = re.escape(e["pattern"])
                        possessive_pattern = pattern_escaped + r"[''`]s\b"
                        if re.search(possessive_pattern, text, re.IGNORECASE):
                            # Check if the fuzzy match is likely matching this possessive form
                            # We'll be conservative and exclude if there's any chance
                            is_possessive_form = True
                    
                    if is_possessive_form:
                        continue
                    
                    # we can't reliably map back spans after normalization; flag without span
                    findings.append({
                        "engine": "fuzzy",
                        "value": e["pattern"],
                        "pattern": e["pattern"],
                        "category": e["category"],
                        "severity": e["severity"],
                        "score": int(score),
                        "start": None,
                        "end": None,
                    })

        return self._merge_overlaps(findings)

    def _merge_overlaps(self, items: List[Dict[str,Any]]) -> List[Dict[str,Any]]:
        # prefer longer/higher severity when overlaps on exact/regex
        with_spans = [x for x in items if x["start"] is not None]
        no_spans = [x for x in items if x["start"] is None]
        with_spans.sort(key=lambda x: (x["start"], -(x["end"]-x["start"]), -x["severity"]))

        merged: List[Dict[str,Any]] = []
        cur = None
        for x in with_spans:
            if cur is None:
                cur = x
                continue
            if x["start"] <= cur["end"]:
                # overlap → extend end if longer
                if x["end"] > cur["end"]:
                    cur["end"] = x["end"]
                    cur["value"] = cur["value"] + text[cur["end"]:x["end"]] if False else cur["value"]
                # keep highest severity/score label
                if x["severity"] > cur["severity"]:
                    cur["category"] = x["category"]
                    cur["severity"] = x["severity"]
                continue
            merged.append(cur)
            cur = x
        if cur is not None:
            merged.append(cur)
        # add fuzzy/no-span at the end
        merged.extend(no_spans)
        return merged
