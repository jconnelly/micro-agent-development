#!/usr/bin/env python3

"""
Debug test to verify the extracted_rules output without using actual API calls.
This will help us isolate the issue from API quota problems.
"""

import json
from Agents.ComplianceMonitoringAgent import ComplianceMonitoringAgent, AuditLevel
from Agents.BusinessRuleExtractionAgent import BusinessRuleExtractorAgent

# Mock LLM client that returns predictable results
class MockLLMClient:
    def __init__(self):
        self.call_count = 0
    
    def generate_content(self, contents, generation_config=None):
        self.call_count += 1
        
        # Mock response with usage metadata
        class MockResponse:
            def __init__(self, rules):
                self.text = json.dumps({"business_rules": rules})
                self.usage_metadata = MockUsageMetadata()
        
        class MockUsageMetadata:
            def __init__(self):
                self.prompt_token_count = 100
                self.candidates_token_count = 50
        
        # Return different rules for different chunks
        if self.call_count == 1:
            rules = [{"rule_id": "rule1", "description": "Age must be >= 18"}]
        elif self.call_count == 2:
            rules = [{"rule_id": "rule2", "description": "Income must be > 50000"}]
        else:
            rules = [{"rule_id": f"rule{self.call_count}", "description": f"Rule from chunk {self.call_count}"}]
        
        return MockResponse(rules)

def main():
    print("=== Debug Test: Extracted Rules Output ===")
    
    # Read test file
    try:
        with open("./Example_Rule_Files/sample_legacy_code.java", 'r') as f:
            code_content = f.read()
        print(f"Successfully read test file ({len(code_content.split())} lines)")
    except FileNotFoundError:
        print("Test file not found")
        return

    # Initialize components
    audit_system = ComplianceMonitoringAgent("./Rule_Agent_Output_Files/debug_audit_logs.jsonl")
    mock_llm_client = MockLLMClient()
    
    rule_extractor_agent = BusinessRuleExtractorAgent(
        llm_client=mock_llm_client,
        audit_system=audit_system,
        log_level=1,  # Enable logging
        model_name="mock-llm-v1.0",
        llm_provider="test"
    )
    
    print("Agent initialized with mock LLM")
    
    # Call extraction
    extraction_result = rule_extractor_agent.extract_and_translate_rules(
        legacy_code_snippet=code_content,
        context="This Java code processes loan applications for a financial institution.",
        audit_level=AuditLevel.LEVEL_1.value
    )
    
    # Check results
    extracted_rules = extraction_result.get("extracted_rules", [])
    print(f"\n=== RESULTS ===")
    print(f"Result type: {type(extraction_result)}")
    print(f"Result keys: {list(extraction_result.keys())}")
    print(f"Extracted rules type: {type(extracted_rules)}")
    print(f"Extracted rules count: {len(extracted_rules)}")
    
    if extracted_rules:
        print(f"First rule: {extracted_rules[0]}")
        print(f"Sample rules: {[rule.get('rule_id', 'no_id') for rule in extracted_rules[:3]]}")
    else:
        print("WARNING: Extracted rules list is empty!")
    
    # Write to output file for comparison
    output_file = "./Rule_Agent_Output_Files/debug_extracted_rules.json"
    try:
        with open(output_file, 'w') as f:
            json.dump(extracted_rules, f, indent=2)
        print(f"Debug results written to {output_file}")
    except Exception as e:
        print(f"Error writing debug file: {e}")

if __name__ == "__main__":
    main()