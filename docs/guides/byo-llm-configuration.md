# BYO-LLM (Bring Your Own LLM) Configuration Guide

Complete guide for using custom LLM providers with the Micro-Agent Development Platform, providing enterprise flexibility, cost optimization, and vendor independence.

## 🎯 Overview

The **BYO-LLM (Bring Your Own LLM)** feature allows you to use your preferred LLM provider instead of being locked into a single vendor. This enterprise-grade capability provides:

**🏢 Business Benefits:**
- **Enterprise Flexibility**: Choose LLM providers based on cost, compliance, or performance requirements
- **Cost Optimization**: Switch between providers to optimize costs for different use cases
- **Vendor Independence**: Avoid vendor lock-in and maintain negotiating power with LLM providers
- **Compliance Support**: Use specific providers that meet enterprise security and data residency requirements
- **Custom Model Support**: Integrate proprietary or fine-tuned models for specialized business domains

**🔧 Technical Benefits:**
- **Seamless Integration**: Works with all 7 existing agents without code changes
- **Backward Compatibility**: Existing code continues to work unchanged
- **Standardized Interface**: Consistent API across all LLM providers
- **Error Handling**: Built-in retry logic and graceful error handling
- **Performance Monitoring**: Usage statistics and response time tracking

---

## 🚀 Quick Start

### Default Usage (Gemini - No Changes Required)

```python
# Your existing code works unchanged - defaults to Gemini
from Agents.BusinessRuleExtractionAgent import BusinessRuleExtractionAgent
from Agents.ComplianceMonitoringAgent import ComplianceMonitoringAgent

audit_system = ComplianceMonitoringAgent()
extractor = BusinessRuleExtractionAgent(audit_system=audit_system)

# Uses Google Gemini by default (gemini-1.5-flash)
result = extractor.extract_and_translate_rules(
    legacy_code_snippet="if (score >= 650) approve_loan();",
    context="Banking loan approval system"
)
```

### Using OpenAI GPT Models

```python
import os
from Utils.llm_providers import OpenAILLMProvider
from Agents.BusinessRuleExtractionAgent import BusinessRuleExtractionAgent
from Agents.ComplianceMonitoringAgent import ComplianceMonitoringAgent

# Set your OpenAI API key
os.environ["OPENAI_API_KEY"] = "your_openai_api_key_here"

# Create OpenAI provider
openai_provider = OpenAILLMProvider(model_name="gpt-4o")

# Initialize agent with custom LLM provider
audit_system = ComplianceMonitoringAgent()
extractor = BusinessRuleExtractionAgent(
    audit_system=audit_system,
    llm_provider=openai_provider
)

# Use exactly the same API - no code changes needed
result = extractor.extract_and_translate_rules(
    legacy_code_snippet="if (score >= 650) approve_loan();",
    context="Banking loan approval system"
)
```

### Using Claude (Anthropic)

```python
import os
from Utils.llm_providers import ClaudeLLMProvider
from Agents.ApplicationTriageAgent import ApplicationTriageAgent
from Agents.ComplianceMonitoringAgent import ComplianceMonitoringAgent

# Set your Anthropic API key
os.environ["ANTHROPIC_API_KEY"] = "your_anthropic_api_key_here"

# Create Claude provider
claude_provider = ClaudeLLMProvider(model_name="claude-3-5-sonnet-20241022")

# Initialize agent with Claude
audit_system = ComplianceMonitoringAgent()
triage_agent = ApplicationTriageAgent(
    audit_system=audit_system,
    llm_provider=claude_provider
)
```

---

## 📚 Supported LLM Providers

### 1. **Google Gemini (Default)**

**Models Available:**
- `gemini-1.5-flash` (fast, cost-effective) - **Default**
- `gemini-1.5-pro` (advanced reasoning)
- `gemini-2.0-flash-exp` (latest experimental)

**Configuration:**
```python
from Utils.llm_providers import GeminiLLMProvider
import os

# Set API key (required)
os.environ["GOOGLE_API_KEY"] = "your_google_api_key"

# Create provider
gemini_provider = GeminiLLMProvider(
    model_name="gemini-1.5-pro",  # Optional, defaults to gemini-1.5-flash
    api_key="explicit_api_key"    # Optional, uses env var if not provided
)

# Supported parameters
result = agent._call_llm(
    prompt="Extract business rules from this code",
    temperature=0.1,    # Creativity level (0.0-1.0)
    max_tokens=8192     # Maximum response length
)
```

