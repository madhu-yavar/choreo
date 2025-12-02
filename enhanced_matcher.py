"""
Enhanced Ban Matcher with Context-Aware Competitor Detection
"""
import os
import json
import re
from typing import List, Dict, Any, Optional
from pathlib import Path
import custom_config

class EnhancedBanMatcher:
    def __init__(self, lists_dir: str = "lists"):
        self.lists_dir = Path(lists_dir)
        self.ban_entries = []
        self.allow_phrases = []
        self.competitors = set()
        self._load_lists()
        
    def _load_lists(self):
        """Load ban lists and competitor database"""
        # Load existing ban lists
        for file_path in self.lists_dir.glob("banlist.*.json"):
            try:
                with open(file_path, 'r') as f:
                    entries = json.load(f)
                    self.ban_entries.extend(entries)
            except Exception as e:
                print(f"Warning: Could not load {file_path}: {e}")
        
        # Load allow list
        allow_file = self.lists_dir / "allow.json"
        if allow_file.exists():
            try:
                with open(allow_file, 'r') as f:
                    self.allow_phrases = json.load(f)
            except Exception as e:
                print(f"Warning: Could not load {allow_file}: {e}")
        
        # Load custom bans using the same method as the standard matcher
        try:
            custom_bans = custom_config.load_custom_bans("ban_service")
            self.ban_entries.extend(custom_bans)
        except Exception as e:
            print(f"Warning: Could not load custom bans: {e}")
        
        # Extract competitors from ALL ban entries
        for entry in self.ban_entries:
            if entry.get("category") == "COMPETITOR":
                self.competitors.add(entry["pattern"].lower())
                
        print(f"Loaded {len(self.ban_entries)} ban entries and {len(self.competitors)} competitors")
    
    def _check_allow_list(self, text: str) -> bool:
        """Check if text matches any allow phrases"""
        text_lower = text.lower()
        for phrase in self.allow_phrases:
            if phrase.lower() in text_lower:
                return True
        return False
    
    def _exact_matches(self, text: str) -> List[Dict]:
        """Find exact matches in ban lists"""
        matches = []
        text_lower = text.lower()
        
        for entry in self.ban_entries:
            pattern = entry["pattern"]
            if entry["type"] == "literal":
                # Use word boundaries but exclude possessive forms
                # This regex looks for the pattern as a whole word that is NOT followed by 's or 'S
                regex_pattern = r'\b' + re.escape(pattern) + r"\b(?!\s*'s\b)(?!\s*'S\b)"
                for match in re.finditer(regex_pattern, text_lower, re.IGNORECASE):
                    start = match.start()
                    end = match.end()
                    matches.append({
                        "pattern": pattern,
                        "category": entry["category"],
                        "severity": entry["severity"],
                        "start": start,
                        "end": end,
                        "engine": "exact",
                        "value": text[start:end],  # Add the matched text value
                        "score": 100
                    })
            elif entry["type"] == "regex":
                try:
                    regex = re.compile(pattern, re.IGNORECASE)
                    for match in regex.finditer(text):
                        matches.append({
                            "pattern": pattern,
                            "category": entry["category"],
                            "severity": entry["severity"],
                            "start": match.start(),
                            "end": match.end(),
                            "engine": "regex",
                            "value": match.group(0),  # Add the matched text value
                            "score": 100
                        })
                except re.error:
                    continue
                    
        return matches
    
    def _detect_competitor_mentions(self, text: str) -> List[Dict]:
        """Detect competitor mentions in competitive contexts"""
        matches = []
        text_lower = text.lower()
        
        # Negation words that can change the meaning of a comparison
        negation_words = ["not", "n't", "no", "never", "neither", "nor"]
        
        # Specific competitive comparison patterns that indicate brand safety violations
        # These patterns look for explicit competitive comparisons where our product is being compared
        competition_patterns = [
            (r"better than\s+" + r"({}\b(?!\s*'s\b)(?!\s*'S\b))", 4),    # "better than Microsoft" (not "Microsoft's")
            (r"worse than\s+" + r"({}\b(?!\s*'s\b)(?!\s*'S\b))", 3),     # "worse than Microsoft"
            (r"compared to\s+" + r"({}\b(?!\s*'s\b)(?!\s*'S\b))", 4),    # "compared to Microsoft"
            (r"beats\s+" + r"({}\b(?!\s*'s\b)(?!\s*'S\b))", 4),          # "beats Microsoft"
            (r"loses to\s+" + r"({}\b(?!\s*'s\b)(?!\s*'S\b))", 3),       # "loses to Microsoft"
            (r"superior to\s+" + r"({}\b(?!\s*'s\b)(?!\s*'S\b))", 4),    # "superior to Microsoft"
            (r"inferior to\s+" + r"({}\b(?!\s*'s\b)(?!\s*'S\b))", 3),    # "inferior to Microsoft"
            (r"outperforms\s+" + r"({}\b(?!\s*'s\b)(?!\s*'S\b))", 4),    # "outperforms Microsoft"
            (r"outperformed by\s+" + r"({}\b(?!\s*'s\b)(?!\s*'S\b))", 3), # "outperformed by Microsoft"
            (r"dominates\s+" + r"({}\b(?!\s*'s\b)(?!\s*'S\b))", 4),      # "dominates Microsoft"
            (r"dominated by\s+" + r"({}\b(?!\s*'s\b)(?!\s*'S\b))", 3),   # "dominated by Microsoft"
            (r"vs\.?\s+" + r"({}\b(?!\s*'s\b)(?!\s*'S\b))", 4),          # "vs Microsoft" or "vs. Microsoft"
            (r"versus\s+" + r"({}\b(?!\s*'s\b)(?!\s*'S\b))", 4)          # "versus Microsoft"
        ]
        
        # Check for each competitor in competitive contexts
        for competitor in self.competitors:
            competitor_escaped = re.escape(competitor)
            
            # Look for competitive context patterns that include this competitor
            for pattern_template, severity in competition_patterns:
                # Replace the placeholder with the specific competitor
                full_pattern = pattern_template.format(competitor_escaped)
                for match in re.finditer(full_pattern, text_lower):
                    # Extract the competitor name from the match group
                    competitor_match = match.group(1)  # The competitor name is in group 1
                    competitor_start = match.start(1)
                    competitor_end = match.end(1)
                    
                    # Check if there's a negation word before the comparison
                    # Look for negation within a reasonable window before the comparison
                    comparison_start = match.start()
                    negation_window_start = max(0, comparison_start - 50)
                    negation_window = text_lower[negation_window_start:comparison_start]
                    
                    # Check if any negation word appears in the window
                    has_negation = any(neg_word in negation_window for neg_word in negation_words)
                    
                    # If there's negation, reduce the severity or skip entirely
                    # "not better than" should be less severe than "better than"
                    if has_negation:
                        # For "not better than", we might want to pass it entirely
                        # or reduce severity, depending on business logic
                        if "better than" in match.group().lower():
                            # "not better than" is generally a positive statement about the competitor
                            continue  # Skip flagging this
                    
                    matches.append({
                        "pattern": competitor,
                        "category": "COMPETITOR",
                        "severity": severity,
                        "start": competitor_start,
                        "end": competitor_end,
                        "engine": "enhanced_context",
                        "value": text[competitor_start:competitor_end],
                        "score": 100,
                        "details": "competitive_context"
                    })
                
        return matches
    
    def find(self, text: str, categories: Optional[List[str]] = None) -> List[Dict]:
        """Find all ban violations in text - enhanced version with context awareness"""
        if not text.strip():
            return []
            
        # Check allow list first
        if self._check_allow_list(text):
            return []
            
        matches = []
        
        # Find context-aware competitor mentions (this handles competitor-related violations)
        context_matches = self._detect_competitor_mentions(text)
        matches.extend(context_matches)
        
        # Find exact matches, but exclude competitor matches since those are handled by context matching
        for match in self._exact_matches(text):
            if match.get("category") != "COMPETITOR":
                matches.append(match)
            # For competitor exact matches, only include them if they were NOT handled by context matching
            # But since we trust our context matching, we'll defer to it
            # UNLESS there's no context match, which might mean it's a simple mention not covered by our patterns
        
        # Filter by categories if specified
        if categories:
            matches = [m for m in matches if m["category"] in categories]
            
        return matches

