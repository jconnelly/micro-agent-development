# Configuration Guide

Comprehensive configuration options for customizing the Micro-Agent Development Platform for your enterprise environment.

## 📁 Configuration Overview

The platform uses a hierarchical configuration system with graceful fallbacks:

1. **Environment Variables** (highest priority)
2. **YAML Configuration Files** (config/ directory)
3. **Hardcoded Defaults** (fallback if files missing)

```
config/
├── agent_defaults.yaml          # Agent timeouts, retries, cache settings
├── domains.yaml                 # Business domain classification
├── pii_patterns.yaml            # PII detection patterns and strategies
└── prompts/
    ├── extraction_prompts.yaml  # LLM prompts for rule extraction
    ├── documentation_prompts.yaml # LLM prompts for documentation
    └── triage_prompts.yaml      # LLM prompts for triage
```

## 🔧 Core Configuration

### Environment Variables

Set these in your `.env` file or system environment:

```bash
# API Configuration
GOOGLE_API_KEY=your_google_ai_api_key_here
ENVIRONMENT=production                    # development, testing, production
LOG_LEVEL=INFO                           # DEBUG, INFO, WARNING, ERROR

# Agent Configuration
DEFAULT_MODEL_NAME=gemini-1.5-flash      # Default LLM model
DEFAULT_LLM_PROVIDER=google              # LLM provider identifier
AUDIT_LEVEL=2                            # Default audit verbosity (1-4)

# Performance Configuration
MAX_CONCURRENT_REQUESTS=10               # API concurrency limit
API_TIMEOUT_SECONDS=30                   # Default API timeout
CACHE_SIZE_LIMIT=1000                    # LRU cache size limit

# File Processing
MAX_FILE_SIZE_MB=100                     # Maximum file size for processing
CHUNK_SIZE_LINES=175                     # Lines per chunk for large files
OVERLAP_SIZE_LINES=25                    # Overlap between chunks

# Security
ENABLE_PII_PROTECTION=true               # Global PII protection toggle
DEFAULT_MASKING_STRATEGY=PARTIAL_MASK    # PARTIAL_MASK, FULL_MASK, TOKENIZE, REDACT
```

### Agent Defaults Configuration

**File:** `config/agent_defaults.yaml`

```yaml
# Agent Default Configuration
# Production-ready settings with environment-specific overrides

# API Configuration
api:
  timeout_seconds: 30
  max_retries: 3
  retry_delay_seconds: 1.0
  backoff_factor: 2.0
  rate_limit_requests_per_minute: 60

# Cache Configuration
caching:
  enable_caching: true
  ip_address_cache_size: 100
  pii_detection_cache_size: 256
  file_context_cache_size: 128
  cache_ttl_seconds: 3600

# File Processing
file_processing:
  max_file_size_bytes: 104857600  # 100MB
  chunk_size_lines: 175
  overlap_size_lines: 25
  max_chunks_per_file: 50
  supported_encodings: ["utf-8", "utf-16", "iso-8859-1"]

# LLM Configuration
llm:
  default_model: "gemini-1.5-flash"
  default_provider: "google"
  temperature: 0.1
  max_tokens: 8192
  timeout_seconds: 30

# Audit Configuration
auditing:
  default_level: 2
  log_storage_path: "audit_logs.jsonl"
  max_log_file_size_mb: 100
  log_rotation_count: 5
  anonymize_sensitive_data: true

# Performance Thresholds
performance:
  large_file_threshold_lines: 1000
  high_volume_threshold_requests_per_hour: 1000
  memory_usage_warning_mb: 512
  processing_time_warning_seconds: 60

# Environment-specific overrides
environments:
  development:
    api:
      timeout_seconds: 60
      max_retries: 1
    auditing:
      default_level: 3
    caching:
      enable_caching: false

  testing:
    api:
      timeout_seconds: 10
      max_retries: 1
    file_processing:
      max_file_size_bytes: 10485760  # 10MB for testing
    auditing:
      default_level: 4

  production:
    api:
      timeout_seconds: 30
      max_retries: 3
    auditing:
      default_level: 2
    performance:
      memory_usage_warning_mb: 1024
```

## 🏢 Business Domain Configuration

**File:** `config/domains.yaml`

Customize business domain classification for your industry:

