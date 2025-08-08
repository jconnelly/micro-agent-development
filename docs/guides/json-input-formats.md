# JSON Input Format Guide

Complete specifications for agents that require structured JSON input files with specific schemas and formats.

## 🎯 Overview

Several agents in the platform require JSON input files with **specific formats and schemas**. These agents process structured business rule data and need precise JSON formatting to ensure proper functionality and accurate results.

## 📋 **Required JSON Input Agents**

| Agent | Purpose | JSON Schema Required | Sample Available |
|-------|---------|---------------------|------------------|
| **RuleDocumentationGeneratorAgent** | Business rule documentation | ✅ Extracted Rules Schema | ✅ `sample_extracted_rules.json` |
| **AdvancedDocumentationAgent** | Enterprise documentation platform | ✅ Enhanced Rules Schema | ✅ `sample_advanced_rules.json` |

---

## 📄 **RuleDocumentationGeneratorAgent JSON Format**

### **Required Input Format**

The `RuleDocumentationGeneratorAgent.document_and_visualize_rules()` method requires a **List of Dict** with this exact schema:

```json
[
  {
    "rule_id": "string",
    "business_description": "string", 
    "conditions": "string",
    "actions": "string",
    "business_domain": "string",
    "priority": "string",
    "source_lines": "string (optional)",
    "technical_implementation": "string (optional)",
    "compliance_notes": "string (optional)",
    "dependencies": "array (optional)"
  }
]
```

### **Field Specifications**

| Field | Type | Required | Description | Valid Values |
|-------|------|----------|-------------|--------------|
| `rule_id` | string | ✅ **Required** | Unique identifier for the rule | Format: `RULE_001`, `LOAN_APPROVAL_01` |
| `business_description` | string | ✅ **Required** | Human-readable rule description | Clear business language, no technical jargon |
| `conditions` | string | ✅ **Required** | Rule trigger conditions | Business logic conditions (AND/OR statements) |
| `actions` | string | ✅ **Required** | Actions taken when rule triggers | Specific business actions or outcomes |
| `business_domain` | string | ✅ **Required** | Domain classification | `banking`, `insurance`, `healthcare`, `trading`, `government`, `ecommerce` |
| `priority` | string | ✅ **Required** | Business importance level | `critical`, `high`, `medium`, `low` |
| `source_lines` | string | ❌ Optional | Original code line references | `lines 45-67`, `function processLoan()` |
| `technical_implementation` | string | ❌ Optional | Technical implementation details | Programming language specifics |
| `compliance_notes` | string | ❌ Optional | Regulatory compliance information | GDPR, HIPAA, SOX, etc. |
| `dependencies` | array | ❌ Optional | Rule dependencies | `["RULE_001", "RULE_003"]` |

### **Sample Valid JSON File**

**File:** `Sample_Data_Files/sample_extracted_rules.json`

```json
[
  {
    "rule_id": "LOAN_001", 
    "business_description": "Prime borrower qualification criteria for conventional loans",
    "conditions": "Credit score must be 650 or higher AND debt-to-income ratio must be 43% or lower AND applicant must have verified employment",
    "actions": "Approve loan application for manual underwriting review and set interest rate to prime rate",
    "business_domain": "banking",
    "priority": "critical",
    "source_lines": "lines 145-162 in loan_processor.cobol",
    "technical_implementation": "COBOL IF-THEN-ELSE logic with nested conditions",
    "compliance_notes": "Complies with Equal Credit Opportunity Act (ECOA) requirements",
    "dependencies": ["CREDIT_VERIFICATION_001", "INCOME_VALIDATION_002"]
  },
  {
    "rule_id": "LOAN_002",
    "business_description": "Subprime borrower rejection criteria for high-risk applications", 
    "conditions": "Credit score is below 580 OR debt-to-income ratio exceeds 50% OR bankruptcy within last 2 years",
    "actions": "Automatically reject loan application with specific reason codes and compliance documentation",
    "business_domain": "banking",
    "priority": "critical",
    "source_lines": "lines 163-185 in loan_processor.cobol",
    "technical_implementation": "COBOL conditional logic with multiple exit points",
    "compliance_notes": "Adverse action notices required per Fair Credit Reporting Act (FCRA)",
    "dependencies": ["CREDIT_HISTORY_001", "BANKRUPTCY_CHECK_001"]
  },
  {
    "rule_id": "INSURANCE_001",
    "business_description": "Auto insurance eligibility age restrictions",
    "conditions": "Applicant age is between 18 and 80 years for standard auto insurance coverage",
    "actions": "Qualify applicant for standard auto insurance rates and coverage options",
    "business_domain": "insurance", 
    "priority": "high",
    "source_lines": "VALIDATE-AGE section in insurance_validation.cbl",
    "technical_implementation": "COBOL age validation with MIN-AGE and MAX-AGE constants",
    "compliance_notes": "State insurance commission age requirements compliance"
  },
  {
    "rule_id": "HEALTHCARE_001",
    "business_description": "Patient medication dosage safety check for elderly patients",
    "conditions": "Patient age is over 65 AND prescribed medication has elderly dosage warnings",
    "actions": "Flag prescription for clinical pharmacist review and adjust dosage recommendations",
    "business_domain": "healthcare",
    "priority": "critical", 
    "source_lines": "medication_safety_check() function lines 89-120",
    "compliance_notes": "HIPAA compliant patient safety protocol",
    "dependencies": ["PATIENT_AGE_VERIFICATION", "DRUG_INTERACTION_CHECK"]
  }
]
```