**Cost:** Very competitive, Google's latest pricing  
**Performance:** Fast response times, excellent for business rule extraction  
**Compliance:** Google Cloud compliance certifications

### 2. **OpenAI GPT Models**

**Models Available:**
- `gpt-4o` (latest GPT-4 optimized) - **Recommended**
- `gpt-4-turbo` (balanced performance and cost)
- `gpt-3.5-turbo` (cost-effective for simple tasks)
- `o1-preview` (advanced reasoning for complex problems)

**Configuration:**
```python
from Utils.llm_providers import OpenAILLMProvider
import os

# Set API key (required)
os.environ["OPENAI_API_KEY"] = "your_openai_api_key"

# Create provider
openai_provider = OpenAILLMProvider(
    model_name="gpt-4o",
    api_key="explicit_api_key",    # Optional
    base_url="https://api.openai.com"  # Optional, for OpenAI-compatible APIs
)

# Supported parameters
result = agent._call_llm(
    prompt="Document these business rules",
    temperature=0.1,    # Creativity level
    max_tokens=4096,    # Maximum response length
    top_p=1.0          # Nucleus sampling parameter
)
```

**Cost:** Premium pricing, pay-per-token  
**Performance:** Excellent quality, proven track record  
**Compliance:** SOC 2 Type 2, extensive enterprise features

### 3. **Anthropic Claude**

**Models Available:**
- `claude-3-5-sonnet-20241022` (latest Sonnet) - **Recommended**
- `claude-3-5-haiku-20241022` (fast, cost-effective)
- `claude-3-opus-20240229` (most capable, highest quality)

**Configuration:**
```python
from Utils.llm_providers import ClaudeLLMProvider
import os

# Set API key (required)
os.environ["ANTHROPIC_API_KEY"] = "your_anthropic_api_key"

# Create provider
claude_provider = ClaudeLLMProvider(
    model_name="claude-3-5-sonnet-20241022",
    api_key="explicit_api_key"    # Optional
)

# Supported parameters
result = agent._call_llm(
    prompt="Analyze this legacy code for compliance rules",
    temperature=0.1,    # Creativity level
    max_tokens=4096     # Maximum response length
)
```

**Cost:** Competitive pricing, excellent value  
**Performance:** Superior reasoning, excellent for complex business logic  
**Compliance:** Strong privacy focus, constitutional AI approach

### 4. **Azure OpenAI (Enterprise)**

**Enterprise Features:**
- Data residency and compliance controls
- Private networking and VNet integration
- Enterprise security and access controls
- SLA guarantees and dedicated support

**Models Available:**
- All OpenAI models available through Azure
- Custom fine-tuned models
- On-demand and provisioned throughput options

**Configuration:**
```python
from Utils.llm_providers import AzureOpenAILLMProvider
import os

# Set Azure credentials (required)
os.environ["AZURE_OPENAI_API_KEY"] = "your_azure_api_key"
os.environ["AZURE_OPENAI_ENDPOINT"] = "https://your-resource.openai.azure.com/"

# Create provider
azure_provider = AzureOpenAILLMProvider(
    deployment_name="gpt-4o-deployment",  # Your Azure deployment name
    api_version="2024-02-15-preview",     # API version
    api_key="explicit_api_key",           # Optional
    endpoint="https://custom-endpoint/"   # Optional
)
```

**Cost:** Enterprise pricing, reserved capacity options  
**Performance:** Same as OpenAI with enterprise SLAs  
**Compliance:** Meets strictest enterprise requirements

---

## 🏭 Factory Methods & Convenience Functions

### Quick Provider Creation

```python
from Utils.llm_providers import LLMProviderFactory

# Create providers with sensible defaults
gemini = LLMProviderFactory.create_gemini_provider()
openai = LLMProviderFactory.create_openai_provider(model_name="gpt-4o")
claude = LLMProviderFactory.create_claude_provider(model_name="claude-3-5-sonnet-20241022")

# Create from configuration dictionary
provider = LLMProviderFactory.create_provider_from_config(
    provider_type="openai",
    model_name="gpt-4-turbo",
    api_key="your_api_key"
)
```

