"""
Debug script for testing the enhanced matcher
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from enhanced_matcher import EnhancedBanMatcher

# Create matcher
matcher = EnhancedBanMatcher("lists")

# Test cases
test_cases = [
    "Microsoft announced a new product",
    "Our product is better than Microsoft",
    "competitorxyz makes better products",
    "This fakecasino is a scam"
]

print("Testing enhanced matcher:")
print(f"Loaded {len(matcher.ban_entries)} ban entries")
print(f"Loaded {len(matcher.competitors)} competitors: {list(matcher.competitors)}")

for text in test_cases:
    print(f"\nTesting: '{text}'")
    matches = matcher.find(text)
    print(f"Matches found: {len(matches)}")
    for match in matches:
        print(f"  - {match}")