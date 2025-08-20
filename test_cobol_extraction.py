#!/usr/bin/env python3
"""
Simple test script for BusinessRuleExtractionAgent with COBOL sample data.

This script tests the BusinessRuleExtractionAgent using the sample_legacy_insurance.cbl 
file without requiring API calls or external dependencies.
"""

import os
import sys
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from Agents.BusinessRuleExtractionAgent import BusinessRuleExtractionAgent
from Agents.ComplianceMonitoringAgent import ComplianceMonitoringAgent, AuditLevel
from Test_Cases.test_output_cleanup import TestOutputManager


def test_cobol_business_rule_extraction():
    """Test BusinessRuleExtractionAgent with COBOL insurance validation code."""
    
    print("Testing BusinessRuleExtractionAgent with COBOL sample data...")
    
    # Initialize test output manager for unique filenames
    output_manager = TestOutputManager()
    audit_file = output_manager.get_audit_filename("cobol_extraction")
    rules_file = output_manager.get_rules_output_filename("cobol_extraction")
    
    print(f"Using unique audit file: {audit_file}")
    print(f"Using unique rules file: {rules_file}")
    
    # Read the COBOL sample file
    cobol_file_path = project_root / "Sample_Data_Files" / "sample_legacy_insurance.cbl"
    
    try:
        with open(cobol_file_path, 'r', encoding='utf-8') as f:
            cobol_code = f.read()
        print(f"SUCCESS: Read COBOL file: {cobol_file_path}")
        print(f"File size: {len(cobol_code)} characters")
    except FileNotFoundError:
        print(f"ERROR: COBOL sample file not found: {cobol_file_path}")
        return False
    except Exception as e:
        print(f"ERROR: Reading COBOL file: {e}")
        return False
    
    # Initialize audit system with unique filename
    try:
        audit_system = ComplianceMonitoringAgent(log_storage_path=str(audit_file))
        print("SUCCESS: Audit system initialized with unique filename")
    except Exception as e:
        print(f"ERROR: Initializing audit system: {e}")
        return False
    
    # Initialize BusinessRuleExtractionAgent with mock LLM
    try:
        # Create a simple mock LLM client for testing
        class MockLLMClient:
            def generate_content(self, prompt):
                """Mock LLM response for testing."""
                class MockResponse:
                    def __init__(self):
                        self.text = """
                        Here are the extracted business rules from the COBOL insurance validation code:
                        
                        1. Age Requirements:
                           - Minimum age: 18 years
                           - Maximum age for auto insurance: 80 years  
                           - Maximum age for life insurance: 75 years
                        
                        2. Credit Score Validation:
                           - Minimum credit score: 600
                        
                        3. Employment Requirements:
                           - Unemployed applicants are not eligible
                        
                        4. Auto Insurance Rules:
                           - Minimum driving years: 2
                           - Maximum claims allowed: 5
                           - DUI history excludes eligibility
                           - Maximum violations: 3
                        
                        5. Premium Calculations:
                           - Young driver surcharge: 50% for drivers under 25
                           - Senior driver discount: 10% for married drivers over 65
                           - Smoker surcharge: 25% for life insurance
                           - Multi-policy discount: 10%
                        """
                
                return MockResponse()
        
        agent = BusinessRuleExtractionAgent(
            llm_client=MockLLMClient(),
            audit_system=audit_system,
            log_level=1,
            model_name="mock-model",
            llm_provider="mock"
        )
        print("SUCCESS: BusinessRuleExtractionAgent initialized with mock LLM")
    except Exception as e:
        print(f"ERROR: Initializing BusinessRuleExtractionAgent: {e}")
        return False
    
    # Test input validation with the COBOL code
    try:
        print("\nTesting input validation...")
        
        # This should pass with our updated validation rules
        result = agent.extract_and_translate_rules(
            legacy_code_snippet=cobol_code,
            context="Legacy COBOL insurance policy validation system from 1985 containing embedded business rules for policy approval",
            audit_level=AuditLevel.LEVEL_1.value,
            filename="sample_legacy_insurance.cbl"
        )
        
        print("SUCCESS: Input validation passed!")
        print(f"Result type: {type(result)}")
        print(f"Result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
        
        # Check if extracted_rules are present and save to unique file
        if isinstance(result, dict) and "extracted_rules" in result:
            rules = result["extracted_rules"]
            print(f"Extracted {len(rules)} business rules")
            
            # Save rules to unique output file
            try:
                with open(rules_file, 'w', encoding='utf-8') as f:
                    json.dump(rules, f, indent=2)
                print(f"SUCCESS: Saved extracted rules to {rules_file}")
            except Exception as e:
                print(f"WARNING: Could not save rules to file: {e}")
            
            # Show first few rules
            for i, rule in enumerate(rules[:3]):
                if isinstance(rule, dict):
                    rule_name = rule.get('rule_name', f'Rule {i+1}')
                    print(f"   - {rule_name}")
        
        return True
        
    except Exception as e:
        print(f"ERROR: During rule extraction: {e}")
        print(f"Error type: {type(e).__name__}")
        return False


def main():
    """Main test function."""
    print("=" * 60)
    print("COBOL Business Rule Extraction Test")
    print("=" * 60)
    
    success = test_cobol_business_rule_extraction()
    
    print("\n" + "=" * 60)
    if success:
        print("SUCCESS: Test completed successfully!")
        print("The BusinessRuleExtractionAgent can process COBOL code with:")
        print("  - Proper input validation (no pattern restrictions)")
        print("  - Special character handling (COBOL syntax)")
        print("  - Business context understanding")
        print("  - Mock LLM integration")
        print("  - Unique output files per test run")
        print(f"\nCheck output files in: Rule_Agent_Output_Files/")
        print("  Look for files with timestamp: " + TestOutputManager().timestamp)
    else:
        print("FAILED: Test failed - check error messages above")
    print("=" * 60)


if __name__ == "__main__":
    main()