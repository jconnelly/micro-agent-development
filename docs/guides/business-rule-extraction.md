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

## 📁 Supported File Formats & Extensions

The BusinessRuleExtractionAgent supports a wide range of legacy file formats. Here are the **recommended file extensions** and what to expect:

### ✅ **Fully Supported Formats**

| Extension | Language/System | Example Use Cases | Processing Notes |
|-----------|----------------|------------------|------------------|
| **`.cbl`, `.cob`, `.cobol`** | COBOL | Mainframe banking, insurance, government systems | Excellent rule extraction from paragraphs and IF statements |
| **`.java`, `.jsp`** | Java/J2EE | Enterprise web applications, business logic | Strong support for business methods and validation rules |
| **`.cpp`, `.cc`, `.c`** | C/C++ | Financial calculations, trading systems, embedded systems | Good for algorithmic business rules and calculations |
| **`.pl`, `.pm`** | Perl | Legacy data processing, text manipulation, integration scripts | Effective for data transformation rules |
| **`.rb`** | Ruby | Web applications, business rule engines | Good support for Rails models and business logic |
| **`.sql`, `.plsql`** | SQL/PL-SQL | Database stored procedures, business logic in DB | Excellent for data validation and business constraint rules |
| **`.vb`, `.vba`** | Visual Basic | Desktop applications, Office macros, legacy systems | Strong support for business validation and workflow rules |
| **`.cs`** | C# | .NET enterprise applications, business services | Good extraction from business layer classes |
| **`.py`** | Python | Business applications, data processing, automation | Effective for business logic and rule-based systems |
| **`.xml`** | XML Config | Business rule configurations, workflow definitions | Good for declarative rule extraction |

### 🔧 **Specialized Legacy Formats**

| Extension | System | Description | Sample Available |
|-----------|--------|-------------|------------------|
| **`.clp`** | CLIPS | Expert systems, rule-based AI | ✅ `sample_legacy_banking.clp` |
| **`.drl`** | Drools | Business rule management systems | ✅ `sample_legacy_insurance.drl` |
| **`.mumps`, `.m`** | MUMPS/M | Healthcare systems, medical databases | ✅ `sample_legacy_healthcare.mumps` |
| **`.pas`** | Pascal/Delphi | Legacy manufacturing, scientific applications | ✅ `sample_legacy_manufacturing.pas` |
| **`.bpmn`** | BPMN | Business process workflows | ✅ `sample_legacy_workflow.bpmn` |
| **`.4gl`** | 4GL Systems | Legacy database applications | Contact support for specific 4GL dialects |
| **`.natural`** | Natural/ADABAS | Mainframe database applications | Processing available on request |

### 📋 **What to Prepare Before Processing**

#### **File Content Requirements**
```
✅ DO include:
- Complete business logic functions/methods
- Validation rules and conditional statements  
- Business calculations and algorithms
- Workflow decision points
- Data validation logic
- Approval/rejection criteria

❌ AVOID:
- Pure technical setup code (imports, includes)
- Database connection logic only
- UI/presentation layer code without business rules
- Empty files or comment-only files
- Binary files or compiled code
```

#### **Optimal File Size Guidelines**
- **Small files (< 175 lines)**: Processed in single pass - fastest
- **Medium files (175-1000 lines)**: Automatic chunking with context preservation  
- **Large files (1000+ lines)**: Intelligent chunking with progress tracking
- **Maximum recommended**: 10MB per file for optimal performance

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

## 📚 **Practical Examples with Sample Files**

The platform includes comprehensive sample files you can use to test and learn. All samples are located in `Sample_Data_Files/`:

### 🏦 **COBOL Insurance System Example**

**File:** `Sample_Data_Files/sample_legacy_insurance.cbl`
**Use Case:** Insurance policy validation and premium calculation

```python
# Process real COBOL insurance system
with open("Sample_Data_Files/sample_legacy_insurance.cbl", "r") as f:
    cobol_insurance = f.read()

result = extractor.extract_and_translate_rules(
    legacy_code_snippet=cobol_insurance,
    context="""
    Legacy mainframe insurance system from 1985.
    Handles policy validation for auto, life, and home insurance.
    Contains business rules for eligibility, risk assessment, and premium calculation.
    Must comply with state insurance regulations.
    """,
    audit_level=2
)

print(f"✅ Extracted {len(result['extracted_rules'])} business rules from COBOL:")
for rule in result['extracted_rules'][:3]:  # Show first 3
    print(f"  📋 {rule['rule_id']}: {rule['business_description']}")
```

