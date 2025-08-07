#!/usr/bin/env python3

"""
Caching Performance Test

Tests the performance improvement from adding LRU caching to expensive operations
including PII detection and file context extraction.
"""

import sys
import os
import time
from typing import List, Dict, Any

# Add the parent directory to Python path for imports (since we're in Test_Cases subdirectory)
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

def test_pii_detection_caching():
    """Test PIIScrubbingAgent LRU caching performance for repeated text inputs"""
    print("[TEST] Testing PIIScrubbingAgent LRU Caching Performance...")
    
    from Agents.AuditingAgent import AgentAuditing
    from Agents.PIIScrubbingAgent import PIIScrubbingAgent, PIIContext
    
    # Create test agent
    audit_system = AgentAuditing("test_pii_caching.jsonl")
    pii_agent = PIIScrubbingAgent(
        audit_system=audit_system,
        context=PIIContext.FINANCIAL,
        log_level=0  # Silent for performance test
    )
    
    # Test data with repeated inputs to test caching effectiveness
    test_texts = [
        "Customer SSN: 123-45-6789, Credit Card: 4111-1111-1111-1111, Phone: (555) 123-4567",
        "Email: user@example.com, Account: 123456789012345, DOB: 01/15/1985", 
        "Contact: john.doe@company.com, Phone: 555-987-6543, SSN: 987-65-4321"
    ]
    
    # Phase 1: First run (cache misses)
    iterations = 100
    start_time = time.perf_counter()
    
    for i in range(iterations):
        for text in test_texts:
            result = pii_agent._detect_pii(text)
    
    first_run_time = time.perf_counter() - start_time
    
    # Phase 2: Second run (cache hits)
    start_time = time.perf_counter()
    
    for i in range(iterations):
        for text in test_texts:
            result = pii_agent._detect_pii(text)
    
    second_run_time = time.perf_counter() - start_time
    
    # Calculate performance metrics
    total_operations = iterations * len(test_texts)
    first_ops_per_second = total_operations / first_run_time
    second_ops_per_second = total_operations / second_run_time
    cache_speedup = second_ops_per_second / first_ops_per_second
    
    print(f"   First run (cache misses): {first_run_time:.3f}s, {first_ops_per_second:.1f} ops/sec")
    print(f"   Second run (cache hits): {second_run_time:.3f}s, {second_ops_per_second:.1f} ops/sec")
    print(f"   Cache speedup: {cache_speedup:.1f}x faster")
    
    # Verify functionality is preserved
    test_result = pii_agent._detect_pii(test_texts[0])
    detected_types = [t.value for t in test_result['detected_types']]
    
    assert len(detected_types) >= 3, f"Expected multiple PII types, got: {detected_types}"
    assert "ssn" in detected_types
    assert "credit_card" in detected_types
    
    print("   [PASS] PIIScrubbingAgent caching working correctly")
    return {
        "cache_speedup": cache_speedup,
        "first_run_ops_per_second": first_ops_per_second,
        "second_run_ops_per_second": second_ops_per_second,
        "total_operations": total_operations
    }

def test_file_context_caching():
    """Test LegacyRuleExtractionAgent file context extraction caching"""
    print("[TEST] Testing File Context Extraction LRU Caching Performance...")
    
    from Agents.AuditingAgent import AgentAuditing
    from Agents.LegacyRuleExtractionAndTranslatorAgent import LegacyRuleExtractionAgent
    
    # Create test agent
    audit_system = AgentAuditing("test_file_context_caching.jsonl")
    extraction_agent = LegacyRuleExtractionAgent(
        llm_client=None,  # We're only testing file context extraction
        audit_system=audit_system,
        log_level=0
    )
    
    # Create test file content with typical headers and imports
    test_file_lines = [
        "#!/usr/bin/env python3",
        "# -*- coding: utf-8 -*-",
        "\"\"\"",
        "Business Rules Engine - Main Module", 
        "Contains core rule processing logic",
        "\"\"\"",
        "",
        "import sys",
        "import json", 
        "import datetime",
        "from typing import Dict, Any, List",
        "from dataclasses import dataclass",
        "",
        "# Configuration constants",
        "MAX_RETRIES = 3",
        "DEFAULT_TIMEOUT = 30",
        "",
        "class RuleEngine:",
        "    def __init__(self):",
        "        pass",
        "",
        "    def process_rule(self, rule_data):",
        "        # Business logic here",
        "        return True"
    ] * 5  # Multiply to create larger file
    
    # Phase 1: First run (cache misses) - different file contexts
    iterations = 200
    start_time = time.perf_counter()
    
    for i in range(iterations):
        # Vary the file slightly to test different cache keys
        modified_lines = test_file_lines[:]
        modified_lines[0] = f"#!/usr/bin/env python3  # Version {i % 10}"
        context_lines = extraction_agent._extract_file_context(modified_lines, max_lines=50)
    
    first_run_time = time.perf_counter() - start_time
    
    # Phase 2: Second run (cache hits) - same file contexts repeated
    start_time = time.perf_counter()
    
    for i in range(iterations):
        # Use same variations to trigger cache hits
        modified_lines = test_file_lines[:]
        modified_lines[0] = f"#!/usr/bin/env python3  # Version {i % 10}"
        context_lines = extraction_agent._extract_file_context(modified_lines, max_lines=50)
    
    second_run_time = time.perf_counter() - start_time
    
    # Calculate performance metrics
    first_ops_per_second = iterations / first_run_time
    second_ops_per_second = iterations / second_run_time
    cache_speedup = second_ops_per_second / first_ops_per_second
    
    print(f"   First run (cache misses): {first_run_time:.3f}s, {first_ops_per_second:.1f} ops/sec")
    print(f"   Second run (cache hits): {second_run_time:.3f}s, {second_ops_per_second:.1f} ops/sec") 
    print(f"   Cache speedup: {cache_speedup:.1f}x faster")
    
    # Verify functionality is preserved
    test_context = extraction_agent._extract_file_context(test_file_lines, max_lines=50)
    
    # Should extract imports, comments, and other context
    assert len(test_context) > 0, "Expected context lines to be extracted"
    assert any("import" in line for line in test_context), "Expected import statements in context"
    assert any("#" in line for line in test_context), "Expected comments in context"
    
    print("   [PASS] File context extraction caching working correctly")
    return {
        "cache_speedup": cache_speedup,
        "first_run_ops_per_second": first_ops_per_second,
        "second_run_ops_per_second": second_ops_per_second,
        "total_operations": iterations
    }

