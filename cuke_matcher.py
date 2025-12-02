import re
from typing import List, Dict, Any, Optional, Tuple
from cucumber_expressions.expression import CucumberExpression
from cucumber_expressions.parameter_type_registry import ParameterTypeRegistry
from cucumber_expressions.argument import Argument
from param_types import register_defaults

class MatchResult:
    def __init__(self, ok: bool, expr: Optional[str], vars: Dict[str, Any], spans: Dict[str, Tuple[int,int]]):
        self.ok = ok
        self.expr = expr
        self.vars = vars
        self.spans = spans

def _registry(case_sensitive: bool) -> ParameterTypeRegistry:
    reg = ParameterTypeRegistry()
    register_defaults(reg)
    if not case_sensitive:
        # cucumber-expressions is case-insensitive for parameter types via regex flags
        # We already chose case-agnostic regexes for custom types; for literals, handle text lowering
        pass
    return reg

def match_any(text: str, expressions: List[str], case_sensitive: bool=False) -> MatchResult:
    reg = _registry(case_sensitive)

    for expr in expressions:
        ce = CucumberExpression(expr, reg)
        args = ce.match(text)
        if args is None:
            # try case-insensitive fallback if not case_sensitive
            if not case_sensitive:
                try:
                    # Try matching with lowercase text for comparison
                    lower_text = text.lower()
                    lower_expr = expr.lower()
                    # Create a new expression with the lowercased pattern for matching
                    args = ce.match(lower_text)
                    if args is not None:
                        # Use original text for span extraction but matched args
                        pass
                except:
                    pass
            if args is None:
                continue

        # Map positional args back to parameter names (in order of occurrence)
        # cucumber-expressions returns a list of Argument – each has group.value, etc.
        named: Dict[str, Any] = {}
        spans: Dict[str, Tuple[int,int]] = {}

        # Get the groups from the match to properly extract spans
        for i, arg in enumerate(args):
            key = arg.parameter_type.name if arg.parameter_type else f"arg{i}"
            val = arg.value
            named[key] = val

            # Extract the actual span from the argument's group using properties
            if arg.group:
                spans[key] = (arg.group.start, arg.group.end)

        # Additional validation: ensure the match is not overly permissive
        # For expressions with specific parameters, ensure they actually extracted meaningful values
        if _is_meaningful_match(expr, named, text):
            return MatchResult(True, expr, named, spans)

    return MatchResult(False, None, {}, {})

def _is_meaningful_match(expr: str, named_vars: Dict[str, Any], text: str) -> bool:
    """Check if the match is meaningful and not overly permissive"""
    # If expression contains {int}, ensure we got a proper integer
    if "{int}" in expr and "int" in named_vars:
        try:
            int(named_vars["int"])
        except (ValueError, TypeError):
            return False

    # If expression contains {word}, ensure we got a non-empty word
    if "{word}" in expr and "word" in named_vars:
        if not named_vars["word"] or not str(named_vars["word"]).strip():
            return False

    # For complex expressions with multiple parameters, ensure we extracted most of them
    param_count = expr.count("{")
    extracted_count = len([v for v in named_vars.values() if v is not None and str(v).strip()])

    # Allow at most 1 missing parameter (for optional parts)
    if param_count > 0 and extracted_count < max(1, param_count - 1):
        return False

    # Ensure the match covers a significant portion of the text
    # This prevents overly generic matches
    total_match_length = sum(len(str(v)) for v in named_vars.values() if v)
    if total_match_length < len(text) * 0.3:  # Match should cover at least 30% of text
        return False

    return True

def filter_nonmatching(text: str, expressions: List[str], case_sensitive: bool=False) -> str:
    # If you choose ACTION_ON_FAIL=filter we remove everything not covered by any expression tokens.
    # Extract only the parts that match expressions
    result = match_any(text, expressions, case_sensitive)
    
    if not result.ok or not result.spans:
        # No matches found, return empty string
        return ""
    
    # Extract the matched parts from the text
    matched_parts = []
    for key, (start, end) in sorted(result.spans.items(), key=lambda x: x[1][0]):
        matched_parts.append(text[start:end])
    
    # Join the matched parts with spaces
    return " ".join(matched_parts) if matched_parts else ""