### Environment-Based Configuration

```python
import os
from Utils.llm_providers import create_llm_provider

# Set environment variables
os.environ["LLM_PROVIDER"] = "claude"
os.environ["LLM_MODEL"] = "claude-3-5-sonnet-20241022"
os.environ["ANTHROPIC_API_KEY"] = "your_api_key"

# Create provider from environment
provider = create_llm_provider(
    provider_type=os.environ["LLM_PROVIDER"],
    model_name=os.environ["LLM_MODEL"]
)
```

---

## 🔧 Integration Examples

### All Agents Support BYO-LLM

```python
from Utils.llm_providers import OpenAILLMProvider
from Agents import *

# Create custom LLM provider
custom_llm = OpenAILLMProvider(model_name="gpt-4o")

# All agents work the same way
audit_system = ComplianceMonitoringAgent()

# Business Rule Extraction with OpenAI
rule_extractor = BusinessRuleExtractionAgent(
    audit_system=audit_system,
    llm_provider=custom_llm
)

# Application Triage with same provider
triage_agent = ApplicationTriageAgent(
    audit_system=audit_system,
    llm_provider=custom_llm
)

# Documentation Generation
doc_generator = RuleDocumentationGeneratorAgent(
    audit_system=audit_system,
    llm_provider=custom_llm
)

# Personal Data Protection (doesn't use LLM - works normally)
pii_agent = PersonalDataProtectionAgent(audit_system=audit_system)
```

### Mixed Provider Environment

```python
# Use different providers for different use cases
from Utils.llm_providers import *

# Fast, cost-effective provider for simple tasks
gemini_fast = GeminiLLMProvider(model_name="gemini-1.5-flash")
simple_tasks_agent = ApplicationTriageAgent(
    audit_system=audit_system,
    llm_provider=gemini_fast
)

# High-quality provider for complex analysis
claude_advanced = ClaudeLLMProvider(model_name="claude-3-5-sonnet-20241022")
analysis_agent = BusinessRuleExtractionAgent(
    audit_system=audit_system,
    llm_provider=claude_advanced
)

# Enterprise provider for sensitive data
azure_secure = AzureOpenAILLMProvider(
    deployment_name="secure-gpt4-deployment"
)
secure_agent = AdvancedDocumentationAgent(
    audit_system=audit_system,
    llm_provider=azure_secure
)
```

---

## 📊 Configuration Management

### YAML Configuration Support

Create `config/llm_providers.yaml`:

```yaml
# LLM Provider Configuration
default_provider: "gemini"

providers:
  gemini:
    model_name: "gemini-1.5-flash"
    api_key_env: "GOOGLE_API_KEY"
    parameters:
      temperature: 0.1
      max_tokens: 8192
      
  openai:
    model_name: "gpt-4o"
    api_key_env: "OPENAI_API_KEY"  
    parameters:
      temperature: 0.1
      max_tokens: 4096
      top_p: 1.0
      
  claude:
    model_name: "claude-3-5-sonnet-20241022"
    api_key_env: "ANTHROPIC_API_KEY"
    parameters:
      temperature: 0.1
      max_tokens: 4096
      
  azure_openai:
    deployment_name: "gpt4-production"
    api_version: "2024-02-15-preview"
    api_key_env: "AZURE_OPENAI_API_KEY"
    endpoint_env: "AZURE_OPENAI_ENDPOINT"

# Environment-specific overrides
environments:
  development:
    default_provider: "gemini"
    providers:
      gemini:
        model_name: "gemini-1.5-flash"
        
  production:
    default_provider: "azure_openai"
    providers:
      azure_openai:
        deployment_name: "gpt4-enterprise"
```

### Loading Configuration

```python
from Utils.llm_providers import LLMProviderFactory
import yaml
import os

def load_llm_config(environment="production"):
    """Load LLM configuration from YAML file"""
    
    with open("config/llm_providers.yaml", "r") as f:
        config = yaml.safe_load(f)
    
    # Get environment-specific config
    env_config = config.get("environments", {}).get(environment, {})
    base_config = config
    
    # Merge configurations
    provider_type = env_config.get("default_provider", base_config["default_provider"])
    provider_config = base_config["providers"][provider_type]
    
    # Override with environment-specific settings
    if "providers" in env_config and provider_type in env_config["providers"]:
        provider_config.update(env_config["providers"][provider_type])
    
    # Create provider
    return LLMProviderFactory.create_provider_from_config(
        provider_type=provider_type,
        **provider_config
    )

# Usage
llm_provider = load_llm_config("production")
agent = BusinessRuleExtractionAgent(
    audit_system=audit_system,
    llm_provider=llm_provider
)
```

