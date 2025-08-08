# Business Rule Extraction Guide

Learn how to extract and translate business rules from legacy systems using the BusinessRuleExtractionAgent.

## 🎯 Overview

The BusinessRuleExtractionAgent is designed to analyze legacy code and automatically extract embedded business rules, translating technical implementations into clear, business-friendly documentation. This is essential for:

- **Digital Transformation**: Modernizing legacy systems while preserving business logic
- **Regulatory Compliance**: Documenting business rules for audit and governance requirements  
- **Knowledge Transfer**: Converting tribal knowledge into documented processes
- **System Migration**: Ensuring business rules are preserved during technology upgrades

## 🚀 Quick Start

### Basic Usage

```python
import os
import google.generativeai as genai
from Agents.BusinessRuleExtractionAgent import BusinessRuleExtractionAgent
from Agents.ComplianceMonitoringAgent import ComplianceMonitoringAgent

# Configure LLM
genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))
llm_client = genai.GenerativeModel('gemini-1.5-flash')

# Initialize agents
audit_system = ComplianceMonitoringAgent()
extractor = BusinessRuleExtractionAgent(
    llm_client=llm_client,
    audit_system=audit_system,
    model_name="gemini-1.5-flash",
    log_level=1  # Verbose logging for development
)

# Extract rules from legacy code
legacy_code = """
// Loan approval logic from legacy banking system
if (applicant.creditScore >= 650 && 
    applicant.debtToIncomeRatio <= 0.43 &&
    applicant.hasVerifiedIncome == true) {
    
    if (loanAmount <= applicant.maxLoanAmount) {
        approveLoan(applicant, loanAmount);
        logAuditEvent("LOAN_APPROVED", applicant.id);
    } else {
        rejectLoan(applicant, "AMOUNT_EXCEEDS_LIMIT");
    }
} else {
    rejectLoan(applicant, "CREDIT_REQUIREMENTS_NOT_MET");
}
"""

result = extractor.extract_and_translate_rules(
    legacy_code_snippet=legacy_code,
    context="Legacy banking loan origination system",
    audit_level=2  # Full audit trail
)

# Display extracted rules
print(f"✅ Extracted {len(result['extracted_rules'])} business rules:")
for rule in result['extracted_rules']:
    print(f"\n📋 {rule['rule_id']}: {rule['business_description']}")
    print(f"   Conditions: {rule['conditions']}")
    print(f"   Actions: {rule['actions']}")
```

### Expected Output

```
✅ Extracted 3 business rules:

📋 RULE_001: Loan Eligibility Requirements
   Conditions: Credit score must be 650 or higher AND debt-to-income ratio must be 43% or lower AND applicant must have verified income
   Actions: Qualify applicant for loan processing

📋 RULE_002: Loan Amount Validation
   Conditions: Requested loan amount is within applicant's maximum loan limit
   Actions: Approve loan and create audit log entry

📋 RULE_003: Credit Requirements Rejection
   Conditions: Credit score below 650 OR debt-to-income ratio above 43% OR unverified income
   Actions: Reject loan application with reason code
```

## 🏢 Supported Legacy Systems

The agent is trained to handle multiple legacy technologies:

### Programming Languages

=== "COBOL"
    
    **Use Case:** Mainframe banking and insurance systems
    
    ```python
    cobol_code = """
    IF WS-CREDIT-SCORE >= 650
       AND WS-DTI-RATIO <= 43
       MOVE 'APPROVED' TO WS-LOAN-STATUS
       PERFORM 9000-AUDIT-APPROVAL
    ELSE
       MOVE 'REJECTED' TO WS-LOAN-STATUS
       PERFORM 9100-AUDIT-REJECTION
    END-IF.
    """
    
    result = extractor.extract_and_translate_rules(
        legacy_code_snippet=cobol_code,
        context="COBOL mainframe loan processing system"
    )
    ```

=== "Java"
    
    **Use Case:** Enterprise web applications and services
    
    ```python
    java_code = """
    public class InsurancePolicyValidator {
        public boolean validatePolicy(Policy policy) {
            if (policy.getApplicantAge() < 18) {
                return false; // Minors cannot purchase insurance
            }
            
            if (policy.getType() == PolicyType.LIFE && 
                policy.getApplicantAge() > 75) {
                return false; // Life insurance age limit
            }
            
            return true;
        }
    }
    """
    
    result = extractor.extract_and_translate_rules(
        legacy_code_snippet=java_code,
        context="Java insurance policy validation system"
    )
    ```

=== "C/C++"
    
    **Use Case:** Financial calculations and trading systems
    
    ```python
    cpp_code = """
    double calculateInterestRate(Customer customer, LoanType type) {
        double baseRate = 3.5;
        
        if (customer.creditScore >= 800) {
            baseRate -= 0.5; // Premium customer discount
        } else if (customer.creditScore < 600) {
            baseRate += 1.0; // Higher risk surcharge
        }
        
        if (type == MORTGAGE && customer.isFirstTime) {
            baseRate -= 0.25; // First-time buyer incentive
        }
        
        return baseRate;
    }
    """
    
    result = extractor.extract_and_translate_rules(
        legacy_code_snippet=cpp_code,
        context="C++ financial interest rate calculation engine"
    )
    ```

