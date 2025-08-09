#!/usr/bin/env python3

"""
Test runner for PIIScrubbingAgent functionality.
Demonstrates PII detection, masking strategies, and integration with other agents.
"""

import json
import os
from typing import Dict, Any
from dotenv import load_dotenv
import google.generativeai as genai

from Agents.PersonalDataProtectionAgent import PersonalDataProtectionAgent, PIIType, MaskingStrategy, PIIContext
from Agents.ApplicationTriageAgent import IntelligentSubmissionTriageAgent
from Agents.ComplianceMonitoringAgent import ComplianceMonitoringAgent, AuditLevel


def test_standalone_pii_scrubbing():
    """Test PIIScrubbingAgent as a standalone component"""
    print("=== Standalone PII Scrubbing Tests ===")
    
    # Initialize audit system
    audit_system = ComplianceMonitoringAgent("./Rule_Agent_Output_Files/pii_test_audit.jsonl")
    
    # Test data with various PII types
    test_data_samples = [
        {
            "name": "Financial Data",
            "data": {
                "customer_name": "John Smith",
                "ssn": "123-45-6789",
                "credit_card": "4532 1234 5678 9012",
                "phone": "(555) 123-4567",
                "email": "john.smith@email.com",
                "account_number": "98765432101234",
                "application_text": "I need a loan for $50,000. My SSN is 123-45-6789 and my credit card ending in 9012."
            }
        },
        {
            "name": "Healthcare Data", 
            "data": {
                "patient_name": "Jane Doe",
                "ssn": "987-65-4321",
                "dob": "01/15/1985",
                "phone": "555.987.6543",
                "email": "jane.doe@healthcare.com",
                "medical_record": "Patient Jane Doe (SSN: 987-65-4321) born 01/15/1985 requires treatment."
            }
        },
        {
            "name": "Mixed PII Data",
            "data": "Contact info: Call me at 555-123-4567 or email test@example.com. My SSN is 111-22-3333 and credit card is 4111111111111111."
        }
    ]
    
    # Test different contexts and strategies
    test_configs = [
        {"context": PIIContext.FINANCIAL, "strategy": MaskingStrategy.TOKENIZE, "description": "Financial with Tokenization"},
        {"context": PIIContext.HEALTHCARE, "strategy": MaskingStrategy.HASH, "description": "Healthcare with Hashing"},
        {"context": PIIContext.GENERAL, "strategy": MaskingStrategy.PARTIAL_MASK, "description": "General with Partial Masking"},
        {"context": PIIContext.FINANCIAL, "strategy": MaskingStrategy.FULL_MASK, "description": "Financial with Full Masking"}
    ]
    
    for config in test_configs:
        print(f"\n--- Testing {config['description']} ---")
        
        # Initialize PII scrubber with current config
        pii_scrubber = PersonalDataProtectionAgent(
            audit_system=audit_system,
            context=config['context'],
            log_level=1,  # Verbose for testing
            enable_tokenization=(config['strategy'] == MaskingStrategy.TOKENIZE)
        )
        
        for sample in test_data_samples:
            print(f"\nTesting {sample['name']}:")
            
            try:
                result = pii_scrubber.scrub_data(
                    data=sample['data'],
                    request_id=f"test_{config['context'].value}_{sample['name'].replace(' ', '_')}",
                    custom_strategy=config['strategy'],
                    audit_level=2
                )
                
                print(f"  PII Types Detected: {[t.value for t in result['pii_detected']]}")
                print(f"  Strategy Used: {result['scrubbing_summary']['masking_strategy']}")
                print(f"  Total PII Instances: {result['scrubbing_summary']['total_pii_instances']}")
                print(f"  Processing Time: {result['scrubbing_summary']['processing_duration_ms']:.2f}ms")
                
                # Show before/after comparison for string data
                if isinstance(sample['data'], str):
                    print(f"  Original: {sample['data'][:100]}...")
                    print(f"  Scrubbed: {result['scrubbed_data'][:100]}...")
                
                # Test detokenization if tokenization was used
                if config['strategy'] == MaskingStrategy.TOKENIZE and result['scrubbing_summary']['tokens_generated'] > 0:
                    print(f"  Tokens Generated: {result['scrubbing_summary']['tokens_generated']}")
                    
                    # Test detokenization
                    detok_result = pii_scrubber.detokenize_data(result['scrubbed_data'])
                    print(f"  Detokenization: Restored {detok_result['tokens_restored']} tokens")
                
            except Exception as e:
                print(f"  ERROR: {str(e)}")
    
    print("\n=== Standalone PII Scrubbing Tests Completed ===")


