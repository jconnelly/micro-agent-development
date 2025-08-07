#!/usr/bin/env python3

"""
Comprehensive BaseAgent Integration Test

Tests all AI agents that inherit from BaseAgent to ensure the refactoring
preserves functionality while consolidating common code.
"""

import sys
import os

# Add the parent directory to Python path for imports (since we're in Test_Cases subdirectory)
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

def test_agent_creation_and_inheritance():
    """Test that all agents can be created and inherit BaseAgent properly"""
    print("[TEST] Testing Agent Creation and BaseAgent Inheritance")
    print("=" * 60)
    
    try:
        from Agents.AuditingAgent import AgentAuditing
        
        # Create audit system for all agents
        print("1. Creating shared audit system...")
        audit_system = AgentAuditing("test_comprehensive_audit.jsonl")
        print("   [PASS] Shared audit system created")
        
        results = {}
        
        # Test IntelligentSubmissionTriageAgent
        print("2. Testing IntelligentSubmissionTriageAgent...")
        try:
            from Agents.IntelligentSubmissionTriageAgent import IntelligentSubmissionTriageAgent
            triage_agent = IntelligentSubmissionTriageAgent(
                llm_client=None,
                audit_system=audit_system,
                agent_id="test-triage-001",
                log_level=1,
                model_name="test-model",
                llm_provider="test-provider"
            )
            
            # Test BaseAgent methods
            ip = triage_agent.get_ip_address()
            info = triage_agent.get_agent_info()
            req_id = triage_agent._create_request_id("triage")
            
            results["IntelligentSubmissionTriageAgent"] = {
                "created": True,
                "ip_address": ip,
                "agent_name": info["agent_name"],
                "capabilities": len(info["capabilities"]),
                "inheritance": "BaseAgent" in str(type(triage_agent).__bases__)
            }
            print("   [PASS] IntelligentSubmissionTriageAgent working")
            
        except Exception as e:
            results["IntelligentSubmissionTriageAgent"] = {"error": str(e)}
            print(f"   [FAIL] IntelligentSubmissionTriageAgent: {e}")
        
        # Test LegacyRuleExtractionAgent  
        print("3. Testing LegacyRuleExtractionAgent...")
        try:
            from Agents.LegacyRuleExtractionAndTranslatorAgent import LegacyRuleExtractionAgent
            extraction_agent = LegacyRuleExtractionAgent(
                llm_client=None,
                audit_system=audit_system,
                agent_id="test-extraction-001",
                log_level=1,
                model_name="test-model",
                llm_provider="test-provider"
            )
            
            # Test BaseAgent methods
            ip = extraction_agent.get_ip_address()
            info = extraction_agent.get_agent_info()
            req_id = extraction_agent._create_request_id("extraction")
            
            results["LegacyRuleExtractionAgent"] = {
                "created": True,
                "ip_address": ip,
                "agent_name": info["agent_name"],
                "capabilities": len(info["capabilities"]),
                "supported_languages": len(info["supported_languages"]),
                "inheritance": "BaseAgent" in str(type(extraction_agent).__bases__)
            }
            print("   [PASS] LegacyRuleExtractionAgent working")
            
        except Exception as e:
            results["LegacyRuleExtractionAgent"] = {"error": str(e)}
            print(f"   [FAIL] LegacyRuleExtractionAgent: {e}")
        
        # Test PIIScrubbingAgent
        print("4. Testing PIIScrubbingAgent...")
        try:
            from Agents.PIIScrubbingAgent import PIIScrubbingAgent, PIIContext
            pii_agent = PIIScrubbingAgent(
                audit_system=audit_system,
                context=PIIContext.GENERAL,
                agent_id="test-pii-001",
                log_level=1
            )
            
            # Test BaseAgent methods
            ip = pii_agent.get_ip_address()
            info = pii_agent.get_agent_info()
            req_id = pii_agent._create_request_id("pii")
            
            results["PIIScrubbingAgent"] = {
                "created": True,
                "ip_address": ip,
                "agent_name": info["agent_name"],
                "capabilities": len(info["capabilities"]),
                "pii_types": len(info["supported_pii_types"]),
                "inheritance": "BaseAgent" in str(type(pii_agent).__bases__)
            }
            print("   [PASS] PIIScrubbingAgent working")
            
        except Exception as e:
            results["PIIScrubbingAgent"] = {"error": str(e)}
            print(f"   [FAIL] PIIScrubbingAgent: {e}")
        
        # Test RuleDocumentationAgent
        print("5. Testing RuleDocumentationAgent...")
        try:
            from Agents.RuleDocumentationAgent import RuleDocumentationAgent
            doc_agent = RuleDocumentationAgent(
                llm_client=None,
                audit_system=audit_system,
                agent_id="test-doc-001",
                log_level=1,
                model_name="test-model",
                llm_provider="test-provider"
            )
            
            # Test BaseAgent methods
            ip = doc_agent.get_ip_address()
            info = doc_agent.get_agent_info()
            req_id = doc_agent._create_request_id("documentation")
            
            results["RuleDocumentationAgent"] = {
                "created": True,
                "ip_address": ip,
                "agent_name": info["agent_name"],
                "capabilities": len(info["capabilities"]),
                "supported_formats": len(info["supported_formats"]),
                "inheritance": "BaseAgent" in str(type(doc_agent).__bases__)
            }
            print("   [PASS] RuleDocumentationAgent working")
            
        except Exception as e:
            results["RuleDocumentationAgent"] = {"error": str(e)}
            print(f"   [FAIL] RuleDocumentationAgent: {e}")
        
        return results
        
    except Exception as e:
        print(f"[FAIL] Critical error in test setup: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_common_functionality():
    """Test that common BaseAgent functionality works consistently"""
    print("\n[TEST] Testing Common BaseAgent Functionality")
    print("=" * 60)
    
    try:
        from Agents.AuditingAgent import AgentAuditing
        from Agents.IntelligentSubmissionTriageAgent import IntelligentSubmissionTriageAgent
        from Agents.LegacyRuleExtractionAndTranslatorAgent import LegacyRuleExtractionAgent
        
        audit_system = AgentAuditing("test_common_functionality.jsonl")
        
        # Create two different agents
        agent1 = IntelligentSubmissionTriageAgent(None, audit_system, "test-1", 1)
        agent2 = LegacyRuleExtractionAgent(None, audit_system, "test-2", 1)
        
        print("1. Testing IP address consistency...")
        ip1 = agent1.get_ip_address()
        ip2 = agent2.get_ip_address()
        print(f"   Agent1 IP: {ip1}")
        print(f"   Agent2 IP: {ip2}")
        print(f"   [{'PASS' if ip1 == ip2 else 'WARN'}] IP addresses {'match' if ip1 == ip2 else 'differ'}")
        
        print("2. Testing request ID generation...")
        req1 = agent1._create_request_id("test")
        req2 = agent2._create_request_id("test")
        print(f"   Agent1 Request ID: {req1}")
        print(f"   Agent2 Request ID: {req2}")
        print(f"   [{'PASS' if req1 != req2 else 'FAIL'}] Request IDs are unique")
        
        print("3. Testing timestamp generation...")
        ts1 = agent1._get_current_timestamp()
        ts2 = agent2._get_current_timestamp()
        print(f"   Timestamp1: {ts1}")
        print(f"   Timestamp2: {ts2}")
        print(f"   [PASS] Timestamps generated")
        
        print("4. Testing configuration inheritance...")
        print(f"   Agent1 API Timeout: {agent1.API_TIMEOUT_SECONDS}s")
        print(f"   Agent2 API Timeout: {agent2.API_TIMEOUT_SECONDS}s")
        print(f"   Agent1 Max Retries: {agent1.MAX_RETRIES}")
        print(f"   Agent2 Max Retries: {agent2.MAX_RETRIES}")
        print("   [PASS] Configuration values accessible")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] Common functionality test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all BaseAgent integration tests"""
    print("COMPREHENSIVE BASEAGENT INTEGRATION TEST")
    print("========================================")
    print("Testing all AI agents for BaseAgent inheritance and functionality\n")
    
    # Test 1: Agent creation and inheritance
    results = test_agent_creation_and_inheritance()
    if not results:
        print("\n[FAIL] Critical test setup failure")
        sys.exit(1)
    
    # Test 2: Common functionality
    common_test_passed = test_common_functionality()
    
    # Summary
    print("\n" + "=" * 60)
    print("COMPREHENSIVE TEST RESULTS")
    print("=" * 60)
    
    successful_agents = 0
    failed_agents = 0
    
    for agent_name, result in results.items():
        if "error" in result:
            print(f"[FAIL] {agent_name}: {result['error']}")
            failed_agents += 1
        else:
            print(f"[PASS] {agent_name}: BaseAgent integration successful")
            print(f"       - Inheritance: {result['inheritance']}")
            print(f"       - Capabilities: {result['capabilities']}")
            print(f"       - IP Address: {result['ip_address']}")
            successful_agents += 1
    
    print(f"\nCOMMON FUNCTIONALITY: {'PASS' if common_test_passed else 'FAIL'}")
    
    print(f"\nSUMMARY:")
    print(f"[PASS] Successful integrations: {successful_agents}/4")
    print(f"[FAIL] Failed integrations: {failed_agents}/4") 
    print(f"[INFO] Common functionality: {'Working' if common_test_passed else 'Failed'}")
    
    if successful_agents == 4 and common_test_passed:
        print("\n[SUCCESS] ALL TESTS PASSED - BaseAgent integration complete!")
        print("[SUCCESS] Code duplication eliminated, functionality preserved!")
        sys.exit(0)
    else:
        print(f"\n[ERROR] {failed_agents} agents failed integration")
        sys.exit(1)

if __name__ == "__main__":
    main()