=== "PL/SQL"
    
    **Use Case:** Database stored procedures and business logic
    
    ```python
    plsql_code = """
    CREATE OR REPLACE PROCEDURE process_claim(
        p_claim_id IN NUMBER,
        p_amount IN NUMBER
    ) AS
    BEGIN
        IF p_amount > 10000 THEN
            -- High-value claims require manager approval
            UPDATE claims 
            SET status = 'PENDING_MANAGER_APPROVAL'
            WHERE claim_id = p_claim_id;
        ELSE
            -- Auto-approve small claims
            UPDATE claims 
            SET status = 'APPROVED'
            WHERE claim_id = p_claim_id;
        END IF;
    END;
    """
    
    result = extractor.extract_and_translate_rules(
        legacy_code_snippet=plsql_code,
        context="Oracle PL/SQL insurance claims processing"
    )
    ```

## 📊 Large File Processing

The agent automatically handles large legacy files using intelligent chunking:

### Automatic Chunking

For files larger than 175 lines, the agent:

1. **Extracts Context**: Preserves imports, headers, and key declarations
2. **Smart Boundaries**: Splits at logical points (functions, classes, rules)
3. **Overlapping Chunks**: Maintains context between chunks
4. **Progress Tracking**: Shows real-time processing status
5. **Rule Deduplication**: Removes duplicate rules across chunks

```python
# Process large legacy file
with open("legacy_banking_system.cobol", "r") as f:
    large_cobol_file = f.read()  # 2000+ lines

print(f"Processing {len(large_cobol_file.splitlines())} lines...")

result = extractor.extract_and_translate_rules(
    legacy_code_snippet=large_cobol_file,
    context="Large COBOL banking mainframe system",
    audit_level=2
)

# Output shows chunking progress:
# Processing chunk 1/12 (8.3% complete)
# Processing chunk 2/12 (16.7% complete)
# ...
# Processing complete! Total rules extracted: 47
```

### Performance Optimization

The agent includes several performance optimizations:

- **Pre-compiled Regex**: 30-50% faster pattern matching
- **LRU Caching**: 3.8x speedup for repeated file processing  
- **Set Operations**: O(1) lookups instead of O(n) searches
- **Smart Chunking**: Minimizes API calls while preserving context

## 🎯 Domain-Specific Extraction

The agent automatically classifies business domains and adapts extraction accordingly:

### Supported Domains

| Domain | Keywords | Specialization |
|--------|----------|----------------|
| **Banking** | account, deposit, withdrawal, balance | Financial operations and compliance |
| **Insurance** | policy, premium, claim, coverage | Underwriting and claims processing |
| **Trading** | position, margin, order, risk | Risk management and trading rules |
| **Healthcare** | patient, diagnosis, treatment, hipaa | Clinical workflows and HIPAA compliance |
| **E-commerce** | order, customer, payment, inventory | Customer experience and fulfillment |
| **Government** | citizen, benefit, eligibility, tax | Public service and regulatory rules |

### Domain-Specific Example

```python
# Insurance domain extraction
insurance_code = """
if (applicant.age < 18) {
    reject("MINOR_NOT_ELIGIBLE");
} else if (applicant.hasPreExistingCondition && 
           !applicant.hasWaiver) {
    requireMedicalExam();
} else if (applicant.isSmoker) {
    premiumMultiplier = 1.5;
}
"""

result = extractor.extract_and_translate_rules(
    legacy_code_snippet=insurance_code,
    context="Insurance underwriting system"
)

# Agent automatically detects 'insurance' domain and applies specialized processing
# Extracts rules with insurance-specific terminology and compliance considerations
```

## 🔧 Advanced Configuration

### Custom Processing Options

```python
# Initialize with custom configuration
extractor = BusinessRuleExtractionAgent(
    llm_client=llm_client,
    audit_system=audit_system,
    model_name="gemini-2.0-flash",  # Use more advanced model
    log_level=0,  # Production mode (silent)
    agent_id="rule_extractor_prod_v1"  # Custom identifier
)

# Advanced extraction with detailed context
result = extractor.extract_and_translate_rules(
    legacy_code_snippet=complex_legacy_system,
    context="""
    Legacy COBOL mainframe system for loan origination at regional bank.
    Processes 10,000+ loan applications daily.
    Must comply with federal lending regulations including:
    - Equal Credit Opportunity Act (ECOA)  
    - Truth in Lending Act (TILA)
    - Fair Credit Reporting Act (FCRA)
    Critical business rules relate to:
    - Credit decisioning algorithms
    - Interest rate calculations
    - Regulatory compliance checks
    - Audit trail requirements
    """,
    audit_level=1  # Full regulatory audit trail
)
```

### Error Handling and Recovery

The agent includes comprehensive error handling:

```python
try:
    result = extractor.extract_and_translate_rules(
        legacy_code_snippet=potentially_problematic_code,
        context="Legacy system with encoding issues",
        audit_level=2
    )
    
    if result['extracted_rules']:
        print(f"✅ Successfully extracted {len(result['extracted_rules'])} rules")
    else:
        print("⚠️  No business rules found in the provided code")
        
except Exception as e:
    print(f"❌ Extraction failed: {e}")
    # Check audit logs for detailed error information
    audit_log = result.get('audit_log', {})
    if audit_log.get('error_details'):
        print(f"Error details: {audit_log['error_details']}")
```

## 📈 Output Analysis

### Rule Quality Assessment

Each extracted rule includes quality indicators:

```python
for rule in result['extracted_rules']:
    print(f"Rule: {rule['rule_id']}")
    print(f"  Business Description: {rule['business_description']}")
    print(f"  Domain: {rule.get('business_domain', 'general')}")
    print(f"  Priority: {rule.get('priority', 'medium')}")
    print(f"  Source: {rule.get('source_lines', 'unknown')}")
    
    # Quality indicators
    if rule.get('compliance_notes'):
        print(f"  📋 Compliance: {rule['compliance_notes']}")
    if rule.get('technical_implementation'):
        print(f"  🔧 Technical: {rule['technical_implementation']}")
```

### Business Rule Documentation

The extracted rules are ready for business documentation:

```python
# Convert to business documentation
from Agents.RuleDocumentationGeneratorAgent import RuleDocumentationGeneratorAgent

doc_generator = RuleDocumentationGeneratorAgent(
    llm_client=llm_client,
    audit_system=audit_system
)

documentation = doc_generator.document_and_visualize_rules(
    extracted_rules=result['extracted_rules'],
    output_format="markdown"
)

# Save business-ready documentation
with open("business_rules_documentation.md", "w") as f:
    f.write(documentation['generated_documentation'])

print("📄 Business documentation generated: business_rules_documentation.md")
```

## 🎯 Best Practices

### 1. Provide Rich Context

```python
# Good: Detailed context
context = """
Legacy inventory management system for automotive parts distributor.
Handles 50,000+ SKUs across 200 locations.
Critical business rules for:
- Reorder point calculations
- Seasonal demand adjustments  
- Supplier lead time management
- Emergency stock procedures
"""

# Avoid: Minimal context
context = "Inventory system"
```

### 2. Process in Logical Units

```python
# Good: Process complete business modules
module_code = get_complete_pricing_module()  # Complete pricing logic

# Avoid: Random code fragments
random_snippet = legacy_code[1000:2000]  # Arbitrary slice
```

### 3. Use Appropriate Audit Levels

```python
# Development and testing
audit_level = 3  # Detailed logging for debugging

# Production processing
audit_level = 2  # Standard audit trail  

# High-volume batch processing
audit_level = 1  # Minimal but compliant logging
```

### 4. Handle Large Files Efficiently

```python
# For very large files, consider preprocessing
def preprocess_large_file(file_content):
    """Remove comments and whitespace to focus on business logic"""
    lines = file_content.splitlines()
    
    # Remove pure comment lines and empty lines
    business_lines = [
        line for line in lines 
        if line.strip() and not line.strip().startswith(('*', '//', '#'))
    ]
    
    return '\n'.join(business_lines)

processed_code = preprocess_large_file(large_legacy_file)
result = extractor.extract_and_translate_rules(
    legacy_code_snippet=processed_code,
    context="Preprocessed legacy system focusing on business logic"
)
```

## 🔍 Troubleshooting

### Common Issues

!!! error "No Rules Extracted"
    
    **Cause:** Code contains only technical implementation without clear business logic
    
    **Solutions:**
    - Provide more context about business purpose
    - Include complete business modules rather than fragments
    - Try different sections of the codebase with clearer business rules

!!! error "Rules Too Technical"
    
    **Cause:** Agent extracting implementation details instead of business rules
    
    **Solutions:**
    - Enhance context with business domain information
    - Specify the business purpose of the system
    - Use domain-specific keywords in context

!!! error "Processing Timeout"
    
    **Cause:** Large file taking too long to process
    
    **Solutions:**
    - Break large files into smaller logical modules
    - Increase API timeout in configuration
    - Use preprocessing to focus on business logic sections

### Performance Optimization

```python
# Monitor performance
import time

start_time = time.time()
result = extractor.extract_and_translate_rules(
    legacy_code_snippet=code,
    context=context,
    audit_level=2
)
processing_time = time.time() - start_time

print(f"Processing completed in {processing_time:.2f} seconds")
print(f"Rules extracted: {len(result['extracted_rules'])}")
print(f"Rate: {len(result['extracted_rules'])/processing_time:.1f} rules/second")
```

---

**✅ You're Ready!**

You now have the knowledge to extract business rules from any legacy system. The BusinessRuleExtractionAgent will help you modernize your legacy systems while preserving critical business logic.

*Next: [Personal Data Protection Guide](personal-data-protection.md) to learn about PII compliance →*