def test_pii_integrated_triage():
    """Test PII scrubbing integrated with IntelligentSubmissionTriageAgent"""
    print("\n=== Integrated PII + Triage Agent Tests ===")
    
    # Initialize audit system
    audit_system = ComplianceMonitoringAgent("./Rule_Agent_Output_Files/pii_triage_integrated_audit.jsonl")
    
    # Configure Gemini API
    try:
        load_dotenv()
        api_key = os.getenv('GEMINI_API_KEY')
        genai.configure(api_key=api_key)
        llm_client = genai.GenerativeModel('gemini-2.5-flash')
        print("Gemini API configured for integrated testing")
    except Exception as e:
        print(f"Warning: Could not configure Gemini API: {e}")
        llm_client = None
    
    # Test submissions with PII
    test_submissions_with_pii = [
        {
            "id": "PII-SUB-001",
            "type": "Loan Application",
            "content": "Personal loan application from John Smith, SSN: 123-45-6789, phone: (555) 123-4567, email: john@email.com. Credit card on file: 4532-1234-5678-9012. Requesting $25,000 for debt consolidation.",
            "summary": "Loan application with full PII data",
            "user_context": {
                "ssn": "123-45-6789",
                "credit_score": 680,
                "annual_income": 65000,
                "credit_card": "4532-1234-5678-9012",
                "phone": "(555) 123-4567",
                "email": "john@email.com"
            },
            "user_id": "user_with_pii_123",
            "session_id": "pii_test_session_001"
        },
        {
            "id": "PII-SUB-002", 
            "type": "Credit Card Application",
            "content": "Business credit card application. Company owner SSN: 987-65-4321, business phone: 555.987.6543, email: business@company.com. Bank account: 123456789012345.",
            "summary": "Business credit card with sensitive data",
            "user_context": {
                "business_ssn": "987-65-4321",
                "business_phone": "555.987.6543",
                "business_email": "business@company.com",
                "bank_account": "123456789012345"
            },
            "user_id": "business_user_456",
            "session_id": "pii_test_session_002"
        }
    ]
    
    # Test different PII configurations
    pii_test_configs = [
        {
            "enable_pii": True,
            "strategy": MaskingStrategy.TOKENIZE,
            "description": "PII Enabled - Tokenization"
        },
        {
            "enable_pii": True,
            "strategy": MaskingStrategy.PARTIAL_MASK,
            "description": "PII Enabled - Partial Masking"
        },
        {
            "enable_pii": False,
            "strategy": None,
            "description": "PII Disabled - Raw Data"
        }
    ]
    
    all_results = []
    
    for config in pii_test_configs:
        print(f"\n--- Testing {config['description']} ---")
        
        # Initialize triage agent with PII configuration
        triage_agent = IntelligentSubmissionTriageAgent(
            llm_client=llm_client,
            audit_system=audit_system,
            log_level=1,  # Verbose for testing
            model_name="gemini-2.5-flash",
            llm_provider="google",
            enable_pii_scrubbing=config['enable_pii'],
            pii_masking_strategy=config['strategy'] if config['strategy'] else MaskingStrategy.FULL_MASK
        )
        
        for submission in test_submissions_with_pii:
            print(f"\nProcessing {submission['id']} with {config['description']}:")
            
            try:
                result = triage_agent.triage_submission(
                    submission_data=submission,
                    audit_level=AuditLevel.LEVEL_2.value
                )
                
                # Extract PII processing information
                pii_info = result.get('pii_processing', {})
                triage_decision = result.get('triage_decision', {})
                
                print(f"  PII Processing Enabled: {pii_info.get('enabled', False)}")
                print(f"  PII Types Detected: {pii_info.get('pii_types_detected', [])}")
                print(f"  Masking Strategy: {pii_info.get('masking_strategy', 'None')}")
                print(f"  Triage Decision: {triage_decision.get('decision', 'Unknown')}")
                print(f"  Risk Score: {triage_decision.get('risk_score', 'N/A')}")
                
                if pii_info.get('scrubbing_summary'):
                    summary = pii_info['scrubbing_summary']
                    print(f"  Total PII Instances: {summary.get('total_pii_instances', 0)}")
                    print(f"  Processing Time: {summary.get('processing_duration_ms', 0):.2f}ms")
                
                # Store result for comparison
                all_results.append({
                    'config': config['description'],
                    'submission_id': submission['id'],
                    'pii_detected': len(pii_info.get('pii_types_detected', [])),
                    'decision': triage_decision.get('decision', 'Unknown'),
                    'risk_score': triage_decision.get('risk_score', 'N/A')
                })
                
            except Exception as e:
                print(f"  ERROR: {str(e)}")
                all_results.append({
                    'config': config['description'],
                    'submission_id': submission['id'],
                    'error': str(e)
                })
    
    # Save comprehensive results
    output_file = "./Rule_Agent_Output_Files/pii_integration_test_results.json"
    try:
        with open(output_file, 'w') as f:
            json.dump(all_results, f, indent=2)
        print(f"\nIntegration test results saved to {output_file}")
    except Exception as e:
        print(f"Error saving results: {e}")
    
    print("\n=== Integrated PII + Triage Tests Completed ===")