### **Validation Requirements**

#### ✅ **JSON Must Be Valid**
```python
import json

# Test your JSON file
def validate_json_file(file_path):
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        print("✅ Valid JSON format")
        return data
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON: {e}")
        return None
```

#### ✅ **Schema Validation**
```python
def validate_rule_schema(rules_data):
    """Validate extracted rules JSON schema"""
    required_fields = ['rule_id', 'business_description', 'conditions', 
                      'actions', 'business_domain', 'priority']
    
    if not isinstance(rules_data, list):
        print("❌ Root element must be an array")
        return False
        
    for i, rule in enumerate(rules_data):
        if not isinstance(rule, dict):
            print(f"❌ Rule {i} must be an object")
            return False
            
        # Check required fields
        for field in required_fields:
            if field not in rule:
                print(f"❌ Rule {i} missing required field: {field}")
                return False
                
            if not isinstance(rule[field], str) or not rule[field].strip():
                print(f"❌ Rule {i} field '{field}' must be non-empty string")
                return False
    
    print("✅ Schema validation passed")
    return True
```

### **Usage Example with JSON File**

```python
import json
from Agents.RuleDocumentationGeneratorAgent import RuleDocumentationGeneratorAgent
from Agents.ComplianceMonitoringAgent import ComplianceMonitoringAgent
import google.generativeai as genai
import os

# Configure LLM
genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))
llm_client = genai.GenerativeModel('gemini-1.5-flash')

# Initialize agents
audit_system = ComplianceMonitoringAgent()
doc_generator = RuleDocumentationGeneratorAgent(
    llm_client=llm_client,
    audit_system=audit_system,
    model_name="gemini-1.5-flash"
)

# Load JSON file with extracted rules
with open("Sample_Data_Files/sample_extracted_rules.json", "r") as f:
    extracted_rules = json.load(f)

# Generate documentation
result = doc_generator.document_and_visualize_rules(
    extracted_rules=extracted_rules,
    output_format="markdown",  # Options: "markdown", "html", "json"
    audit_level=2
)

# Save generated documentation
with open("generated_business_documentation.md", "w") as f:
    f.write(result['generated_documentation'])

print(f"✅ Generated documentation for {len(extracted_rules)} business rules")
print(f"📄 Output: generated_business_documentation.md")
```

---

## 🚀 **AdvancedDocumentationAgent JSON Format**

### **Enhanced Schema Requirements**

The `AdvancedDocumentationAgent` extends the base schema with additional enterprise features:

```json
[
  {
    "rule_id": "string",
    "business_description": "string",
    "conditions": "string", 
    "actions": "string",
    "business_domain": "string",
    "priority": "string",
    "source_lines": "string (optional)",
    "technical_implementation": "string (optional)",
    "compliance_notes": "string (optional)",
    "dependencies": "array (optional)",
    
    // Enhanced fields for AdvancedDocumentationAgent
    "stakeholder_impact": "object (optional)",
    "implementation_complexity": "string (optional)",
    "testing_requirements": "array (optional)",
    "business_value": "object (optional)",
    "risk_assessment": "object (optional)",
    "version_info": "object (optional)"
  }
]
```

### **Enhanced Field Specifications**