```yaml
# Business Domain Classification Configuration
# Add or modify domains based on your business context

domains:
  # Financial Services
  banking:
    keywords: [
      "account", "deposit", "balance", "transaction", "withdrawal", "overdraft",
      "fee", "branch", "atm", "wire transfer", "routing", "swift", "ach"
    ]
    weight: 1.0
    priority: high
    
  lending:
    keywords: [
      "loan", "credit score", "dti", "debt", "income", "collateral", "interest rate",
      "mortgage", "approval", "borrower", "refinance", "amortization", "origination"
    ]
    weight: 1.0
    priority: high

  trading:
    keywords: [
      "trade", "position", "margin", "leverage", "portfolio", "volatility", "order",
      "risk", "trader", "execution", "market", "liquidity", "hedge", "derivative"
    ]
    weight: 1.0
    priority: high

  insurance:
    keywords: [
      "policy", "premium", "coverage", "beneficiary", "accident", "smoker", "dui",
      "vehicle", "life insurance", "auto insurance", "claim", "deductible", "underwriting"
    ]
    weight: 1.0
    priority: high

  # Healthcare
  healthcare:
    keywords: [
      "patient", "diagnosis", "treatment", "medication", "doctor", "hospital",
      "medical", "prescription", "therapy", "clinic", "procedure", "hipaa"
    ]
    weight: 1.0
    priority: high

  # E-commerce & Retail
  ecommerce:
    keywords: [
      "order", "customer", "product", "payment", "shipping", "inventory",
      "cart", "checkout", "refund", "discount", "catalog", "sku"
    ]
    weight: 1.0
    priority: medium

  # Government & Public Sector
  government:
    keywords: [
      "citizen", "benefit", "eligibility", "tax", "license", "permit",
      "regulation", "compliance", "audit", "public service"
    ]
    weight: 1.0
    priority: medium

  # Technology
  technology:
    keywords: [
      "api", "database", "user", "authentication", "authorization", "security",
      "encryption", "backup", "system", "network", "server"
    ]
    weight: 0.8
    priority: low

# Custom domain for your organization
# Uncomment and modify as needed
# custom_domain:
#   keywords: ["your", "custom", "business", "terms"]
#   weight: 1.2
#   priority: high
#   description: "Custom domain specific to your organization"

# Domain classification settings
classification:
  minimum_confidence_threshold: 0.1
  multi_domain_threshold: 0.2
  max_keywords_per_domain: 20
  case_sensitive: false
```

## 🔒 PII Protection Configuration  

**File:** `config/pii_patterns.yaml`

Configure PII detection patterns and masking strategies:

```yaml
# PII Detection and Protection Configuration
# Customize patterns and strategies for your compliance requirements

# PII Type Definitions
pii_types:
  SSN:
    patterns:
      - '\b\d{3}-\d{2}-\d{4}\b'        # 123-45-6789
      - '\b\d{3}\s\d{2}\s\d{4}\b'      # 123 45 6789
      - '\b\d{9}\b'                     # 123456789
    description: "Social Security Number"
    priority: critical
    default_strategy: "FULL_MASK"

  CREDIT_CARD:
    patterns:
      - '\b4\d{3}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b'  # Visa
      - '\b5[1-5]\d{2}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b'  # MasterCard
      - '\b3[47]\d{2}[\s-]?\d{6}[\s-]?\d{5}\b'        # American Express
    description: "Credit Card Number"
    priority: critical
    default_strategy: "PARTIAL_MASK"

  EMAIL:
    patterns:
      - '\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    description: "Email Address"
    priority: high
    default_strategy: "PARTIAL_MASK"

  PHONE:
    patterns:
      - '\b(?:\+1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})\b'
      - '\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b'
    description: "Phone Number"
    priority: medium
    default_strategy: "PARTIAL_MASK"

  IP_ADDRESS:
    patterns:
      - '\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
    description: "IP Address"
    priority: medium
    default_strategy: "FULL_MASK"

# Masking Strategies Configuration
masking_strategies:
  PARTIAL_MASK:
    description: "Show first and last characters, mask middle"
    examples:
      email: "j***@example.com"
      ssn: "123-**-6789"
      credit_card: "4123 **** **** 6789"

  FULL_MASK:
    description: "Replace entire value with asterisks"
    mask_character: "*"
    preserve_length: true
    examples:
      email: "***************"
      ssn: "***-**-****"

  TOKENIZE:
    description: "Replace with reversible token"
    token_prefix: "TOKEN_"
    token_length: 8
    examples:
      email: "TOKEN_A7B8C9D1"
      ssn: "TOKEN_X1Y2Z3W4"

  REDACT:
    description: "Replace with descriptive placeholder"
    placeholders:
      email: "[EMAIL_REDACTED]"
      ssn: "[SSN_REDACTED]"
      credit_card: "[CARD_REDACTED]"
      phone: "[PHONE_REDACTED]"

# Context-specific configurations
contexts:
  FINANCIAL:
    priority_types: ["SSN", "CREDIT_CARD", "ACCOUNT_NUMBER", "ROUTING_NUMBER"]
    default_strategy: "TOKENIZE"
    require_full_audit: true
    compliance_frameworks: ["SOX", "PCI_DSS"]

  HEALTHCARE:
    priority_types: ["SSN", "MRN", "INSURANCE_ID", "DOB"]
    default_strategy: "FULL_MASK"
    require_full_audit: true
    compliance_frameworks: ["HIPAA"]

  LEGAL:
    priority_types: ["SSN", "CASE_NUMBER", "BAR_NUMBER"]
    default_strategy: "REDACT"
    require_full_audit: true
    compliance_frameworks: ["CLIENT_PRIVILEGE"]

  GOVERNMENT:
    priority_types: ["SSN", "EMPLOYEE_ID", "SECURITY_CLEARANCE"]
    default_strategy: "FULL_MASK"
    require_full_audit: true
    compliance_frameworks: ["FISMA"]

  GENERAL:
    priority_types: ["EMAIL", "PHONE", "IP_ADDRESS"]
    default_strategy: "PARTIAL_MASK"
    require_full_audit: false
    compliance_frameworks: ["GDPR", "CCPA"]

# Performance and Detection Settings
detection:
  case_sensitive: false
  multiline_support: true
  max_pattern_length: 500
  confidence_threshold: 0.8
  enable_context_analysis: true
  cache_compiled_patterns: true
```