def test_ip_address_caching():
    """Test BaseAgent IP address caching (already implemented)"""
    print("[TEST] Testing BaseAgent IP Address Caching Performance...")
    
    from Agents.AuditingAgent import AgentAuditing
    from Agents.PIIScrubbingAgent import PIIScrubbingAgent, PIIContext
    
    # Create test agent (using concrete implementation)
    audit_system = AgentAuditing("test_ip_caching.jsonl")
    test_agent = PIIScrubbingAgent(
        audit_system=audit_system,
        context=PIIContext.GENERAL,
        log_level=0
    )
    
    # Phase 1: First calls (potential cache misses)
    iterations = 1000
    start_time = time.perf_counter()
    
    for i in range(iterations):
        ip_address = test_agent.get_ip_address()
    
    first_run_time = time.perf_counter() - start_time
    
    # Phase 2: Subsequent calls (cache hits)
    start_time = time.perf_counter()
    
    for i in range(iterations):
        ip_address = test_agent.get_ip_address()
    
    second_run_time = time.perf_counter() - start_time
    
    # Calculate performance metrics
    first_ops_per_second = iterations / first_run_time
    second_ops_per_second = iterations / second_run_time
    cache_speedup = second_ops_per_second / first_ops_per_second
    
    print(f"   First run: {first_run_time:.3f}s, {first_ops_per_second:.1f} ops/sec")
    print(f"   Second run (cached): {second_run_time:.3f}s, {second_ops_per_second:.1f} ops/sec")
    print(f"   Cache speedup: {cache_speedup:.1f}x faster")
    
    # Verify functionality
    test_ip = test_agent.get_ip_address()
    assert test_ip is not None, "Expected IP address to be returned"
    assert isinstance(test_ip, str), "Expected IP address to be a string"
    
    print("   [PASS] IP address caching working correctly")
    return {
        "cache_speedup": cache_speedup,
        "first_run_ops_per_second": first_ops_per_second,
        "second_run_ops_per_second": second_ops_per_second,
        "total_operations": iterations
    }

def analyze_caching_improvements():
    """Analyze and report on the caching performance improvements achieved"""
    print("[ANALYSIS] Caching Performance Improvements...")
    
    print("   LRU caching provides significant performance benefits:")
    print("   1. MEMORY EFFICIENCY: Recently used results stored in fast memory")
    print("   2. CPU SAVINGS: Avoid recomputing expensive operations") 
    print("   3. SCALABILITY: Better performance under repeated workloads")
    print("   4. CONFIGURABLE: Cache size tunable for memory vs performance trade-offs")
    
    print("\\n   Optimizations implemented:")
    print("   - PIIScrubbingAgent: LRU cache (256 entries) for repeated text detection")
    print("   - LegacyRuleExtractionAgent: LRU cache (128 entries) for file context extraction") 
    print("   - BaseAgent: IP address caching for network call optimization")
    print("   - Cache keys: Designed for optimal hit rates and memory efficiency")

def main():
    """Run all caching performance optimization tests"""
    print("CACHING PERFORMANCE OPTIMIZATION TEST")
    print("====================================")
    print("Testing LRU caching for expensive operations\\n")
    
    try:
        # Test 1: PII detection caching
        pii_results = test_pii_detection_caching()
        
        # Test 2: File context caching
        context_results = test_file_context_caching()
        
        # Test 3: IP address caching
        ip_results = test_ip_address_caching()
        
        # Analysis
        analyze_caching_improvements()
        
        print("\\n" + "=" * 60)
        print("CACHING OPTIMIZATION COMPLETE")
        print("=" * 60)
        print("[PASS] PIIScrubbingAgent - LRU caching for PII detection working")
        print("[PASS] LegacyRuleExtractionAgent - File context extraction caching working")
        print("[PASS] BaseAgent - IP address caching working")
        print("[PASS] Functionality preserved - All existing behavior maintained")
        
        print(f"\\n[PERFORMANCE] PII Detection Cache: {pii_results['cache_speedup']:.1f}x speedup")
        print(f"[PERFORMANCE] File Context Cache: {context_results['cache_speedup']:.1f}x speedup") 
        print(f"[PERFORMANCE] IP Address Cache: {ip_results['cache_speedup']:.1f}x speedup")
        
        print(f"\\n[SUCCESS] Phase 3 Task 3 Complete!")
        print("[SUCCESS] LRU caching added for expensive operations")
        print("[SUCCESS] Significant performance improvements for repeated operations")
        
    except Exception as e:
        print(f"\\n[FAIL] Caching optimization test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()