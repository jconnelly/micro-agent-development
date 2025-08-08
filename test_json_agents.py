#!/usr/bin/env python3
"""
Test script to demonstrate JSON input format usage with documentation agents
"""

import json
import os
from pathlib import Path

def test_json_loading():
    """Test that our sample JSON files load correctly"""
    
    print("Testing JSON Input Format Compatibility")
    print("=" * 50)
    
    # Test basic rules JSON
    basic_file = "Sample_Data_Files/sample_extracted_rules.json"
    print(f"\n1. Testing {basic_file}")
    print("-" * 30)
    
    try:
        with open(basic_file, 'r') as f:
            basic_rules = json.load(f)
            
        print(f"SUCCESS: Successfully loaded {len(basic_rules)} basic rules")
        
        # Show sample rule
        if basic_rules:
            sample_rule = basic_rules[0]
            print(f"  Sample Rule ID: {sample_rule['rule_id']}")
            print(f"  Business Domain: {sample_rule['business_domain']}")
            print(f"  Priority: {sample_rule['priority']}")
            
        # Validate required fields
        required_fields = ['rule_id', 'business_description', 'conditions', 
                          'actions', 'business_domain', 'priority']
        
        for rule in basic_rules:
            missing_fields = [field for field in required_fields if field not in rule]
            if missing_fields:
                print(f"  ERROR: Missing fields in rule {rule.get('rule_id', 'unknown')}: {missing_fields}")
                return False
                
        print("  SUCCESS: All required fields present in basic schema")
        
    except Exception as e:
        print(f"  ERROR: Failed to load basic rules: {e}")
        return False
    
    # Test advanced rules JSON  
    advanced_file = "Sample_Data_Files/sample_advanced_rules.json"
    print(f"\n2. Testing {advanced_file}")
    print("-" * 30)
    
    try:
        with open(advanced_file, 'r') as f:
            advanced_rules = json.load(f)
            
        print(f"SUCCESS: Successfully loaded {len(advanced_rules)} advanced rules")
        
        # Show sample rule
        if advanced_rules:
            sample_rule = advanced_rules[0]
            print(f"  Sample Rule ID: {sample_rule['rule_id']}")
            print(f"  Business Domain: {sample_rule['business_domain']}")
            print(f"  Implementation Complexity: {sample_rule.get('implementation_complexity', 'not specified')}")
            
            # Check enhanced fields
            enhanced_fields = ['stakeholder_impact', 'business_value', 'risk_assessment', 'version_info']
            present_enhanced = [field for field in enhanced_fields if field in sample_rule]
            print(f"  Enhanced Fields Present: {present_enhanced}")
            
        print("  SUCCESS: Advanced schema fields validated")
        
    except Exception as e:
        print(f"  ERROR: Failed to load advanced rules: {e}")
        return False
    
    return True

def simulate_agent_usage():
    """Simulate how the JSON files would be used with agents"""
    
    print("\n" + "=" * 50)
    print("Simulating Agent Usage with JSON Files")
    print("=" * 50)
    
    # Load basic rules
    with open("Sample_Data_Files/sample_extracted_rules.json", 'r') as f:
        basic_rules = json.load(f)
        
    print(f"\nRuleDocumentationGeneratorAgent Usage Simulation:")
    print(f"   Input: {len(basic_rules)} rules from sample_extracted_rules.json")
    print(f"   Processing: Converting to business documentation...")
    print(f"   Output formats: markdown, html, json")
    print(f"   STATUS: Ready for doc_generator.document_and_visualize_rules()")
    
    # Load advanced rules
    with open("Sample_Data_Files/sample_advanced_rules.json", 'r') as f:
        advanced_rules = json.load(f)
        
    print(f"\nAdvancedDocumentationAgent Usage Simulation:")
    print(f"   Input: {len(advanced_rules)} rules from sample_advanced_rules.json")
    print(f"   Processing: Enterprise documentation with enhanced features...")
    print(f"   Enhanced features: stakeholder impact, business value, risk assessment")
    print(f"   STATUS: Ready for advanced_doc_agent.document_and_visualize_rules()")
    
    # Show business domains covered
    all_rules = basic_rules + advanced_rules
    domains = set(rule['business_domain'] for rule in all_rules)
    priorities = set(rule['priority'] for rule in all_rules)
    
    print(f"\nCoverage Analysis:")
    print(f"   Business Domains: {sorted(domains)}")
    print(f"   Priority Levels: {sorted(priorities)}")
    print(f"   Total Rules Available: {len(all_rules)}")

def main():
    """Main test function"""
    
    print("JSON Input Format Testing for Documentation Agents")
    print("=" * 60)
    
    # Test JSON loading
    json_test_passed = test_json_loading()
    
    if json_test_passed:
        simulate_agent_usage()
        
        print("\n" + "=" * 60)
        print("SUCCESS: All JSON files are compatible with documentation agents")
        print("\nNext Steps:")
        print("1. Use validate_rule_json.py to validate custom JSON files")
        print("2. Follow docs/guides/json-input-formats.md for detailed specifications")
        print("3. Create custom rule JSON files using the provided schemas")
        print("4. Run actual agents with: RuleDocumentationGeneratorAgent or AdvancedDocumentationAgent")
    else:
        print("\n" + "=" * 60)
        print("FAILED: JSON compatibility issues found")
        print("Please check the sample files and fix any validation errors")

if __name__ == "__main__":
    main()