## 📝 LLM Prompts Configuration

### Extraction Prompts

**File:** `config/prompts/extraction_prompts.yaml`

```yaml
# LLM Prompts for Business Rule Extraction
# Customize prompts for different domains and use cases

system_prompts:
  default: |
    You are an expert business rule extraction and translation agent.
    Your task is to analyze legacy code snippets, identify embedded business rules,
    separate them from technical implementation details, and translate any cryptic
    technical terminology into clear, business-friendly language.
    Output the extracted rules in a structured JSON array format.

  financial: |
    You are a financial services business analyst specializing in regulatory
    compliance and business rule extraction. Focus on identifying rules related to
    risk management, compliance requirements, and financial calculations.
    Pay special attention to regulatory requirements and audit trail needs.

  healthcare: |
    You are a healthcare IT specialist focused on clinical workflow and compliance
    rules. Identify rules related to patient care protocols, HIPAA compliance,
    and medical decision support. Ensure all extracted rules maintain patient
    privacy and clinical accuracy.

user_prompt_templates:
  code_analysis: |
    Analyze the following {language} code snippet and extract all explicit and implicit
    business rules. For each rule, provide:
    - Clear business description
    - Conditions and actions
    - Source code lines
    - Business domain classification
    
    Context: {context}
    
    Code:
    ```{language}
    {code_snippet}
    ```

  domain_specific: |
    Extract business rules from this {domain} system code, focusing on:
    - {domain_specific_concerns}
    - Regulatory compliance requirements
    - Business process workflows
    - Risk management rules
    
    Context: {context}
    Code: {code_snippet}

# Output format specifications
output_formats:
  structured_json:
    schema_version: "1.0"
    required_fields:
      - rule_id
      - business_description
      - conditions
      - actions
      - source_lines
      - business_domain
      - priority
    optional_fields:
      - technical_implementation
      - compliance_notes
      - dependencies

# Domain-specific prompt variations
domain_variations:
  financial_services:
    focus_areas: ["risk_management", "regulatory_compliance", "audit_requirements"]
    terminology_map:
      "dti": "debt-to-income ratio"
      "ltv": "loan-to-value ratio"
      "fico": "credit score"

  healthcare:
    focus_areas: ["patient_safety", "hipaa_compliance", "clinical_workflows"]
    terminology_map:
      "mrn": "medical record number"
      "icd": "diagnostic code"
      "cpt": "procedure code"
```

## ⚙️ Advanced Configuration

### Custom Agent Configuration