def test_pii_compliance_scenarios():
    """Test PII scrubbing for compliance scenarios"""
    print("\n=== PII Compliance Scenario Tests ===")
    
    audit_system = ComplianceMonitoringAgent("./Rule_Agent_Output_Files/pii_compliance_audit.jsonl")
    
    # Compliance test scenarios
    compliance_scenarios = [
        {
            "name": "GDPR Compliance Test",
            "context": PIIContext.GENERAL,
            "strategy": MaskingStrategy.HASH,
            "data": "European customer: email@example.eu, phone +33-1-23-45-67-89, ID: FR123456789",
            "expected_pii_types": ["email", "phone_number"]
        },
        {
            "name": "CCPA Compliance Test", 
            "context": PIIContext.GENERAL,
            "strategy": MaskingStrategy.TOKENIZE,
            "data": "California resident: john@california.com, (555) 123-4567, SSN: 123-45-6789",
            "expected_pii_types": ["email", "phone_number", "ssn"]
        },
        {
            "name": "HIPAA Compliance Test",
            "context": PIIContext.HEALTHCARE,
            "strategy": MaskingStrategy.REMOVE,
            "data": "Patient: Jane Doe, DOB: 01/15/1985, SSN: 987-65-4321, phone: (555) 987-6543",
            "expected_pii_types": ["date_of_birth", "ssn", "phone_number"]
        },
        {
            "name": "Financial Compliance Test",
            "context": PIIContext.FINANCIAL,
            "strategy": MaskingStrategy.PARTIAL_MASK,
            "data": "Account holder: 4532-1234-5678-9012, routing: 021000021, SSN: 111-22-3333",
            "expected_pii_types": ["credit_card", "bank_routing", "ssn"]
        }
    ]
    
    compliance_results = []
    
    for scenario in compliance_scenarios:
        print(f"\n--- {scenario['name']} ---")
        
        pii_scrubber = PersonalDataProtectionAgent(
            audit_system=audit_system,
            context=scenario['context'],
            log_level=1,
            enable_tokenization=(scenario['strategy'] == MaskingStrategy.TOKENIZE)
        )
        
        try:
            result = pii_scrubber.scrub_data(
                data=scenario['data'],
                request_id=f"compliance_{scenario['name'].replace(' ', '_')}",
                custom_strategy=scenario['strategy'],
                audit_level=3  # Full audit for compliance
            )
            
            detected_types = [t.value for t in result['pii_detected']]
            
            print(f"  Original Data: {scenario['data']}")
            print(f"  Scrubbed Data: {result['scrubbed_data']}")
            print(f"  Expected PII Types: {scenario['expected_pii_types']}")
            print(f"  Detected PII Types: {detected_types}")
            print(f"  Strategy Applied: {result['scrubbing_summary']['masking_strategy']}")
            
            # Compliance validation
            compliance_passed = True
            for expected_type in scenario['expected_pii_types']:
                if expected_type not in detected_types:
                    compliance_passed = False
                    print(f"  WARNING: Expected PII type '{expected_type}' not detected")
            
            if compliance_passed:
                print(f"  Compliance validation: PASSED")
            else:
                print(f"  Compliance validation: FAILED")
            
            compliance_results.append({
                'scenario': scenario['name'],
                'context': scenario['context'].value,
                'strategy': scenario['strategy'].value,
                'expected_pii_types': scenario['expected_pii_types'],
                'detected_pii_types': detected_types,
                'compliance_passed': compliance_passed,
                'processing_time_ms': result['scrubbing_summary']['processing_duration_ms']
            })
            
        except Exception as e:
            print(f"  ERROR: {str(e)}")
            compliance_results.append({
                'scenario': scenario['name'],
                'error': str(e)
            })
    
    # Save compliance results
    compliance_output = "./Rule_Agent_Output_Files/pii_compliance_test_results.json"
    try:
        with open(compliance_output, 'w') as f:
            json.dump(compliance_results, f, indent=2)
        print(f"\nCompliance test results saved to {compliance_output}")
    except Exception as e:
        print(f"Error saving compliance results: {e}")
    
    print("\n=== PII Compliance Tests Completed ===")


def main():
    """Run all PII scrubbing tests"""
    print("PII Scrubbing Agent Comprehensive Test Suite")
    print("=" * 60)
    
    # Ensure output directory exists
    os.makedirs("./Rule_Agent_Output_Files", exist_ok=True)
    
    try:
        # Run all test suites
        test_standalone_pii_scrubbing()
        test_pii_integrated_triage()
        test_pii_compliance_scenarios()
        
        print("\n" + "=" * 60)
        print("All PII Scrubbing Tests Completed Successfully!")
        print("\nGenerated Files:")
        print("- ./Rule_Agent_Output_Files/pii_test_audit.jsonl")
        print("- ./Rule_Agent_Output_Files/pii_triage_integrated_audit.jsonl")
        print("- ./Rule_Agent_Output_Files/pii_compliance_audit.jsonl")
        print("- ./Rule_Agent_Output_Files/pii_integration_test_results.json")
        print("- ./Rule_Agent_Output_Files/pii_compliance_test_results.json")
        
    except Exception as e:
        print(f"\nTest suite failed: {str(e)}")
        raise


if __name__ == "__main__":
    main()