---

## 🔍 Monitoring & Performance

### Usage Statistics Tracking

```python
# Make LLM call and get detailed statistics
result = agent._call_llm(
    prompt="Extract business rules from legacy COBOL code",
    temperature=0.1,
    max_tokens=4096
)

# Access detailed metrics
print(f"Provider: {result['provider_type']}")
print(f"Model: {result['model_name']}")
print(f"Response Time: {result['response_time_ms']}ms")
print(f"Success: {result['success']}")

if result['usage_stats']:
    print(f"Token Usage: {result['usage_stats']}")
```

### Error Handling and Monitoring

```python
def robust_llm_processing(agent, prompts):
    """Process multiple prompts with error handling and monitoring"""
    
    results = []
    total_tokens = 0
    total_time = 0
    errors = []
    
    for i, prompt in enumerate(prompts):
        try:
            result = agent._call_llm(prompt)
            
            if result['success']:
                results.append(result['content'])
                
                # Track metrics
                if result['usage_stats']:
                    total_tokens += result['usage_stats'].get('total_tokens', 0)
                if result['response_time_ms']:
                    total_time += result['response_time_ms']
                    
            else:
                errors.append(f"Prompt {i}: {result['error']}")
                
        except Exception as e:
            errors.append(f"Prompt {i}: Unexpected error - {str(e)}")
    
    return {
        "results": results,
        "total_tokens": total_tokens,
        "total_time_ms": total_time,
        "average_time_ms": total_time / len(prompts) if prompts else 0,
        "success_rate": len(results) / len(prompts) if prompts else 0,
        "errors": errors
    }
```

---

## 🛡️ Security & Compliance

### API Key Management

**✅ Best Practices:**
```python
import os
from pathlib import Path

# Use environment variables (recommended)
os.environ["OPENAI_API_KEY"] = "your_api_key"

# Use .env files (development)
from dotenv import load_dotenv
load_dotenv()  # Loads from .env file

# Use cloud secret managers (production)
# - Azure Key Vault
# - AWS Secrets Manager  
# - Google Secret Manager
```

**❌ Security Anti-Patterns:**
```python
# Never hardcode API keys
api_key = "sk-1234567890abcdef"  # DON'T DO THIS

# Never commit API keys to version control
# Never log API keys in application logs
# Never pass API keys in URLs or query parameters
```

### Enterprise Security Features

**Azure OpenAI** (Most Secure):
```python
# Enterprise deployment with full security controls
azure_provider = AzureOpenAILLMProvider(
    deployment_name="secure-gpt4-deployment",
    api_version="2024-02-15-preview"
)

# Features available:
# - Private endpoints and VNet integration
# - Customer-managed encryption keys
# - Azure AD authentication
# - Audit logs and compliance reporting
# - Data residency guarantees
```

**Google Gemini** (Google Cloud Security):
```python
# Uses Google Cloud security infrastructure
# - Identity and Access Management (IAM)
# - VPC Service Controls
# - Customer-managed encryption keys (CMEK)
# - Audit logging and monitoring
```

**OpenAI/Claude** (API-Based):
```python
# Standard API security
# - HTTPS encryption in transit
# - API key authentication
# - Rate limiting and abuse detection
# - Data retention policies
```

---

## 🚀 Production Deployment

### Kubernetes Configuration

```yaml
# kubernetes-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: micro-agent-platform
spec:
  replicas: 3
  selector:
    matchLabels:
      app: micro-agent-platform
  template:
    metadata:
      labels:
        app: micro-agent-platform
    spec:
      containers:
      - name: platform
        image: micro-agent-platform:latest
        env:
        # Use Kubernetes secrets for API keys
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: llm-credentials
              key: openai-api-key
        - name: ANTHROPIC_API_KEY
          valueFrom:
            secretKeyRef:
              name: llm-credentials
              key: anthropic-api-key
        - name: LLM_PROVIDER
          value: "openai"
        - name: LLM_MODEL
          value: "gpt-4o"
---
apiVersion: v1
kind: Secret
metadata:
  name: llm-credentials
type: Opaque
data:
  openai-api-key: <base64-encoded-key>
  anthropic-api-key: <base64-encoded-key>
```