Create agent-specific configurations:

```yaml
# config/agents/business_rule_extraction.yaml
agent_specific:
  BusinessRuleExtractionAgent:
    chunking:
      chunk_size_lines: 200
      overlap_size_lines: 30
      max_chunks: 100
    
    processing:
      enable_smart_boundaries: true
      context_extraction_lines: 50
      progress_reporting: true
    
    llm:
      temperature: 0.05  # Lower for more consistent extraction
      response_format: "json"
      retry_on_parse_error: true
```

### Environment-Specific Overrides

Use environment variables to override YAML settings:

```bash
# Override agent defaults
export AGENT_API_TIMEOUT=60
export AGENT_MAX_RETRIES=5
export AGENT_CACHE_SIZE=512

# Override PII settings
export PII_DEFAULT_STRATEGY=TOKENIZE
export PII_ENABLE_CACHING=true

# Override domain classification
export DOMAIN_MIN_CONFIDENCE=0.2
export DOMAIN_MAX_KEYWORDS=30
```

### Docker Configuration

**docker-compose.yml:**

```yaml
version: '3.8'

services:
  micro-agent-platform:
    build: .
    environment:
      - GOOGLE_API_KEY=${GOOGLE_API_KEY}
      - ENVIRONMENT=production
      - LOG_LEVEL=INFO
      - AGENT_API_TIMEOUT=30
      - AUDIT_LEVEL=2
    volumes:
      - ./config:/app/config:ro
      - ./data:/app/data
      - ./logs:/app/logs
    ports:
      - "8000:8000"
    restart: unless-stopped
```

## 🔍 Configuration Validation

Create a configuration validator script:

```python
#!/usr/bin/env python3
"""Configuration validation script"""

import yaml
from pathlib import Path
from Utils import config_loader

def validate_configuration():
    """Validate all configuration files"""
    config_dir = Path("config")
    
    # Check required files
    required_files = [
        "agent_defaults.yaml",
        "domains.yaml", 
        "pii_patterns.yaml"
    ]
    
    for file_name in required_files:
        file_path = config_dir / file_name
        if not file_path.exists():
            print(f"⚠️  Warning: {file_name} not found, using defaults")
            continue
            
        try:
            config = config_loader.load_config(file_name.replace('.yaml', ''))
            print(f"✅ {file_name}: Valid")
        except Exception as e:
            print(f"❌ {file_name}: Invalid - {e}")

if __name__ == "__main__":
    validate_configuration()
```

## 🚀 Production Configuration

### Recommended Production Settings

```yaml
# config/production.yaml
production:
  api:
    timeout_seconds: 30
    max_retries: 3
    rate_limit_requests_per_minute: 100
    
  security:
    enable_api_key_validation: true
    log_sensitive_data: false
    encrypt_audit_logs: true
    
  performance:
    enable_caching: true
    cache_size_limit: 2000
    memory_limit_mb: 2048
    
  monitoring:
    enable_metrics: true
    metrics_endpoint: "/metrics"
    health_check_endpoint: "/health"
```

### Load Testing Configuration

For high-volume environments:

```yaml
# config/high_performance.yaml
high_performance:
  concurrency:
    max_concurrent_requests: 50
    thread_pool_size: 20
    connection_pool_size: 100
    
  caching:
    redis_url: "redis://localhost:6379"
    cache_ttl_seconds: 7200
    enable_distributed_cache: true
```

## 📊 Monitoring Configuration

### Logging Configuration

```yaml
# config/logging.yaml
logging:
  version: 1
  disable_existing_loggers: false
  
  formatters:
    standard:
      format: "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    
    json:
      format: |
        {
          "timestamp": "%(asctime)s",
          "level": "%(levelname)s",
          "logger": "%(name)s", 
          "message": "%(message)s",
          "request_id": "%(request_id)s"
        }
  
  handlers:
    console:
      class: logging.StreamHandler
      formatter: standard
      level: INFO
      
    file:
      class: logging.handlers.RotatingFileHandler
      filename: logs/platform.log
      formatter: json
      maxBytes: 10485760  # 10MB
      backupCount: 5
  
  loggers:
    Agents:
      level: INFO
      handlers: [console, file]
      propagate: false
```

---

**✅ Configuration Complete!**

Your platform is now configured for your specific environment and use cases.

*Next: [User Guides](../guides/business-rule-extraction.md) to learn how to use each agent →*