| Field | Type | Required | Description | Example Values |
|-------|------|----------|-------------|----------------|
| `stakeholder_impact` | object | ❌ Optional | Impact on different stakeholder groups | `{"customers": "high", "operations": "medium", "compliance": "critical"}` |
| `implementation_complexity` | string | ❌ Optional | Implementation difficulty assessment | `low`, `medium`, `high`, `critical` |
| `testing_requirements` | array | ❌ Optional | Required testing scenarios | `["unit_tests", "integration_tests", "compliance_validation"]` |
| `business_value` | object | ❌ Optional | Business value metrics | `{"cost_savings": 50000, "time_savings_hours": 200, "risk_reduction": "high"}` |
| `risk_assessment` | object | ❌ Optional | Risk analysis | `{"operational_risk": "low", "compliance_risk": "medium", "financial_impact": 25000}` |
| `version_info` | object | ❌ Optional | Version and change tracking | `{"version": "1.2", "last_updated": "2024-01-15", "changed_by": "business_analyst"}` |

### **Sample Enhanced JSON File**

**File:** `Sample_Data_Files/sample_advanced_rules.json`

```json
[
  {
    "rule_id": "ENTERPRISE_LOAN_001",
    "business_description": "Enterprise lending decision framework for commercial real estate loans over $5M",
    "conditions": "Loan amount exceeds $5,000,000 AND property type is commercial real estate AND borrower has minimum 25% down payment AND debt service coverage ratio >= 1.25",
    "actions": "Route to executive lending committee for approval with full financial analysis and require additional collateral documentation",
    "business_domain": "banking",
    "priority": "critical",
    "source_lines": "enterprise_lending_module.java lines 234-289",
    "technical_implementation": "Java Spring Boot microservice with database integration and workflow orchestration",
    "compliance_notes": "Complies with Basel III capital requirements and Dodd-Frank qualified mortgage standards",
    "dependencies": ["CREDIT_ANALYSIS_ENTERPRISE", "COLLATERAL_VALUATION", "COMMITTEE_WORKFLOW"],
    
    "stakeholder_impact": {
      "executive_committee": "high",
      "loan_officers": "medium", 
      "risk_management": "critical",
      "customers": "medium",
      "compliance_team": "high"
    },
    "implementation_complexity": "high",
    "testing_requirements": [
      "loan_amount_boundary_testing",
      "property_type_validation",
      "dscr_calculation_accuracy",
      "committee_routing_workflow",
      "compliance_rule_validation"
    ],
    "business_value": {
      "annual_loan_volume_impact": 50000000,
      "risk_reduction_percentage": 15,
      "processing_time_reduction_hours": 48,
      "compliance_cost_savings": 125000
    },
    "risk_assessment": {
      "operational_risk": "medium",
      "compliance_risk": "low", 
      "financial_impact_if_failed": 2000000,
      "reputation_risk": "high",
      "mitigation_strategies": ["executive_oversight", "dual_approval", "automated_compliance_checks"]
    },
    "version_info": {
      "version": "2.1",
      "last_updated": "2024-01-15T10:30:00Z",
      "changed_by": "senior_credit_analyst",
      "change_reason": "Updated DSCR threshold per regulatory guidance",
      "approval_status": "approved"
    }
  },
  {
    "rule_id": "INSURANCE_ENTERPRISE_001", 
    "business_description": "Large commercial property insurance underwriting decision matrix",
    "conditions": "Property value exceeds $10,000,000 OR high-risk industry classification OR located in catastrophe-prone geographic zone",
    "actions": "Require specialized risk assessment, additional reinsurance coverage, and senior underwriter approval with enhanced premium calculation",
    "business_domain": "insurance",
    "priority": "critical",
    "source_lines": "commercial_underwriting.py class CommercialRiskAnalyzer methods 156-203",
    "technical_implementation": "Python class-based system with ML risk scoring integration and external data sources",
    "compliance_notes": "Meets state insurance commission capital adequacy requirements and catastrophic risk standards",
    "dependencies": ["PROPERTY_VALUATION_SERVICE", "CATASTROPHE_MODELING", "REINSURANCE_CALCULATOR"],
    
    "stakeholder_impact": {
      "underwriters": "critical",
      "risk_managers": "high",
      "reinsurance_team": "high", 
      "sales_team": "medium",
      "customers": "medium"
    },
    "implementation_complexity": "critical",
    "testing_requirements": [
      "property_value_threshold_testing",
      "industry_classification_accuracy",
      "geographic_zone_mapping",
      "ml_risk_scoring_validation", 
      "reinsurance_calculation_accuracy"
    ],
    "business_value": {
      "annual_premium_protected": 25000000,
      "loss_ratio_improvement": 8.5,
      "underwriting_accuracy_increase": 22,
      "processing_efficiency_gain_hours": 120
    },
    "risk_assessment": {
      "operational_risk": "high",
      "compliance_risk": "medium",
      "financial_impact_if_failed": 15000000,
      "reputation_risk": "critical",
      "mitigation_strategies": ["senior_review", "ml_model_validation", "geographic_risk_modeling"]
    },
    "version_info": {
      "version": "1.4",
      "last_updated": "2024-02-01T14:15:30Z", 
      "changed_by": "chief_underwriter",
      "change_reason": "Enhanced catastrophe modeling integration",
      "approval_status": "approved"
    }
  }
]
```