### Docker Configuration

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . /app

RUN pip install -r requirements.txt

# Don't include API keys in image
ENV PYTHONPATH=/app
ENV LLM_PROVIDER=gemini

CMD ["python", "-m", "your_application"]
```

### Load Balancing Multiple Providers

```python
import random
from typing import List
from Utils.llm_providers import LLMProvider

class LoadBalancedLLMProvider:
    """Load balance between multiple LLM providers for high availability"""
    
    def __init__(self, providers: List[LLMProvider], weights: List[float] = None):
        self.providers = providers
        self.weights = weights or [1.0] * len(providers)
        self._normalize_weights()
    
    def _normalize_weights(self):
        total = sum(self.weights)
        self.weights = [w / total for w in self.weights]
    
    def generate_content(self, prompt: str, **kwargs):
        """Try providers in weighted random order with fallback"""
        
        # Shuffle providers based on weights
        provider_indices = list(range(len(self.providers)))
        provider = random.choices(provider_indices, weights=self.weights)[0]
        
        # Try primary provider first
        try:
            return self.providers[provider].generate_content(prompt, **kwargs)
        except Exception as e:
            # Try other providers as fallback
            for i, fallback_provider in enumerate(self.providers):
                if i != provider:
                    try:
                        return fallback_provider.generate_content(prompt, **kwargs)
                    except:
                        continue
            
            # All providers failed
            raise Exception(f"All LLM providers failed. Last error: {str(e)}")

# Usage
balanced_provider = LoadBalancedLLMProvider(
    providers=[
        GeminiLLMProvider(),
        OpenAILLMProvider(model_name="gpt-4o"),
        ClaudeLLMProvider()
    ],
    weights=[0.4, 0.4, 0.2]  # 40% Gemini, 40% OpenAI, 20% Claude
)
```

---

## 🔧 Troubleshooting

### Common Issues

!!! error "API Key Not Found"
    
    **Problem:** `ValueError: OPENAI_API_KEY environment variable or api_key parameter required`
    
    **Solutions:**
    ```python
    # Set environment variable
    import os
    os.environ["OPENAI_API_KEY"] = "your_key_here"
    
    # Or pass explicitly
    provider = OpenAILLMProvider(api_key="your_key_here")
    
    # Or use .env file
    from dotenv import load_dotenv
    load_dotenv()
    ```

!!! error "Import Error"
    
    **Problem:** `ImportError: anthropic package required for Claude provider`
    
    **Solutions:**
    ```bash
    # Install required packages
    pip install anthropic
    pip install openai
    pip install google-generativeai
    
    # Or install all at once
    pip install -r requirements.txt
    ```

!!! error "Model Not Available"
    
    **Problem:** `Invalid model name or deployment not found`
    
    **Solutions:**
    - Check model name spelling
    - Verify model is available in your region
    - For Azure: Ensure deployment name is correct
    - Check API key permissions

### Performance Optimization

```python
# Optimize for different use cases

# High-throughput, cost-effective
fast_provider = GeminiLLMProvider(model_name="gemini-1.5-flash")

# Balanced performance and quality
balanced_provider = OpenAILLMProvider(model_name="gpt-4-turbo") 

# Maximum quality for complex tasks
premium_provider = ClaudeLLMProvider(model_name="claude-3-opus-20240229")

# Use appropriate provider for each agent
simple_triage = ApplicationTriageAgent(llm_provider=fast_provider)
complex_extraction = BusinessRuleExtractionAgent(llm_provider=premium_provider)
```

### Testing Provider Connections

```python
def test_all_providers():
    """Test all configured LLM providers"""
    
    providers = {
        "Gemini": GeminiLLMProvider(),
        "OpenAI": OpenAILLMProvider(),
        "Claude": ClaudeLLMProvider()
    }
    
    for name, provider in providers.items():
        try:
            if provider.validate_connection():
                print(f"✅ {name}: Connection successful")
            else:
                print(f"❌ {name}: Connection failed")
        except Exception as e:
            print(f"❌ {name}: Error - {str(e)}")

