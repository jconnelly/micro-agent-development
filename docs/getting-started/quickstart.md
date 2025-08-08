# Quick Start Guide

Get up and running with the Micro-Agent Development Platform in under 5 minutes.

## 🚀 Prerequisites

Before you begin, ensure you have:

- **Python 3.9+** installed on your system
- **Git** for repository cloning
- **LLM API key** - Choose from:
  - **Google Gemini** ([Get key](https://makersuite.google.com/app/apikey)) - Default, free tier available
  - **OpenAI GPT** ([Get key](https://platform.openai.com/api-keys)) - Premium models
  - **Anthropic Claude** ([Get key](https://console.anthropic.com/)) - Advanced reasoning
  - **Azure OpenAI** - Enterprise deployment
- **Basic Python knowledge** for configuration and usage

## ⚡ 5-Minute Setup

### Step 1: Clone and Install

```bash
# Clone the repository
git clone https://github.com/jconnelly/micro-agent-development.git
cd micro-agent-development

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configure API Access

```bash
# Set your Google AI API key (replace with your actual key)
export GOOGLE_API_KEY="your_api_key_here"

# On Windows:
set GOOGLE_API_KEY=your_api_key_here
```

### Step 3: Quick Test - Business Rule Extraction

Create a test file `quick_test.py`:

```python
import os
import google.generativeai as genai
from Agents.BusinessRuleExtractionAgent import BusinessRuleExtractionAgent
from Agents.ComplianceMonitoringAgent import ComplianceMonitoringAgent

# Configure Google AI
genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))
llm_client = genai.GenerativeModel('gemini-1.5-flash')

# Initialize agents
audit_system = ComplianceMonitoringAgent()
extractor = BusinessRuleExtractionAgent(
    llm_client=llm_client,
    audit_system=audit_system,
    model_name="gemini-1.5-flash"
)

# Test with sample legacy code
legacy_code = """
if (customer.creditScore >= 650 && customer.debtToIncomeRatio <= 0.43) {
    approveApplication(customer);
} else {
    rejectApplication(customer, "Credit requirements not met");
}
"""

# Extract business rules
result = extractor.extract_and_translate_rules(
    legacy_code_snippet=legacy_code,
    context="Loan processing system",
    audit_level=1
)

print("✅ Business Rules Extracted:")
for rule in result['extracted_rules']:
    print(f"- {rule.get('business_description', 'No description')}")
```

Run the test:

```bash
python quick_test.py
```

**Expected Output:**
```
✅ Business Rules Extracted:
- Loan Eligibility Rule: Credit score must be 650 or higher and debt-to-income ratio must be 43% or lower for loan approval
```

## 🎯 What You Just Did

In 5 minutes, you've:

- ✅ **Installed** the complete enterprise AI agent platform
- ✅ **Configured** API access for Google's Gemini AI
- ✅ **Tested** business rule extraction from legacy code
- ✅ **Verified** the audit system is working

## 🚀 Next Steps

### Explore More Agents

Try other agents with the same pattern:

=== "🆕 BYO-LLM (Bring Your Own LLM)"
    
    ```python
    from Utils.llm_providers import OpenAILLMProvider, ClaudeLLMProvider
    from Agents.BusinessRuleExtractionAgent import BusinessRuleExtractionAgent
    from Agents.ComplianceMonitoringAgent import ComplianceMonitoringAgent
    import os
    
    # Use OpenAI GPT instead of Gemini
    os.environ["OPENAI_API_KEY"] = "your_openai_key_here"
    openai_provider = OpenAILLMProvider(model_name="gpt-4o")
    
    audit_system = ComplianceMonitoringAgent()
    extractor = BusinessRuleExtractionAgent(
        audit_system=audit_system,
        llm_provider=openai_provider  # Custom LLM provider!
    )
    
    # Same API, different LLM provider - no code changes needed!
    result = extractor.extract_and_translate_rules(
        legacy_code_snippet="if (score >= 650) approve_loan();",
        context="Banking system"
    )
    ```

=== "PII Protection"
    
    ```python
    from Agents.PersonalDataProtectionAgent import PersonalDataProtectionAgent
    
    pii_agent = PersonalDataProtectionAgent(audit_system=audit_system)
    
    result = pii_agent.scrub_data(
        input_data="John Smith's SSN is 123-45-6789",
        masking_strategy="PARTIAL_MASK"
    )
    print(f"Protected: {result['scrubbed_text']}")
    ```

=== "Document Processing"
    
    ```python
    from Agents.ApplicationTriageAgent import ApplicationTriageAgent
    
    triage_agent = ApplicationTriageAgent(
        llm_client=llm_client,
        audit_system=audit_system
    )
    
    result = triage_agent.triage_submission({
        "type": "loan_application",
        "content": "I need a $50,000 business loan"
    })
    print(f"Category: {result['category']}")
    ```

=== "Documentation"
    
    ```python
    from Agents.RuleDocumentationGeneratorAgent import RuleDocumentationGeneratorAgent
    
    doc_agent = RuleDocumentationGeneratorAgent(
        llm_client=llm_client,
        audit_system=audit_system
    )
    
    result = doc_agent.document_and_visualize_rules(
        extracted_rules=result['extracted_rules'],
        output_format="markdown"
    )
    print("📄 Documentation generated!")
    ```

### Dive Deeper

- **[Installation Guide](installation.md)** - Detailed setup for production
- **[BYO-LLM Configuration](../guides/byo-llm-configuration.md)** - 🆕 Use your preferred LLM provider
- **[Configuration Guide](configuration.md)** - Customize for your environment
- **[User Guides](../guides/business-rule-extraction.md)** - Learn each agent in detail
- **[API Reference](../api/agents/business-rule-extraction.md)** - Complete technical documentation

## 🆘 Troubleshooting

### Common Issues

!!! error "API Key Not Set"
    
    **Error:** `google.generativeai.types.generation_types.BlockedPromptException`
    
    **Solution:** Ensure your `GOOGLE_API_KEY` environment variable is set correctly.

!!! error "Import Errors"
    
    **Error:** `ModuleNotFoundError: No module named 'Agents'`
    
    **Solution:** Make sure you're running Python from the project root directory.

!!! error "Permission Errors"
    
    **Error:** `PermissionError: [Errno 13] Permission denied`
    
    **Solution:** On macOS/Linux, you may need to use `pip3 install --user -r requirements.txt`

### Get Help

- **[GitHub Issues](https://github.com/jconnelly/micro-agent-development/issues)** - Report bugs
- **[Documentation](../index.md)** - Full platform documentation
- **[Examples](../examples/basic-usage.md)** - More usage examples

---

**🎉 Congratulations!** You now have a working enterprise AI agent platform. Ready to modernize your legacy systems and automate your business processes!

*Next: [Installation Guide](installation.md) for production deployment →*