**Expected Output:**
```
✅ Extracted 15 business rules from COBOL:
  📋 RULE_001: Minimum Age Eligibility - Applicants must be at least 18 years old for any insurance policy
  📋 RULE_002: Auto Insurance Age Limit - Auto insurance applicants cannot exceed 80 years of age
  📋 RULE_003: Credit Score Requirement - Minimum credit score of 600 required for policy approval
```

### 🏥 **MUMPS Healthcare System Example**

**File:** `Sample_Data_Files/sample_legacy_healthcare.mumps`
**Use Case:** Medical record processing and patient care protocols

```python
# Process MUMPS healthcare system
with open("Sample_Data_Files/sample_legacy_healthcare.mumps", "r") as f:
    mumps_healthcare = f.read()

result = extractor.extract_and_translate_rules(
    legacy_code_snippet=mumps_healthcare,
    context="""
    Legacy MUMPS/M healthcare system for patient record management.
    Contains clinical decision support rules, medication protocols, and HIPAA compliance logic.
    Used in hospital setting for patient care coordination.
    """,
    audit_level=2
)
```

### 🏭 **Pascal Manufacturing System Example**

**File:** `Sample_Data_Files/sample_legacy_manufacturing.pas`
**Use Case:** Quality control and production rules

```python
# Process Pascal manufacturing system
with open("Sample_Data_Files/sample_legacy_manufacturing.pas", "r") as f:
    pascal_manufacturing = f.read()

result = extractor.extract_and_translate_rules(
    legacy_code_snippet=pascal_manufacturing,
    context="""
    Legacy Pascal system for manufacturing quality control.
    Implements production rules, safety protocols, and quality assurance checks.
    Used in automotive parts manufacturing facility.
    """,
    audit_level=2
)
```

### 🔄 **BPMN Business Process Example**

**File:** `Sample_Data_Files/sample_legacy_workflow.bpmn`
**Use Case:** Business process workflows and decision points

```python
# Process BPMN workflow definitions
with open("Sample_Data_Files/sample_legacy_workflow.bpmn", "r") as f:
    bpmn_workflow = f.read()

result = extractor.extract_and_translate_rules(
    legacy_code_snippet=bpmn_workflow,
    context="""
    BPMN workflow definition for loan approval process.
    Contains business process rules, decision gateways, and approval workflows.
    Used for automated loan processing and manual review triggers.
    """,
    audit_level=2
)
```

### 💰 **C++ Trading System Example**

**File:** `Sample_Data_Files/sample_legacy_trading.cpp`
**Use Case:** Financial trading rules and risk management

```python
# Process C++ trading system
with open("Sample_Data_Files/sample_legacy_trading.cpp", "r") as f:
    cpp_trading = f.read()

result = extractor.extract_and_translate_rules(
    legacy_code_snippet=cpp_trading,
    context="""
    Legacy C++ high-frequency trading system.
    Contains risk management rules, position limits, and trading algorithms.
    Must comply with financial regulations and risk management policies.
    """,
    audit_level=2
)
```

### 🧠 **CLIPS Expert System Example**

**File:** `Sample_Data_Files/sample_legacy_banking.clp`
**Use Case:** Expert system rules for banking decisions

```python
# Process CLIPS expert system
with open("Sample_Data_Files/sample_legacy_banking.clp", "r") as f:
    clips_banking = f.read()

result = extractor.extract_and_translate_rules(
    legacy_code_snippet=clips_banking,
    context="""
    CLIPS expert system for banking loan decisions.
    Rule-based system for credit evaluation and loan approval.
    Implements complex business logic for financial risk assessment.
    """,
    audit_level=2
)
```

## 🎯 **File Processing Workflow**

