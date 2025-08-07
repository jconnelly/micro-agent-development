#!/usr/bin/env python3

"""
Debug phone pattern detection
"""

import sys
import os
import re

# Add the parent directory to Python path for imports (since we're in Test_Cases subdirectory)
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

def test_phone_patterns():
    """Test phone pattern detection"""
    from Agents.AuditingAgent import AgentAuditing  
    from Agents.PIIScrubbingAgent import PIIScrubbingAgent, PIIContext, PIIType
    
    # Create test agent
    audit_system = AgentAuditing("debug_phone.jsonl")
    pii_agent = PIIScrubbingAgent(
        audit_system=audit_system,
        context=PIIContext.GENERAL,
        log_level=1
    )
    
    # Test specific phone pattern
    test_text = "(555) 123-4567"
    
    print(f"Testing: '{test_text}'")
    print("\nCompiled phone patterns:")
    for compiled_pattern, original_pattern in pii_agent.compiled_patterns.get(PIIType.PHONE_NUMBER, []):
        print(f"  Pattern: {original_pattern}")
        matches = list(compiled_pattern.finditer(test_text))
        print(f"  Matches: {len(matches)}")
        for match in matches:
            print(f"    - '{match.group()}' at {match.start()}-{match.end()}")
    
    # Test detection
    result = pii_agent._detect_pii(test_text)
    print(f"\nDetection result:")
    print(f"  Detected types: {[t.value for t in result['detected_types']]}")
    print(f"  Matches: {result['matches']}")

if __name__ == "__main__":
    test_phone_patterns()