### **Advanced Usage Example**

```python
import json
from Agents.AdvancedDocumentationAgent import AdvancedDocumentationAgent
from Agents.ComplianceMonitoringAgent import ComplianceMonitoringAgent
import google.generativeai as genai
import os

# Configure LLM
genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))
llm_client = genai.GenerativeModel('gemini-1.5-flash')

# Initialize advanced documentation agent
audit_system = ComplianceMonitoringAgent()
advanced_doc_agent = AdvancedDocumentationAgent(
    llm_client=llm_client,
    audit_system=audit_system,
    model_name="gemini-1.5-flash"
)

# Load enhanced rules JSON file
with open("Sample_Data_Files/sample_advanced_rules.json", "r") as f:
    enhanced_rules = json.load(f)

# Generate comprehensive enterprise documentation
result = advanced_doc_agent.document_and_visualize_rules(
    extracted_rules=enhanced_rules,
    output_format="html",  # Generate rich HTML documentation
    audit_level=3  # Full enterprise audit trail
)

# The AdvancedDocumentationAgent provides additional capabilities:
# - Stakeholder impact analysis
# - Implementation complexity assessment  
# - Business value quantification
# - Risk assessment integration
# - Version control and change tracking

print(f"✅ Generated enterprise documentation for {len(enhanced_rules)} rules")
print(f"📊 Stakeholder analysis completed")
print(f"💰 Business value assessment included") 
print(f"⚖️ Risk assessment integrated")
```

---

## 📊 **JSON Schema Validation Tools**

### **Comprehensive Validation Script**

Create `validate_rule_json.py`:

```python
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
    
    print(f"🔍 Validating {len(rules)} rules for basic schema...")
    
    for i, rule in enumerate(rules):
        # Check if rule is dictionary
        if not isinstance(rule, dict):
            print(f"❌ Rule {i}: Must be an object")
            return False
            
        # Check required fields
        for field in required_fields:
            if field not in rule:
                print(f"❌ Rule {i}: Missing required field '{field}'")
                return False
                
            if not isinstance(rule[field], str) or not rule[field].strip():
                print(f"❌ Rule {i}: Field '{field}' must be non-empty string")
                return False
        
        # Validate business domain
        if rule['business_domain'] not in valid_domains:
            print(f"❌ Rule {i}: Invalid business_domain '{rule['business_domain']}'")
            print(f"   Valid domains: {valid_domains}")
            return False
            
        # Validate priority
        if rule['priority'] not in valid_priorities:
            print(f"❌ Rule {i}: Invalid priority '{rule['priority']}'")
            print(f"   Valid priorities: {valid_priorities}")
            return False
            
        # Validate optional array fields
        if 'dependencies' in rule and not isinstance(rule['dependencies'], list):
            print(f"❌ Rule {i}: 'dependencies' must be an array")
            return False
    
    print("✅ Basic schema validation passed")
    return True

def validate_advanced_rule_schema(rules: List[Dict[str, Any]]) -> bool:
    """Validate enhanced schema for AdvancedDocumentationAgent"""
    
    # First validate basic schema
    if not validate_basic_rule_schema(rules):
        return False
        
    print(f"🚀 Validating enhanced fields for AdvancedDocumentationAgent...")
    
    valid_complexity = ['low', 'medium', 'high', 'critical']
    
    for i, rule in enumerate(rules):
        # Validate enhanced optional fields
        
        # Stakeholder impact validation
        if 'stakeholder_impact' in rule:
            if not isinstance(rule['stakeholder_impact'], dict):
                print(f"❌ Rule {i}: 'stakeholder_impact' must be an object")
                return False
                
        # Implementation complexity validation  
        if 'implementation_complexity' in rule:
            if rule['implementation_complexity'] not in valid_complexity:
                print(f"❌ Rule {i}: Invalid implementation_complexity")
                return False
                
        # Testing requirements validation
        if 'testing_requirements' in rule:
            if not isinstance(rule['testing_requirements'], list):
                print(f"❌ Rule {i}: 'testing_requirements' must be an array") 
                return False
                
        # Business value validation
        if 'business_value' in rule:
            if not isinstance(rule['business_value'], dict):
                print(f"❌ Rule {i}: 'business_value' must be an object")
                return False
                
        # Risk assessment validation
        if 'risk_assessment' in rule:
            if not isinstance(rule['risk_assessment'], dict):
                print(f"❌ Rule {i}: 'risk_assessment' must be an object")
                return False
                
        # Version info validation
        if 'version_info' in rule:
            if not isinstance(rule['version_info'], dict):
                print(f"❌ Rule {i}: 'version_info' must be an object")
                return False
                
    print("✅ Advanced schema validation passed")
    return True

def validate_json_file(file_path: str, schema_type: str = "basic") -> bool:
    """Validate JSON file for rule documentation agents"""
    
    print(f"📂 Validating JSON file: {file_path}")
    print(f"🔧 Schema type: {schema_type}")
    print("=" * 50)
    
    # Check file exists
    if not Path(file_path).exists():
        print(f"❌ File not found: {file_path}")
        return False
        
    # Load JSON
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print("✅ JSON parsing successful")
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON syntax: {e}")
        return False
    except Exception as e:
        print(f"❌ File reading error: {e}")
        return False
        
    # Validate root structure
    if not isinstance(data, list):
        print("❌ Root element must be an array of rule objects")
        return False
        
    if len(data) == 0:
        print("⚠️  Warning: Empty rules array")
        return True
        
    # Schema validation
    if schema_type == "basic":
        return validate_basic_rule_schema(data)
    elif schema_type == "advanced":
        return validate_advanced_rule_schema(data)
    else:
        print(f"❌ Unknown schema type: {schema_type}")
        return False

def main():
    """Main validation function"""
    
    # Test files to validate
    test_files = [
        ("Sample_Data_Files/sample_extracted_rules.json", "basic"),
        ("Sample_Data_Files/sample_advanced_rules.json", "advanced")
    ]
    
    print("🧪 JSON Schema Validation for Rule Documentation Agents")
    print("=" * 60)
    
    results = []
    
    for file_path, schema_type in test_files:
        print(f"\n📋 Testing {file_path} ({schema_type} schema)")
        print("-" * 50)
        
        result = validate_json_file(file_path, schema_type)
        results.append((file_path, schema_type, result))
        
        if result:
            print(f"🎉 {file_path}: PASSED")
        else:
            print(f"💥 {file_path}: FAILED")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 VALIDATION SUMMARY")
    print("=" * 60)
    
    for file_path, schema_type, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {Path(file_path).name} ({schema_type})")
        
    passed = sum(1 for _, _, result in results if result)
    total = len(results)
    
    print(f"\n🏁 Overall: {passed}/{total} files passed validation")
    
    if passed == total:
        print("🎉 All JSON files are valid and ready for use!")
    else:
        print("⚠️  Please fix validation errors before using with agents")

if __name__ == "__main__":
    main()
```

Run the validation:

```bash
python validate_rule_json.py
```

---

## 🛠️ **JSON File Creation Tools**

### **Rule Builder Script**

Create `build_rule_json.py`:

```python
#!/usr/bin/env python3
"""
Interactive tool to create valid JSON files for rule documentation agents
"""

import json
from typing import List, Dict, Any

def create_basic_rule() -> Dict[str, Any]:
    """Interactive creation of basic rule"""
    
    print("\n📝 Creating New Business Rule")
    print("-" * 30)
    
    rule = {}
    
    # Required fields
    rule['rule_id'] = input("Rule ID (e.g., LOAN_001): ").strip()
    rule['business_description'] = input("Business Description: ").strip()  
    rule['conditions'] = input("Conditions (business logic): ").strip()
    rule['actions'] = input("Actions (what happens): ").strip()
    
    # Domain selection
    domains = ['banking', 'insurance', 'healthcare', 'trading', 'government', 'ecommerce']
    print(f"Business Domain Options: {domains}")
    rule['business_domain'] = input("Business Domain: ").strip()
    
    # Priority selection  
    priorities = ['critical', 'high', 'medium', 'low']
    print(f"Priority Options: {priorities}")
    rule['priority'] = input("Priority: ").strip()
    
    # Optional fields
    source_lines = input("Source Lines (optional): ").strip()
    if source_lines:
        rule['source_lines'] = source_lines
        
    tech_impl = input("Technical Implementation (optional): ").strip() 
    if tech_impl:
        rule['technical_implementation'] = tech_impl
        
    compliance = input("Compliance Notes (optional): ").strip()
    if compliance:
        rule['compliance_notes'] = compliance
        
    # Dependencies
    deps = input("Dependencies (comma-separated, optional): ").strip()
    if deps:
        rule['dependencies'] = [d.strip() for d in deps.split(',')]
    
    return rule

def create_rule_json_file(file_path: str, schema_type: str = "basic"):
    """Create JSON file interactively"""
    
    print(f"🚀 Creating {schema_type} schema JSON file: {file_path}")
    print("=" * 50)
    
    rules = []
    
    while True:
        rule = create_basic_rule()
        rules.append(rule)
        
        continue_input = input("\nAdd another rule? (y/n): ").strip().lower()
        if continue_input != 'y':
            break
    
    # Save to file
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(rules, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Created {file_path} with {len(rules)} rules")
        print(f"📂 File ready for use with {'RuleDocumentationGeneratorAgent' if schema_type == 'basic' else 'AdvancedDocumentationAgent'}")
        
    except Exception as e:
        print(f"❌ Error saving file: {e}")

if __name__ == "__main__":
    print("🧰 Rule JSON Builder")
    print("=" * 30)
    
    file_path = input("Output file path: ").strip()
    if not file_path:
        file_path = "custom_rules.json"
        
    schema_type = input("Schema type (basic/advanced): ").strip()
    if schema_type not in ['basic', 'advanced']:
        schema_type = 'basic'
        
    create_rule_json_file(file_path, schema_type)
```

---

## 📚 **Sample Files Reference**

### **Available Sample Files**

| File | Purpose | Agent | Lines | Rules |
|------|---------|-------|-------|-------|
| `sample_extracted_rules.json` | Basic rule documentation | RuleDocumentationGeneratorAgent | 87 | 4 rules |
| `sample_advanced_rules.json` | Enterprise documentation | AdvancedDocumentationAgent | 156 | 2 rules |

### **Testing Your JSON Files**

```python
# Quick test your JSON file
import json
from pathlib import Path

def quick_test(json_file_path):
    """Quick validation test"""
    try:
        with open(json_file_path, 'r') as f:
            rules = json.load(f)
            
        print(f"✅ Loaded {len(rules)} rules from {Path(json_file_path).name}")
        
        # Show first rule summary  
        if rules:
            first_rule = rules[0]
            print(f"📋 Sample Rule: {first_rule.get('rule_id', 'No ID')}")
            print(f"🏢 Domain: {first_rule.get('business_domain', 'Unknown')}")
            print(f"⚡ Priority: {first_rule.get('priority', 'Unknown')}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

# Test your files
quick_test("Sample_Data_Files/sample_extracted_rules.json")
quick_test("Sample_Data_Files/sample_advanced_rules.json")
```

---

## ✅ **Best Practices**

### **JSON File Organization**

```
Sample_Data_Files/
├── rules/
│   ├── banking_rules.json           # Domain-specific rules
│   ├── insurance_rules.json         # Insurance business rules  
│   ├── healthcare_rules.json        # Healthcare compliance rules
│   └── government_rules.json        # Government regulation rules
├── advanced/
│   ├── enterprise_banking.json      # Enhanced banking rules
│   └── enterprise_insurance.json    # Enhanced insurance rules
└── templates/
    ├── basic_rule_template.json     # Empty template for basic rules
    └── advanced_rule_template.json  # Empty template for enhanced rules
```

### **Quality Guidelines**

✅ **DO:**
- Use descriptive, unique rule IDs
- Write business-friendly descriptions (avoid technical jargon)  
- Include clear conditions and actions
- Specify correct business domain
- Set appropriate priority levels
- Validate JSON syntax before use

❌ **AVOID:**
- Technical implementation details in business descriptions
- Empty or missing required fields
- Invalid domain or priority values  
- Malformed JSON syntax
- Duplicate rule IDs
- Vague or ambiguous rule descriptions

---

**✅ You're Ready!** 

Your JSON files are now properly formatted for the documentation agents. The platform will automatically generate professional business documentation from your structured rule data.

*Next: [Business Rule Extraction Guide](business-rule-extraction.md) to learn how to extract rules for documentation →*