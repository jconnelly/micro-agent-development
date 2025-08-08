#!/usr/bin/env python3
"""
Comprehensive JSON validation for rule documentation agents
"""

import json
import os
from typing import List, Dict, Any
from pathlib import Path

def validate_basic_rule_schema(rules: List[Dict[str, Any]]) -> bool:
    """Validate basic rule schema for RuleDocumentationGeneratorAgent"""
    
    required_fields = [
        'rule_id', 'business_description', 'conditions', 
        'actions', 'business_domain', 'priority'
    ]
    
    valid_domains = [
        'banking', 'insurance', 'healthcare', 'trading', 
        'government', 'ecommerce', 'manufacturing', 'technology'
    ]
    
    valid_priorities = ['critical', 'high', 'medium', 'low']
    
    print(f"Validating {len(rules)} rules for basic schema...")
    
    for i, rule in enumerate(rules):
        # Check if rule is dictionary
        if not isinstance(rule, dict):
            print(f"ERROR Rule {i}: Must be an object")
            return False
            
        # Check required fields
        for field in required_fields:
            if field not in rule:
                print(f"ERROR Rule {i}: Missing required field '{field}'")
                return False
                
            if not isinstance(rule[field], str) or not rule[field].strip():
                print(f"ERROR Rule {i}: Field '{field}' must be non-empty string")
                return False
        
        # Validate business domain
        if rule['business_domain'] not in valid_domains:
            print(f"ERROR Rule {i}: Invalid business_domain '{rule['business_domain']}'")
            print(f"   Valid domains: {valid_domains}")
            return False
            
        # Validate priority
        if rule['priority'] not in valid_priorities:
            print(f"ERROR Rule {i}: Invalid priority '{rule['priority']}'")
            print(f"   Valid priorities: {valid_priorities}")
            return False
            
        # Validate optional array fields
        if 'dependencies' in rule and not isinstance(rule['dependencies'], list):
            print(f"ERROR Rule {i}: 'dependencies' must be an array")
            return False
    
    print("SUCCESS: Basic schema validation passed")
    return True

def validate_advanced_rule_schema(rules: List[Dict[str, Any]]) -> bool:
    """Validate enhanced schema for AdvancedDocumentationAgent"""
    
    # First validate basic schema
    if not validate_basic_rule_schema(rules):
        return False
        
    print(f"Validating enhanced fields for AdvancedDocumentationAgent...")
    
    valid_complexity = ['low', 'medium', 'high', 'critical']
    
    for i, rule in enumerate(rules):
        # Validate enhanced optional fields
        
        # Stakeholder impact validation
        if 'stakeholder_impact' in rule:
            if not isinstance(rule['stakeholder_impact'], dict):
                print(f"ERROR Rule {i}: 'stakeholder_impact' must be an object")
                return False
                
        # Implementation complexity validation  
        if 'implementation_complexity' in rule:
            if rule['implementation_complexity'] not in valid_complexity:
                print(f"ERROR Rule {i}: Invalid implementation_complexity")
                return False
                
        # Testing requirements validation
        if 'testing_requirements' in rule:
            if not isinstance(rule['testing_requirements'], list):
                print(f"ERROR Rule {i}: 'testing_requirements' must be an array") 
                return False
                
        # Business value validation
        if 'business_value' in rule:
            if not isinstance(rule['business_value'], dict):
                print(f"ERROR Rule {i}: 'business_value' must be an object")
                return False
                
        # Risk assessment validation
        if 'risk_assessment' in rule:
            if not isinstance(rule['risk_assessment'], dict):
                print(f"ERROR Rule {i}: 'risk_assessment' must be an object")
                return False
                
        # Version info validation
        if 'version_info' in rule:
            if not isinstance(rule['version_info'], dict):
                print(f"ERROR Rule {i}: 'version_info' must be an object")
                return False
                
    print("SUCCESS: Advanced schema validation passed")
    return True

def validate_json_file(file_path: str, schema_type: str = "basic") -> bool:
    """Validate JSON file for rule documentation agents"""
    
    print(f"Validating JSON file: {file_path}")
    print(f"Schema type: {schema_type}")
    print("=" * 50)
    
    # Check file exists
    if not Path(file_path).exists():
        print(f"ERROR: File not found: {file_path}")
        return False
        
    # Load JSON
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print("SUCCESS: JSON parsing successful")
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON syntax: {e}")
        return False
    except Exception as e:
        print(f"ERROR: File reading error: {e}")
        return False
        
    # Validate root structure
    if not isinstance(data, list):
        print("ERROR: Root element must be an array of rule objects")
        return False
        
    if len(data) == 0:
        print("WARNING: Empty rules array")
        return True
        
    # Schema validation
    if schema_type == "basic":
        return validate_basic_rule_schema(data)
    elif schema_type == "advanced":
        return validate_advanced_rule_schema(data)
    else:
        print(f"ERROR: Unknown schema type: {schema_type}")
        return False

def main():
    """Main validation function"""
    
    # Test files to validate
    test_files = [
        ("Sample_Data_Files/sample_extracted_rules.json", "basic"),
        ("Sample_Data_Files/sample_advanced_rules.json", "advanced")
    ]
    
    print("JSON Schema Validation for Rule Documentation Agents")
    print("=" * 60)
    
    results = []
    
    for file_path, schema_type in test_files:
        print(f"\nTesting {file_path} ({schema_type} schema)")
        print("-" * 50)
        
        result = validate_json_file(file_path, schema_type)
        results.append((file_path, schema_type, result))
        
        if result:
            print(f"RESULT: {file_path}: PASSED")
        else:
            print(f"RESULT: {file_path}: FAILED")
    
    # Summary
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    
    for file_path, schema_type, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{status}: {Path(file_path).name} ({schema_type})")
        
    passed = sum(1 for _, _, result in results if result)
    total = len(results)
    
    print(f"\nOverall: {passed}/{total} files passed validation")
    
    if passed == total:
        print("SUCCESS: All JSON files are valid and ready for use!")
    else:
        print("WARNING: Please fix validation errors before using with agents")

if __name__ == "__main__":
    main()