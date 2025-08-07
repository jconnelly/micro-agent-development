#!/usr/bin/env python3

import re

# Test the problematic pattern
pattern = r'\b\(\d{3}\)\s?\d{3}-\d{4}\b'
test_text = "(555) 123-4567"

print(f"Pattern: {pattern}")
print(f"Text: '{test_text}'")

# Test with re.finditer
matches = list(re.finditer(pattern, test_text, re.IGNORECASE))
print(f"Matches with \\b: {len(matches)}")

# Test without leading word boundary
pattern2 = r'\(\d{3}\)\s?\d{3}-\d{4}\b'
matches2 = list(re.finditer(pattern2, test_text, re.IGNORECASE))  
print(f"Matches without leading \\b: {len(matches2)}")

# Test in context
context_text = "Call me at (555) 123-4567 today"
matches3 = list(re.finditer(pattern, context_text, re.IGNORECASE))
matches4 = list(re.finditer(pattern2, context_text, re.IGNORECASE))
print(f"In context with \\b: {len(matches3)}")
print(f"In context without leading \\b: {len(matches4)}")

if matches4:
    print(f"Match found: '{matches4[0].group()}'")