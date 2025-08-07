#!/usr/bin/env python3

"""
Clean Rule IDs Test

Tests that rule IDs are clean and don't contain chunk prefixes like "chunk2_rule_name".
"""

import sys
import os
import json

# Add the parent directory to Python path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

def test_clean_rule_ids():
    """Test that rule IDs are clean and don't contain chunk prefixes"""
    print("[TEST] Testing Clean Rule IDs (No Chunk Prefixes)...")
    
    from Agents.AuditingAgent import AgentAuditing
    from Agents.LegacyRuleExtractionAndTranslatorAgent import LegacyRuleExtractionAgent
    
    # Create test agent
    audit_system = AgentAuditing("test_clean_rule_ids.jsonl")
    extraction_agent = LegacyRuleExtractionAgent(
        llm_client=None,  # We're testing deduplication logic, not LLM calls
        audit_system=audit_system,
        log_level=0
    )
    
    # Create mock rules with potential duplicate IDs (simulating multiple chunks)
    mock_rules = [
        {"rule_id": "loan_approval", "conditions": "score > 700", "actions": "approve"},
        {"rule_id": "credit_check", "conditions": "score > 650", "actions": "review"},
        {"rule_id": "loan_approval", "conditions": "score > 720", "actions": "fast_approve"},  # Duplicate
        {"rule_id": "risk_assessment", "conditions": "income > 50000", "actions": "assess"},
        {"rule_id": "credit_check", "conditions": "score > 680", "actions": "deep_review"},  # Duplicate
        {"rule_id": "loan_approval", "conditions": "score > 740", "actions": "instant_approve"}  # Another duplicate
    ]
    
    # Test deduplication
    deduplicated_rules = extraction_agent._deduplicate_rules(mock_rules, "test-request-123")
    
    # Check results
    rule_ids = [rule["rule_id"] for rule in deduplicated_rules]
    
    print(f"   Original rules: {len(mock_rules)}")
    print(f"   Deduplicated rules: {len(deduplicated_rules)}")
    print(f"   Rule IDs: {rule_ids}")
    
    # Assertions
    assert len(deduplicated_rules) == 6, f"Expected 6 rules, got {len(deduplicated_rules)}"
    assert len(set(rule_ids)) == 6, f"Expected all unique rule IDs, got duplicates: {rule_ids}"
    
    # Check for clean IDs (no chunk prefixes)
    for rule_id in rule_ids:
        assert not rule_id.startswith("chunk"), f"Rule ID '{rule_id}' contains chunk prefix"
        assert "chunk" not in rule_id.lower(), f"Rule ID '{rule_id}' contains 'chunk' text"
    
    # Check that duplicates got proper versioning
    expected_ids = {"loan_approval", "credit_check", "loan_approval_v2", "risk_assessment", "credit_check_v2", "loan_approval_v3"}
    actual_ids = set(rule_ids)
    assert actual_ids == expected_ids, f"Expected {expected_ids}, got {actual_ids}"
    
    print("   [PASS] All rule IDs are clean (no chunk prefixes)")
    print("   [PASS] Duplicate rule IDs properly versioned (_v2, _v3, etc.)")
    
    return {
        "original_count": len(mock_rules),
        "deduplicated_count": len(deduplicated_rules),
        "clean_ids": rule_ids
    }

def test_empty_and_edge_cases():
    """Test edge cases for rule deduplication"""
    print("[TEST] Testing Edge Cases for Rule Deduplication...")
    
    from Agents.AuditingAgent import AgentAuditing
    from Agents.LegacyRuleExtractionAndTranslatorAgent import LegacyRuleExtractionAgent
    
    audit_system = AgentAuditing("test_edge_cases.jsonl")
    extraction_agent = LegacyRuleExtractionAgent(
        llm_client=None,
        audit_system=audit_system,
        log_level=0
    )
    
    # Test empty list
    empty_result = extraction_agent._deduplicate_rules([], "test-request-empty")
    assert empty_result == [], "Empty list should remain empty"
    
    # Test single rule
    single_rule = [{"rule_id": "single_rule", "conditions": "test"}]
    single_result = extraction_agent._deduplicate_rules(single_rule, "test-request-single")
    assert len(single_result) == 1, "Single rule should remain single"
    assert single_result[0]["rule_id"] == "single_rule", "Single rule ID should remain unchanged"
    
    # Test rules without rule_id
    no_id_rules = [{"conditions": "test1"}, {"conditions": "test2"}]
    no_id_result = extraction_agent._deduplicate_rules(no_id_rules, "test-request-no-id")
    assert len(no_id_result) == 2, "Rules without IDs should be preserved"
    
    print("   [PASS] Empty list handling works correctly")
    print("   [PASS] Single rule handling works correctly")
    print("   [PASS] Rules without IDs handled gracefully")
    
    return True

def main():
    """Run all clean rule ID tests"""
    print("CLEAN RULE ID TEST")
    print("==================")
    print("Testing rule ID cleanliness and deduplication\n")
    
    try:
        # Test 1: Clean rule IDs
        clean_results = test_clean_rule_ids()
        
        # Test 2: Edge cases
        edge_results = test_empty_and_edge_cases()
        
        print("\n" + "=" * 50)
        print("CLEAN RULE ID TEST COMPLETE")
        print("=" * 50)
        print("[PASS] Rule IDs are clean (no chunk prefixes)")
        print("[PASS] Duplicate rule IDs properly handled")
        print("[PASS] Edge cases handled correctly")
        print("[PASS] Deduplication logic working as expected")
        
        print(f"\n[RESULTS] Clean rule IDs: {clean_results['clean_ids']}")
        print(f"[RESULTS] Deduplication: {clean_results['original_count']} -> {clean_results['deduplicated_count']} rules")
        
        print(f"\n[SUCCESS] Rule ID cleanup complete!")
        print("[SUCCESS] No chunk prefixes in rule identifiers")
        print("[SUCCESS] Intelligent deduplication with clean versioning")
        
    except Exception as e:
        print(f"\n[FAIL] Clean rule ID test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()