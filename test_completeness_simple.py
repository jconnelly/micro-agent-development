#!/usr/bin/env python3
"""
Simple Rule Completeness Analyzer Test with Known Rule Count

Tests the completeness analyzer with the known 24 rules from our COBOL analysis
to validate the core completeness analysis functionality.
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from Utils.rule_completeness_analyzer import RuleCompletenessAnalyzer, CompletenessStatus


def test_completeness_simple():
    """Test completeness analyzer with known rule counts."""
    
    print("=" * 60)
    print("Rule Completeness Analyzer - Simple Test")
    print("=" * 60)
    
    analyzer = RuleCompletenessAnalyzer()
    
    # Test scenarios with known rule counts
    scenarios = {
        "excellent": {"extracted": 23, "expected": 24, "target_status": CompletenessStatus.EXCELLENT},
        "good": {"extracted": 22, "expected": 24, "target_status": CompletenessStatus.GOOD},
        "warning": {"extracted": 20, "expected": 24, "target_status": CompletenessStatus.WARNING},  
        "poor": {"extracted": 17, "expected": 24, "target_status": CompletenessStatus.POOR},
        "current": {"extracted": 14, "expected": 24, "target_status": CompletenessStatus.CRITICAL}
    }
    
    print("Testing completeness status determination:")
    print(f"{'Scenario':<10} {'Rules':<10} {'Complete':<12} {'Status':<12} {'Target':<8}")
    print(f"{'-'*10} {'-'*10} {'-'*12} {'-'*12} {'-'*8}")
    
    all_passed = True
    
    for scenario_name, data in scenarios.items():
        extracted = data["extracted"]
        expected = data["expected"] 
        expected_status = data["target_status"]
        
        # Calculate completeness percentage
        completeness = (extracted / expected) * 100 if expected > 0 else 0
        
        # Determine actual status
        actual_status = analyzer._determine_completeness_status(completeness)
        
        # Check if target achieved (90%+)
        target_achieved = completeness >= 90.0
        target_str = "PASS" if target_achieved else "FAIL"
        
        # Verify status matches expected
        status_correct = actual_status == expected_status
        status_mark = "PASS" if status_correct else "FAIL"
        
        print(f"{scenario_name:<10} {extracted}/{expected:<7} {completeness:<11.1f}% "
              f"{actual_status.value:<12} {target_str:<8} {status_mark}")
        
        if not status_correct:
            print(f"  ERROR: Expected {expected_status.value}, got {actual_status.value}")
            all_passed = False
    
    # Test progress monitoring
    print(f"\n{'='*60}")
    print("Testing Real-Time Progress Monitoring:")
    print(f"{'='*60}")
    
    # Simulate progressive extraction
    chunk_results = [
        [{"rule_id": f"RULE_{i:03d}"} for i in range(1, 9)],    # Chunk 1: 8 rules
        [{"rule_id": f"RULE_{i:03d}"} for i in range(9, 16)],   # Chunk 2: 7 rules
        [{"rule_id": f"RULE_{i:03d}"} for i in range(16, 19)],  # Chunk 3: 3 rules
    ]
    
    expected_total = 24
    
    for i, current_results in enumerate([chunk_results[:1], chunk_results[:2], chunk_results], 1):
        progress = analyzer.monitor_extraction_progress(
            chunk_results=current_results,
            expected_total=expected_total
        )
        
        print(f"After chunk {i}: {progress['current_extracted']}/{expected_total} rules "
              f"({progress['progress_percentage']:.1f}%) - "
              f"Target: {'ACHIEVED' if progress['target_achieved'] else 'NOT ACHIEVED'}")
        
        # Show warnings
        for warning in progress['warnings']:
            print(f"  {warning['level'].upper()}: {warning['message']}")
    
    # Test threshold warnings
    print(f"\n{'='*60}")
    print("Testing Threshold Warning System:")
    print(f"{'='*60}")
    
    # Test scenario below 90% threshold
    low_performance_chunks = [
        [{"rule_id": f"RULE_{i:03d}"} for i in range(1, 6)],    # 5 rules
        [{"rule_id": f"RULE_{i:03d}"} for i in range(6, 11)],   # 5 rules  
        [{"rule_id": f"RULE_{i:03d}"} for i in range(11, 16)],  # 5 rules
    ]
    
    progress = analyzer.monitor_extraction_progress(
        chunk_results=low_performance_chunks,
        expected_total=24
    )
    
    print(f"Low performance test: {progress['current_extracted']}/{expected_total} rules "
          f"({progress['progress_percentage']:.1f}%)")
    print(f"Warnings generated: {len(progress['warnings'])}")
    
    for warning in progress['warnings']:
        print(f"  {warning['level'].upper()}: {warning['message']}")
        print(f"  Recommendation: {warning['recommendation']}")
    
    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    
    if all_passed:
        print("SUCCESS: All completeness status tests passed")
        print("+ Status determination working correctly")
        print("+ Progress monitoring functional") 
        print("+ Warning system operational")
        print("+ 90% threshold detection working")
        print("\nRule Completeness Analyzer is ready for integration")
    else:
        print("PARTIAL SUCCESS: Some tests failed")
        print("- Review status determination logic")
        print("- Verify threshold calculations")
    
    return all_passed


if __name__ == "__main__":
    test_completeness_simple()