# Run connectivity tests
test_all_providers()
```

---

## 📈 Cost Optimization

### Provider Cost Comparison (Approximate)

| Provider | Model | Input (per 1K tokens) | Output (per 1K tokens) | Best For |
|----------|-------|-------------------|-------------------|----------|
| **Gemini** | 1.5-flash | $0.075 | $0.30 | High-volume, cost-effective |
| **Gemini** | 1.5-pro | $1.25 | $5.00 | Balanced performance |
| **OpenAI** | GPT-4o | $2.50 | $10.00 | Premium quality |
| **OpenAI** | GPT-4-turbo | $10.00 | $30.00 | Complex reasoning |
| **Claude** | 3.5-Sonnet | $3.00 | $15.00 | Superior reasoning |
| **Claude** | 3-Opus | $15.00 | $75.00 | Maximum capability |

### Cost-Optimized Strategies

```python
# Strategy 1: Tiered processing
def create_tiered_agents(audit_system):
    """Create agents optimized for different cost/quality tiers"""
    
    # Tier 1: High-volume, simple tasks (lowest cost)
    tier1_provider = GeminiLLMProvider(model_name="gemini-1.5-flash")
    simple_triage = ApplicationTriageAgent(
        audit_system=audit_system,
        llm_provider=tier1_provider
    )
    
    # Tier 2: Moderate complexity (balanced cost/quality) 
    tier2_provider = OpenAILLMProvider(model_name="gpt-4o")
    rule_extraction = BusinessRuleExtractionAgent(
        audit_system=audit_system,
        llm_provider=tier2_provider
    )
    
    # Tier 3: Complex analysis (premium quality)
    tier3_provider = ClaudeLLMProvider(model_name="claude-3-5-sonnet-20241022")
    advanced_docs = AdvancedDocumentationAgent(
        audit_system=audit_system,
        llm_provider=tier3_provider
    )
    
    return {
        "simple": simple_triage,
        "moderate": rule_extraction,
        "complex": advanced_docs
    }

# Strategy 2: Dynamic provider selection based on input complexity
def select_provider_by_complexity(input_text: str):
    """Select LLM provider based on input complexity"""
    
    # Simple heuristics (can be made more sophisticated)
    word_count = len(input_text.split())
    complexity_score = word_count + input_text.count('\n') * 2
    
    if complexity_score < 100:
        return GeminiLLMProvider(model_name="gemini-1.5-flash")
    elif complexity_score < 500:
        return OpenAILLMProvider(model_name="gpt-4o")
    else:
        return ClaudeLLMProvider(model_name="claude-3-5-sonnet-20241022")
```

---

## 🎯 Migration Guide

### From Existing Code

**Before (Single Provider):**
```python
# Old way - hardcoded to specific LLM
import google.generativeai as genai
from Agents.BusinessRuleExtractionAgent import BusinessRuleExtractionAgent

genai.configure(api_key="your_key")
llm_client = genai.GenerativeModel('gemini-1.5-flash')

agent = BusinessRuleExtractionAgent(
    llm_client=llm_client,
    audit_system=audit_system
)
```

**After (BYO-LLM):**
```python
# New way - flexible provider selection
from Utils.llm_providers import GeminiLLMProvider, OpenAILLMProvider
from Agents.BusinessRuleExtractionAgent import BusinessRuleExtractionAgent

# Option 1: Use default (no changes needed)
agent = BusinessRuleExtractionAgent(audit_system=audit_system)

# Option 2: Specify provider
provider = OpenAILLMProvider(model_name="gpt-4o")
agent = BusinessRuleExtractionAgent(
    audit_system=audit_system,
    llm_provider=provider
)
```

### Gradual Migration Strategy

1. **Phase 1**: Update existing code to use new constructor format (backward compatible)
2. **Phase 2**: Add provider selection for new features
3. **Phase 3**: Optimize provider choice based on cost/performance requirements
4. **Phase 4**: Full migration to standardized provider interface

---

**✅ You're Ready!**

The BYO-LLM system provides enterprise-grade flexibility while maintaining the simplicity of the original API. Choose the provider that best fits your cost, compliance, and performance requirements.

*Next: [Business Rule Extraction Guide](business-rule-extraction.md) to start using your custom LLM provider →*