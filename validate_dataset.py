#!/usr/bin/env python3
"""
Validate the training dataset for duplicates, quality issues, and completeness
"""

import json
from collections import Counter
from typing import Dict, List, Set

def validate_dataset():
    """Perform comprehensive dataset validation"""
    dataset_path = "/Users/yavar/Documents/CoE/z_grid/gibberish_service/training_data/gibberish_training_dataset.json"

    with open(dataset_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print("🔍 DATASET VALIDATION REPORT")
    print("=" * 60)

    # Basic stats
    total_samples = len(data['training_samples'])
    print(f"📊 Total samples: {total_samples}")
    print(f"📈 Target was: {data['metadata']['target_total']}")

    # Check for duplicates
    print("\n🔄 DUPLICATE ANALYSIS:")
    texts = [sample['text'] for sample in data['training_samples']]
    text_counts = Counter(texts)

    duplicates = {text: count for text, count in text_counts.items() if count > 1}
    if duplicates:
        print(f"❌ Found {len(duplicates)} duplicate texts:")
        for text, count in duplicates.items():
            print(f"   ({count}x): {text[:50]}...")
    else:
        print("✅ No duplicate texts found")

    # Check category distribution
    print("\n📋 CATEGORY DISTRIBUTION:")
    good_samples = [s for s in data['training_samples'] if s['label'] == 'good']
    gibberish_samples = [s for s in data['training_samples'] if s['label'] == 'gibberish']

    print(f"   Good samples: {len(good_samples)} ({len(good_samples)/total_samples*100:.1f}%)")
    print(f"   Gibberish samples: {len(gibberish_samples)} ({len(gibberish_samples)/total_samples*100:.1f}%)")

    # Category breakdown
    good_categories = Counter(s['category'] for s in good_samples)
    gibberish_categories = Counter(s['category'] for s in gibberish_samples)

    print("\n   GOOD CATEGORIES:")
    for cat, count in sorted(good_categories.items()):
        print(f"      {cat}: {count}")

    print("\n   GIBBERISH CATEGORIES:")
    for cat, count in sorted(gibberish_categories.items()):
        print(f"      {cat}: {count}")

    # Check for quality issues
    print("\n🔍 QUALITY ISSUES:")

    # Very short samples
    very_short = [s for s in data['training_samples'] if len(s['text'].strip()) < 5]
    if very_short:
        print(f"⚠️  {len(very_short)} very short samples (< 5 chars):")
        for s in very_short:
            print(f"      '{s['text']}' [{s['label']}]")

    # Very long samples
    very_long = [s for s in data['training_samples'] if len(s['text']) > 200]
    if very_long:
        print(f"⚠️  {len(very_long)} very long samples (> 200 chars):")
        for s in very_long:
            print(f"      Length: {len(s['text'])} [{s['label']}] - {s['text'][:50]}...")

    # Samples with special characters only
    special_only = [s for s in data['training_samples'] if not any(c.isalnum() for c in s['text'])]
    if special_only:
        print(f"⚠️  {len(special_only)} samples with only special characters:")
        for s in special_only:
            print(f"      '{s['text']}' [{s['label']}]")

    # Check for potentially mislabeled samples
    print("\n🏷️  POTENTIAL MISLABELS:")

    # Good samples that look like gibberish
    suspicious_good = []
    for s in good_samples:
        text = s['text'].lower()
        # Check for keyboard patterns
        if any(pattern in text for pattern in ['asdf', 'qwer', 'zxcv', 'qwerty']):
            suspicious_good.append(s)
        # Check for excessive repetition
        if len(set(text)) < len(text) * 0.3 and len(text) > 10:
            suspicious_good.append(s)

    if suspicious_good:
        print(f"⚠️  {len(suspicious_good)} 'good' samples that look like gibberish:")
        for s in suspicious_good[:5]:  # Show first 5
            print(f"      '{s['text']}' [category: {s['category']}]")
        if len(suspicious_good) > 5:
            print(f"      ... and {len(suspicious_good)-5} more")

    # Gibberish samples that might be valid
    suspicious_gibberish = []
    for s in gibberish_samples:
        text = s['text'].lower()
        # Check for common words
        common_words = ['the', 'and', 'you', 'for', 'are', 'with', 'have', 'this']
        if any(word in text for word in common_words):
            suspicious_gibberish.append(s)
        # Check for sentence structure
        if ' ' in text and len(text.split()) >= 3:
            suspicious_gibberish.append(s)

    if suspicious_gibberish:
        print(f"⚠️  {len(suspicious_gibberish)} 'gibberish' samples that might be valid:")
        for s in suspicious_gibberish[:5]:  # Show first 5
            print(f"      '{s['text']}' [category: {s['category']}]")
        if len(suspicious_gibberish) > 5:
            print(f"      ... and {len(suspicious_gibberish)-5} more")

    # Missing required fields
    missing_fields = []
    for i, s in enumerate(data['training_samples']):
        missing = []
        if 'text' not in s or not s['text']:
            missing.append('text')
        if 'label' not in s:
            missing.append('label')
        if 'category' not in s:
            missing.append('category')
        if missing:
            missing_fields.append(f"Sample {i}: missing {', '.join(missing)}")

    if missing_fields:
        print(f"❌ Missing fields in {len(missing_fields)} samples:")
        for issue in missing_fields:
            print(f"      {issue}")

    # Summary
    print("\n📋 VALIDATION SUMMARY:")
    issues = len(duplicates) + len(very_short) + len(special_only) + len(missing_fields)

    if issues == 0:
        print("✅ Dataset looks clean!")
    else:
        print(f"⚠️  Found {issues} issues to address:")
        print(f"   - Duplicates: {len(duplicates)}")
        print(f"   - Very short: {len(very_short)}")
        print(f"   - Special only: {len(special_only)}")
        print(f"   - Missing fields: {len(missing_fields)}")

    return {
        'total_samples': total_samples,
        'duplicates': len(duplicates),
        'good_samples': len(good_samples),
        'gibberish_samples': len(gibberish_samples),
        'issues': issues,
        'quality_score': (total_samples - issues) / total_samples * 100
    }

if __name__ == "__main__":
    validation_results = validate_dataset()