### **Step 1: File Preparation**
```python
def prepare_file_for_extraction(file_path, encoding='utf-8'):
    """Prepare legacy file for business rule extraction"""
    try:
        with open(file_path, 'r', encoding=encoding) as f:
            content = f.read()
        
        # Basic validation
        if len(content.strip()) == 0:
            raise ValueError("File is empty")
            
        if len(content) > 10 * 1024 * 1024:  # 10MB
            print("⚠️  Warning: Large file detected. Processing may take time.")
            
        return content, len(content.splitlines())
        
    except UnicodeDecodeError:
        # Try alternative encodings
        for alt_encoding in ['latin-1', 'cp1252', 'iso-8859-1']:
            try:
                with open(file_path, 'r', encoding=alt_encoding) as f:
                    content = f.read()
                print(f"✅ File read using {alt_encoding} encoding")
                return content, len(content.splitlines())
            except UnicodeDecodeError:
                continue
        raise ValueError(f"Unable to decode file {file_path}")

# Example usage
content, line_count = prepare_file_for_extraction("Sample_Data_Files/sample_legacy_insurance.cbl")
print(f"📄 Loaded {line_count} lines from COBOL insurance system")
```

### **Step 2: Context Preparation**
```python
def generate_context_for_file(file_path, business_domain=None):
    """Generate appropriate context based on file characteristics"""
    
    file_ext = Path(file_path).suffix.lower()
    file_name = Path(file_path).stem
    
    # Domain detection from filename
    domain_keywords = {
        'insurance': ['insurance', 'policy', 'claim', 'premium'],
        'banking': ['banking', 'loan', 'credit', 'account'], 
        'trading': ['trading', 'market', 'position', 'risk'],
        'healthcare': ['healthcare', 'medical', 'patient', 'clinical'],
        'manufacturing': ['manufacturing', 'production', 'quality']
    }
    
    detected_domain = business_domain
    if not detected_domain:
        for domain, keywords in domain_keywords.items():
            if any(keyword in file_name.lower() for keyword in keywords):
                detected_domain = domain
                break
    
    # Extension-specific context
    ext_contexts = {
        '.cbl': f"Legacy COBOL mainframe system",
        '.cpp': f"C++ high-performance system", 
        '.java': f"Java enterprise application",
        '.mumps': f"MUMPS/M healthcare database system",
        '.pas': f"Pascal/Delphi legacy application",
        '.clp': f"CLIPS expert system with rule-based logic",
        '.drl': f"Drools business rule management system"
    }
    
    base_context = ext_contexts.get(file_ext, "Legacy business system")
    
    if detected_domain:
        domain_contexts = {
            'insurance': "for insurance policy processing and risk assessment",
            'banking': "for banking operations and financial services",  
            'trading': "for financial trading and risk management",
            'healthcare': "for patient care and medical record management",
            'manufacturing': "for production control and quality assurance"
        }
        base_context += f" {domain_contexts.get(detected_domain, '')}"
    
    return f"{base_context}. Contains embedded business rules and decision logic."

# Example usage  
context = generate_context_for_file("Sample_Data_Files/sample_legacy_insurance.cbl")
print(f"📋 Generated context: {context}")
```

### **Step 3: Batch Processing Multiple Files**
```python
def batch_extract_rules(sample_directory="Sample_Data_Files", file_patterns=None):
    """Process multiple sample files in batch"""
    
    if file_patterns is None:
        file_patterns = ["*.cbl", "*.java", "*.cpp", "*.mumps", "*.pas", "*.clp", "*.drl"]
    
    sample_files = []
    for pattern in file_patterns:
        sample_files.extend(Path(sample_directory).glob(pattern))
    
    results = {}
    
    for file_path in sample_files:
        print(f"\n🔍 Processing {file_path.name}...")
        
        try:
            content, line_count = prepare_file_for_extraction(str(file_path))
            context = generate_context_for_file(str(file_path))
            
            result = extractor.extract_and_translate_rules(
                legacy_code_snippet=content,
                context=context,
                audit_level=1  # Minimal audit for batch processing
            )
            
            results[file_path.name] = {
                'rules_extracted': len(result['extracted_rules']),
                'file_size_lines': line_count,
                'status': 'success',
                'rules': result['extracted_rules']
            }
            
            print(f"✅ {file_path.name}: {len(result['extracted_rules'])} rules extracted")
            
        except Exception as e:
            results[file_path.name] = {
                'rules_extracted': 0,
                'file_size_lines': 0,
                'status': 'failed', 
                'error': str(e)
            }
            print(f"❌ {file_path.name}: Failed - {e}")
    
    return results

# Run batch processing
batch_results = batch_extract_rules()

# Summary
total_rules = sum(r['rules_extracted'] for r in batch_results.values())
successful_files = sum(1 for r in batch_results.values() if r['status'] == 'success')
print(f"\n📊 Batch Summary: {total_rules} rules from {successful_files} files")
```

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