# Admin functions for competitor management
def add_competitor(competitor_name: str, lists_dir: str = "lists"):
    """Add a competitor to the ban list"""
    lists_path = Path(lists_dir)
    brand_list_file = lists_path / "banlist.brand.json"
    
    # Load existing brand list
    brand_entries = []
    if brand_list_file.exists():
        try:
            with open(brand_list_file, 'r') as f:
                brand_entries = json.load(f)
        except Exception as e:
            print(f"Warning: Could not load {brand_list_file}: {e}")
    
    # Add new competitor
    new_entry = {
        "pattern": competitor_name,
        "type": "literal",
        "category": "COMPETITOR",
        "severity": 3
    }
    
    # Check if competitor already exists
    for entry in brand_entries:
        if entry["pattern"].lower() == competitor_name.lower():
            return False, "Competitor already exists"
    
    brand_entries.append(new_entry)
    
    # Save updated list
    try:
        with open(brand_list_file, 'w') as f:
            json.dump(brand_entries, f, indent=2)
        return True, f"Added competitor: {competitor_name}"
    except Exception as e:
        return False, f"Error saving competitor: {e}"

def remove_competitor(competitor_name: str, lists_dir: str = "lists"):
    """Remove a competitor from the ban list"""
    lists_path = Path(lists_dir)
    brand_list_file = lists_path / "banlist.brand.json"
    
    # Load existing brand list
    brand_entries = []
    if brand_list_file.exists():
        try:
            with open(brand_list_file, 'r') as f:
                brand_entries = json.load(f)
        except Exception as e:
            print(f"Warning: Could not load {brand_list_file}: {e}")
            return False, f"Error loading competitor list: {e}"
    
    # Remove competitor
    original_count = len(brand_entries)
    brand_entries = [entry for entry in brand_entries if entry["pattern"].lower() != competitor_name.lower()]
    
    if len(brand_entries) == original_count:
        return False, "Competitor not found"
    
    # Save updated list
    try:
        with open(brand_list_file, 'w') as f:
            json.dump(brand_entries, f, indent=2)
        return True, f"Removed competitor: {competitor_name}"
    except Exception as e:
        return False, f"Error saving competitor list: {e}"