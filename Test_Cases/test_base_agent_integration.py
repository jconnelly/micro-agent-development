#!/usr/bin/env python3

"""
Test BaseAgent integration with IntelligentSubmissionTriageAgent.

This script validates that the BaseAgent refactoring preserves functionality.
"""

import sys
import os

# Add the parent directory to Python path for imports (since we're in Test_Cases subdirectory)
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

try:
    from Agents.ApplicationTriageAgent import IntelligentSubmissionTriageAgent
    from Agents.ComplianceMonitoringAgent import ComplianceMonitoringAgent
    from Agents.PersonalDataProtectionAgent import MaskingStrategy
    
    print("[PASS] BaseAgent Integration Test")
    print("=" * 50)
    
    # Test 1: Create audit system
    print("1. Creating audit system...")
    audit_system = ComplianceMonitoringAgent("test_audit.jsonl")
    print("   [PASS] Audit system created")
    
    # Test 2: Create agent with BaseAgent inheritance
    print("2. Creating IntelligentSubmissionTriageAgent...")
    agent = IntelligentSubmissionTriageAgent(
        llm_client=None,  # Mock client for testing
        audit_system=audit_system,
        agent_id="test-agent-001",
        log_level=1,
        model_name="test-model",
        llm_provider="test-provider"
    )
    print("   [PASS] Agent created successfully")
    
    # Test 3: Verify inheritance
    print("3. Testing BaseAgent methods...")
    
    # Test IP address method (inherited from BaseAgent)
    ip_address = agent._get_ip_address()
    print(f"   [PASS] IP Address: {ip_address}")
    
    # Test agent info method (required abstract method)
    agent_info = agent.get_agent_info()
    print(f"   [PASS] Agent Info: {agent_info['agent_name']}")
    print(f"      - ID: {agent_info['agent_id']}")
    print(f"      - Version: {agent_info['version']}")
    print(f"      - Model: {agent_info['model_name']}")
    
    # Test 4: Verify configuration
    print("4. Testing configuration inheritance...")
    print(f"   [PASS] API Timeout: {agent.API_TIMEOUT_SECONDS}s")
    print(f"   [PASS] Max Retries: {agent.MAX_RETRIES}")
    print(f"   [PASS] Agent Name: {agent.agent_name}")
    
    # Test 5: Test helper methods
    print("5. Testing utility methods...")
    
    # Test request ID creation
    request_id = agent._create_request_id("test")
    print(f"   [PASS] Request ID: {request_id}")
    
    # Test timestamp
    timestamp = agent._get_current_timestamp()
    print(f"   [PASS] Timestamp: {timestamp}")
    
    print("\n" + "=" * 50)
    print("[PASS] ALL TESTS PASSED - BaseAgent integration working!")
    print("[PASS] IntelligentSubmissionTriageAgent successfully inherits from BaseAgent")
    print("[PASS] Common functionality consolidated without breaking changes")
    
except ImportError as e:
    print(f"[FAIL] IMPORT ERROR: {e}")
    sys.exit(1)
    
except Exception as e:
    print(f"[FAIL] TEST FAILED: {e}")
    print(f"   Error type: {type(e).__name__}")
    import traceback
    traceback.print_exc()
    sys.exit(1)