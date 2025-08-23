# Marketplace Demo Application

## Overview

The **Marketplace Demo Application** provides interactive demonstrations of all 7 AI agents in the Micro-Agent Development Platform. This Flask web application showcases real agent capabilities with sample data, designed for marketplace presentations, sales demonstrations, and customer trials.

## Features

### 🎯 **Interactive Agent Demonstrations**
- **Live Processing**: Real-time agent execution with sample data
- **7 Agent Showcases**: Individual demo pages for each AI agent
- **Professional Interface**: Bootstrap 5 responsive design with Material theme
- **Sample File Library**: 15+ pre-loaded sample files covering multiple industries

### 🚀 **Supported Agents**
1. **Business Rule Extraction** - Extract rules from legacy COBOL, Java, C++ systems
2. **Application Triage** - Intelligent document routing and classification
3. **Personal Data Protection** - GDPR/CCPA compliant PII detection and masking
4. **Rule Documentation Generator** - Automated business documentation
5. **Compliance Monitoring** - SOX/GDPR/HIPAA audit trail management
6. **Advanced Documentation** - Enterprise documentation with tool integration
7. **Enterprise Data Privacy** - High-performance PII processing

### 💼 **Business Value**
- **"Try Before You Buy"**: Live demonstrations with real sample data
- **Performance Validation**: Live metrics showing speed and accuracy
- **Integration Examples**: Python and REST API code samples
- **Compliance Proof**: Live GDPR/HIPAA compliance demonstrations

## Quick Start

### Prerequisites
- Python 3.9+
- All platform dependencies installed (`pip install -r requirements.txt`)
- Sample data files in `Sample_Data_Files/` directory

### Start the Demo
```bash
cd C:\Development\AI_Development\micro-agent-development
python demo_app.py
```

### Access the Demo
- **Home Page**: http://localhost:5001
- **Agent Demos**: http://localhost:5001/demo/{agent_name}
- **API Endpoints**: http://localhost:5001/api/run_demo/{agent_name}

## Usage Guide

### 🏠 **Home Page** (`/`)
- **Agent Overview**: Cards showing all 7 agents with capabilities
- **Performance Metrics**: Live specs for each agent (speed, accuracy, formats)
- **Quick Navigation**: Direct links to individual agent demonstrations
- **Enterprise Features**: Overview of key platform capabilities

### 🔧 **Agent Demo Pages** (`/demo/{agent_name}`)
- **Sample File Selection**: Choose from pre-loaded industry-specific samples
- **Live Processing**: Click "Run Demo" to execute agent with selected sample
- **Results Display**: Professional formatting of agent outputs
- **Integration Examples**: Python and REST API code samples
- **Capabilities Panel**: Agent-specific performance metrics and features

### 📊 **Sample Files Available**

#### **Business Rule Extraction**
- `sample_legacy_insurance.cbl` - COBOL insurance underwriting system
- `sample_legacy_code.java` - Java banking system with loan rules
- `sample_legacy_trading.cpp` - C++ high-frequency trading system

#### **Application Triage**  
- `financial_submissions.json` - Insurance claims and loan applications
- `government_submissions.json` - Citizen service requests
- `telecom_submissions.json` - Customer service tickets

#### **Personal Data Protection**
- `financial_submissions.json` - Customer financial data with PII
- `sample_legacy_healthcare.mumps` - Medical records system

#### **Rule Documentation**
- `sample_extracted_rules.json` - Business rules for documentation
- `sample_advanced_rules.json` - Complex multi-domain rules

#### **And More**
- 15+ total sample files covering healthcare, e-commerce, manufacturing, retail, and government use cases

## API Usage

### Run Agent Demo
```bash
curl -X POST "http://localhost:5001/api/run_demo/business_rule_extraction" \
  -H "Content-Type: application/json" \
  -d '{"sample_file": "sample_legacy_insurance.cbl"}'
```

### Response Format
```json
{
  "success": true,
  "agent": "business_rule_extraction",
  "input_file": "sample_legacy_insurance.cbl",
  "input_preview": "COBOL code preview...",
  "output": {
    "type": "rule_extraction",
    "rules_found": 25,
    "rules": [...],
    "language_detected": "COBOL",
    "confidence": 0.96
  },
  "timestamp": "2024-01-15T10:30:00Z",
  "processing_time": "2.45s"
}
```

## Demo Output Examples

### Business Rule Extraction
```json
{
  "rules_found": 25,
  "language_detected": "COBOL",
  "confidence": 0.96,
  "rules": [
    {
      "rule_id": "RULE_001",
      "description": "Minimum age requirement (18 years) for insurance eligibility"
    }
  ]
}
```

### Application Triage
```json
{
  "submissions_processed": 3,
  "results": [
    {
      "submission_id": "DEMO_1",
      "category": "insurance_claim",
      "priority": "HIGH",
      "routing": "insurance_department",
      "confidence": 0.95
    }
  ]
}
```

### Personal Data Protection
```json
{
  "pii_found": 8,
  "pii_types": ["Email", "Phone", "SSN"],
  "protection_applied": "Masking strategy applied",
  "compliance": ["GDPR", "CCPA", "HIPAA"]
}
```

## Configuration

### Demo Settings
The demo app uses fallback configurations for marketplace demonstration. For production use, ensure proper configuration:

```python
# In demo_app.py
CONFIG = load_config("agent_defaults")  # Uses config/agent_defaults.yaml
SAMPLE_DATA_DIR = Path("Sample_Data_Files")
```

### Environment Variables
For agent functionality, set up environment variables:
```bash
# For OpenAI integration (BYO-LLM pattern)
export OPENAI_API_KEY="your-api-key"

# For Google Generative AI (fallback)
export GOOGLE_API_KEY="your-api-key"
```

## Troubleshooting

### Common Issues

#### **Agent Initialization Errors**
```python
# Ensure correct constructor parameters
agent = BusinessRuleExtractionAgent(
    audit_system=audit_system,
    llm_client=None  # Uses BYO-LLM auto-creation
)
```

#### **Sample File Not Found**
- Verify `Sample_Data_Files/` directory exists
- Check file permissions and encoding
- Ensure sample files are in correct format

#### **Port Already in Use**
```bash
# Change port in demo_app.py
app.run(debug=True, host='0.0.0.0', port=5002)
```

#### **Missing Dependencies**
```bash
pip install flask
pip install -r requirements.txt
```

## Production Deployment

### For Production Use
```python
# Use production WSGI server
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5001 demo_app:app
```

### Docker Deployment
```dockerfile
FROM python:3.9
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
EXPOSE 5001
CMD ["python", "demo_app.py"]
```

## File Structure

```
├── demo_app.py                 # Main Flask application (787 lines)
├── templates/
│   ├── base.html              # Base template with Bootstrap 5
│   ├── marketplace_home.html  # Agent showcase homepage
│   └── agent_demo.html        # Individual agent demo interface
├── Sample_Data_Files/          # Sample data for demonstrations
│   ├── sample_legacy_insurance.cbl
│   ├── financial_submissions.json
│   └── ... (15+ sample files)
└── DEMO_README.md             # This file
```

## Support

For demo application issues:
- Check console output for error messages
- Verify agent constructor parameters
- Ensure sample files are accessible
- Test individual agents separately if needed

For platform support:
- GitHub Issues: https://github.com/jconnelly/micro-agent-development/issues
- Documentation: Complete MkDocs system available
- Enterprise Support: Available for production deployments

---

**Built for enterprise AI demonstrations. Ready for marketplace showcase and customer trials.**