# Documentation Generation Guide

![Auto Documentation](https://img.shields.io/badge/Auto-Documentation-green?style=for-the-badge)
![Multi Format](https://img.shields.io/badge/Multi-Format-blue?style=for-the-badge)
![Enterprise Ready](https://img.shields.io/badge/Enterprise-Ready-purple?style=for-the-badge)

**Automated business rule documentation generation with multi-format output and domain classification**

---

## 🎯 Overview

The Documentation Generation system provides **automated business documentation**, **multi-format output**, and **intelligent domain classification** for enterprise business rules and processes. Designed to accelerate modernization projects and maintain institutional knowledge.

### Key Capabilities

=== "Automated Documentation"
    
    **Intelligent Analysis**
    
    - Business rule classification and categorization
    - Domain-specific documentation templates
    - Automated cross-references and relationships
    - Context-aware documentation generation
    
    **Multi-Language Support**
    
    - COBOL legacy system documentation
    - Java enterprise application documentation  
    - C++ system documentation
    - Generic business process documentation

=== "Multi-Format Output"
    
    **Professional Formats**
    
    - **Markdown**: Technical documentation and wikis
    - **HTML**: Interactive web documentation
    - **JSON**: API integration and data exchange
    - **PDF**: Executive reports and compliance documentation
    - **Excel**: Business stakeholder reports
    
    **Template System**
    
    - Customizable documentation templates
    - Corporate branding and styling
    - Stakeholder-specific views
    - Automated table of contents and indexing

=== "Domain Classification"
    
    **Business Domains**
    
    - Financial Services (Banking, Insurance, Trading)
    - Healthcare (Clinical, Administrative, Compliance)
    - Government (Citizen Services, Regulatory)
    - Manufacturing (Quality, Safety, Supply Chain)
    - Technology (API, Data Processing, Integration)
    
    **Smart Classification**
    
    - Automatic domain detection from context
    - Rule complexity scoring
    - Business impact assessment
    - Modernization priority ranking

---

## 🚀 Quick Start

### Basic Documentation Generation

```python
from Agents.RuleDocumentationGeneratorAgent import RuleDocumentationGeneratorAgent
from Agents.ComplianceMonitoringAgent import ComplianceMonitoringAgent

# Initialize compliance monitoring
audit_system = ComplianceMonitoringAgent()

# Create documentation generator
doc_generator = RuleDocumentationGeneratorAgent(
    audit_system=audit_system,
    output_format="markdown",
    template_style="professional"
)

# Generate documentation from extracted rules
business_rules = [
    {
        'rule_id': 'LOAN_001',
        'rule_name': 'Minimum Credit Score Requirement',
        'description': 'Loan applicants must have credit score >= 650',
        'business_logic': 'IF credit_score < 650 THEN reject_application',
        'domain': 'Financial Services',
        'complexity': 'Low',
        'priority': 'High'
    },
    {
        'rule_id': 'LOAN_002', 
        'rule_name': 'Debt-to-Income Ratio Validation',
        'description': 'Debt-to-income ratio must not exceed 43%',
        'business_logic': 'IF (monthly_debt / monthly_income) > 0.43 THEN reject_application',
        'domain': 'Financial Services',
        'complexity': 'Medium',
        'priority': 'High'
    }
]

# Generate comprehensive documentation
documentation = doc_generator.generate_documentation(
    rules_data=business_rules,
    context="Loan origination system modernization",
    include_sections=[
        "executive_summary",
        "business_rules_catalog", 
        "implementation_guide",
        "compliance_notes",
        "modernization_roadmap"
    ]
)

print(f"Documentation generated: {documentation['output_file']}")
print(f"Pages: {documentation['page_count']}")
print(f"Rules documented: {documentation['rules_processed']}")
```

### Advanced Documentation with Templates

```python
# Create custom documentation template
custom_template = {
    'name': 'Executive Compliance Report',
    'sections': [
        {
            'title': 'Executive Summary',
            'include_metrics': True,
            'include_recommendations': True
        },
        {
            'title': 'Regulatory Compliance Analysis',
            'frameworks': ['SOX', 'GDPR', 'SOC2'],
            'include_risk_assessment': True
        },
        {
            'title': 'Business Rules Inventory',
            'grouping': 'by_domain',
            'include_complexity_analysis': True
        },
        {
            'title': 'Modernization Recommendations',
            'include_priority_matrix': True,
            'include_cost_estimates': True
        }
    ],
    'styling': {
        'corporate_branding': True,
        'include_charts': True,
        'professional_formatting': True
    }
}

# Generate with custom template
executive_doc = doc_generator.generate_with_template(
    rules_data=business_rules,
    template=custom_template,
    output_format="pdf",
    context="Quarterly compliance review"
)
```

---

## 🔧 Configuration

### Documentation Generator Configuration

Configure documentation generation in `config/agent_defaults.yaml`:

```yaml
agent_defaults:
  rule_documentation_agent:
    api_timeout_seconds: 30.0          # API call timeout
    max_retries: 3                     # Retry attempts
    default_output_format: "markdown"  # Default format
    enable_auto_classification: true   # Enable domain classification
    include_compliance_analysis: true  # Include compliance sections
    
  documentation_settings:
    templates_directory: "./templates/documentation"
    output_directory: "./generated_docs"
    enable_version_control: true       # Git integration
    auto_backup: true                  # Backup generated docs
    
  domain_classification:
    confidence_threshold: 0.85         # Classification confidence
    enable_ml_classification: true     # Use ML for classification
    fallback_domain: "General Business" # Default domain
```

### Output Format Configuration

```yaml
# Format-specific settings
output_formats:
  markdown:
    enable_toc: true                   # Table of contents
    include_metadata: true             # YAML frontmatter
    cross_reference_links: true       # Auto-linking
    
  html:
    template: "professional_responsive"
    enable_search: true               # Client-side search
    include_navigation: true          # Navigation sidebar
    responsive_design: true           # Mobile-friendly
    
  pdf:
    page_size: "A4"
    margins: "1inch"
    include_header_footer: true
    professional_styling: true
    
  json:
    pretty_print: true
    include_metadata: true
    schema_validation: true
    
  excel:
    include_charts: true
    business_dashboard: true
    pivot_tables: true
```

---

## 📄 Documentation Templates

### Professional Business Report

```python
# Professional template for business stakeholders
business_template = {
    'name': 'Business Stakeholder Report',
    'target_audience': 'Business Executives',
    'sections': [
        {
            'section': 'executive_summary',
            'content': {
                'key_metrics': True,
                'business_impact': True,
                'recommendations': True,
                'timeline': True
            }
        },
        {
            'section': 'business_rules_overview',
            'content': {
                'rule_categories': True,
                'complexity_distribution': True,
                'priority_matrix': True,
                'domain_breakdown': True
            }
        },
        {
            'section': 'modernization_strategy',
            'content': {
                'quick_wins': True,
                'medium_term_goals': True,
                'long_term_vision': True,
                'resource_requirements': True
            }
        },
        {
            'section': 'risk_analysis',
            'content': {
                'technical_risks': True,
                'business_risks': True,
                'mitigation_strategies': True,
                'compliance_considerations': True
            }
        }
    ],
    'styling': {
        'executive_friendly': True,
        'minimal_technical_detail': True,
        'emphasis_on_business_value': True,
        'include_visualizations': True
    }
}

# Generate business-focused documentation
business_doc = doc_generator.generate_with_template(
    rules_data=extracted_rules,
    template=business_template,
    output_format="pdf",
    context="Legacy system modernization business case"
)
```

### Technical Implementation Guide

```python
# Technical template for development teams  
technical_template = {
    'name': 'Technical Implementation Guide',
    'target_audience': 'Development Teams',
    'sections': [
        {
            'section': 'architecture_overview',
            'content': {
                'system_diagram': True,
                'component_relationships': True,
                'data_flow': True,
                'integration_points': True
            }
        },
        {
            'section': 'detailed_rule_specifications',
            'content': {
                'rule_logic_breakdown': True,
                'input_output_specifications': True,
                'validation_rules': True,
                'error_handling': True
            }
        },
        {
            'section': 'implementation_guidelines',
            'content': {
                'coding_standards': True,
                'testing_requirements': True,
                'performance_considerations': True,
                'security_requirements': True
            }
        },
        {
            'section': 'deployment_instructions',
            'content': {
                'environment_setup': True,
                'configuration_management': True,
                'monitoring_setup': True,
                'rollback_procedures': True
            }
        }
    ],
    'styling': {
        'detailed_technical_content': True,
        'code_examples': True,
        'api_specifications': True,
        'troubleshooting_guides': True
    }
}
```

### Compliance Documentation

```python
# Compliance-focused template for auditors
compliance_template = {
    'name': 'Regulatory Compliance Documentation',
    'target_audience': 'Auditors and Compliance Officers',
    'sections': [
        {
            'section': 'compliance_framework_mapping',
            'content': {
                'sox_controls': True,
                'gdpr_requirements': True,
                'industry_regulations': True,
                'control_objectives': True
            }
        },
        {
            'section': 'audit_trail_documentation',
            'content': {
                'rule_extraction_evidence': True,
                'validation_procedures': True,
                'approval_workflows': True,
                'change_management': True
            }
        },
        {
            'section': 'risk_assessment',
            'content': {
                'compliance_gaps': True,
                'risk_ratings': True,
                'remediation_plans': True,
                'monitoring_procedures': True
            }
        },
        {
            'section': 'evidence_package',
            'content': {
                'supporting_documentation': True,
                'test_results': True,
                'approval_records': True,
                'audit_signatures': True
            }
        }
    ],
    'styling': {
        'formal_compliance_format': True,
        'regulatory_references': True,
        'audit_ready_presentation': True,
        'evidence_organization': True
    }
}
```

---

## 🏗️ Domain Classification

### Automatic Domain Detection

```python
# Configure domain classification engine
domain_classifier = doc_generator.get_domain_classifier()

# Classify business rules by domain
domain_analysis = domain_classifier.analyze_domains(business_rules)

print("Domain Distribution:")
for domain, rules in domain_analysis['domain_breakdown'].items():
    print(f"  {domain}: {len(rules)} rules ({rules['percentage']:.1f}%)")

# Domain-specific documentation generation
for domain in domain_analysis['detected_domains']:
    domain_rules = domain_analysis['domain_breakdown'][domain]['rules']
    
    # Generate domain-specific documentation
    domain_doc = doc_generator.generate_domain_documentation(
        domain=domain,
        rules=domain_rules,
        include_domain_context=True,
        specialized_templates=True
    )
    
    print(f"Generated {domain} documentation: {domain_doc['output_file']}")
```

### Custom Domain Configuration

```python
# Define custom business domain
custom_domain = {
    'name': 'Supply Chain Management',
    'description': 'Rules governing supply chain operations and logistics',
    'keywords': [
        'inventory', 'supplier', 'procurement', 'logistics',
        'warehouse', 'shipping', 'vendor', 'contract'
    ],
    'rule_patterns': [
        'reorder_point', 'lead_time', 'safety_stock',
        'supplier_rating', 'quality_check'
    ],
    'compliance_frameworks': ['ISO_9001', 'SOX', 'Supply_Chain_Security'],
    'documentation_template': 'supply_chain_operations',
    'stakeholders': ['Procurement', 'Operations', 'Quality Assurance']
}

# Register custom domain
doc_generator.register_custom_domain(
    domain_id="supply_chain",
    domain_config=custom_domain
)

# Use custom domain for classification
classified_rules = doc_generator.classify_with_custom_domains(
    rules=business_rules,
    custom_domains=['supply_chain']
)
```

---

## 📊 Multi-Format Output Examples

### Markdown Documentation

```markdown
# Business Rules Documentation

## Executive Summary

This document provides comprehensive documentation for the **Loan Origination System** business rules extracted during the legacy system modernization project.

### Key Metrics
- **Total Rules Documented**: 25
- **High Priority Rules**: 18 (72%)
- **Compliance Critical**: 12 (48%)
- **Modernization Complexity**: Medium

## Business Rules Catalog

### Financial Services Domain

#### LOAN_001: Minimum Credit Score Requirement
- **Priority**: High
- **Complexity**: Low
- **Business Logic**: `IF credit_score < 650 THEN reject_application`
- **Compliance Impact**: SOX Control ITGC-001
- **Modernization Notes**: Direct API rule translation

#### LOAN_002: Debt-to-Income Ratio Validation  
- **Priority**: High
- **Complexity**: Medium
- **Business Logic**: `IF (monthly_debt / monthly_income) > 0.43 THEN reject_application`
- **Compliance Impact**: Consumer protection regulations
- **Modernization Notes**: Requires income verification service integration

## Implementation Roadmap

### Phase 1: Core Credit Rules (Weeks 1-4)
- Implement credit score validation
- Set up automated decision engine
- Integrate with credit bureau APIs

### Phase 2: Advanced Validation (Weeks 5-8)
- Implement debt-to-income calculations
- Add income verification workflows
- Enhance audit trail capabilities
```

### JSON Output Structure

```json
{
  "documentation_metadata": {
    "generated_date": "2025-08-22T15:30:00Z",
    "generator_version": "2.1.0",
    "source_system": "Legacy COBOL Loan System",
    "total_rules": 25,
    "confidence_score": 0.94
  },
  "executive_summary": {
    "key_metrics": {
      "total_rules": 25,
      "high_priority_rules": 18,
      "compliance_critical_rules": 12,
      "avg_complexity_score": 2.3
    },
    "business_impact": {
      "modernization_effort": "Medium",
      "compliance_risk": "Low", 
      "business_value": "High"
    }
  },
  "business_rules": [
    {
      "rule_id": "LOAN_001",
      "rule_name": "Minimum Credit Score Requirement",
      "domain": "Financial Services",
      "priority": "High",
      "complexity": "Low",
      "business_logic": "IF credit_score < 650 THEN reject_application",
      "compliance_frameworks": ["SOX", "Consumer_Protection"],
      "modernization": {
        "implementation_effort": "Low",
        "api_requirements": ["credit_bureau_api"],
        "estimated_hours": 16
      }
    }
  ],
  "domain_analysis": {
    "Financial Services": {
      "rule_count": 20,
      "percentage": 80.0,
      "complexity_avg": 2.1,
      "priority_distribution": {
        "High": 15,
        "Medium": 4,
        "Low": 1
      }
    }
  }
}
```

### Excel Dashboard Output

The Excel output includes multiple worksheets:

1. **Executive Dashboard**: Key metrics and charts
2. **Rules Inventory**: Detailed rules listing with filters
3. **Domain Analysis**: Pie charts and breakdowns
4. **Implementation Timeline**: Gantt chart view
5. **Compliance Matrix**: Regulatory mapping
6. **Risk Assessment**: Priority and complexity matrix

---

## 🔄 Batch Processing & Automation

### Automated Documentation Pipeline

```python
# Set up automated documentation generation
from pathlib import Path
from datetime import datetime

class DocumentationPipeline:
    def __init__(self, doc_generator):
        self.doc_generator = doc_generator
        self.output_base_path = Path("./generated_docs")
        
    def process_legacy_system(self, system_config):
        """Process entire legacy system for documentation"""
        
        # Extract rules from legacy system
        extracted_rules = self.extract_rules_from_system(system_config)
        
        # Generate multiple documentation formats
        documentation_outputs = {}
        
        # Business stakeholder report (PDF)
        business_doc = self.doc_generator.generate_with_template(
            rules_data=extracted_rules,
            template='business_stakeholder_report',
            output_format='pdf',
            context=f"{system_config['name']} Modernization Analysis"
        )
        documentation_outputs['business_report'] = business_doc
        
        # Technical implementation guide (Markdown)
        tech_doc = self.doc_generator.generate_with_template(
            rules_data=extracted_rules,
            template='technical_implementation_guide',
            output_format='markdown',
            context=f"{system_config['name']} Implementation Guide"
        )
        documentation_outputs['technical_guide'] = tech_doc
        
        # Compliance documentation (JSON + PDF)
        compliance_doc = self.doc_generator.generate_with_template(
            rules_data=extracted_rules,
            template='compliance_documentation',
            output_format=['json', 'pdf'],
            context=f"{system_config['name']} Compliance Package"
        )
        documentation_outputs['compliance_package'] = compliance_doc
        
        # Executive dashboard (Excel)
        dashboard = self.doc_generator.generate_with_template(
            rules_data=extracted_rules,
            template='executive_dashboard',
            output_format='excel',
            context=f"{system_config['name']} Executive Dashboard"
        )
        documentation_outputs['executive_dashboard'] = dashboard
        
        return documentation_outputs
    
    def schedule_regular_updates(self, systems, frequency='weekly'):
        """Schedule regular documentation updates"""
        from apscheduler.schedulers.blocking import BlockingScheduler
        
        scheduler = BlockingScheduler()
        
        if frequency == 'weekly':
            scheduler.add_job(
                func=lambda: self.update_all_documentation(systems),
                trigger="cron",
                day_of_week="sun",
                hour=2,
                minute=0
            )
        
        scheduler.start()

# Set up automated pipeline
pipeline = DocumentationPipeline(doc_generator)

# Process multiple legacy systems
legacy_systems = [
    {
        'name': 'Loan Origination System',
        'type': 'COBOL',
        'source_files': ['./legacy/loan_system/*.cbl'],
        'business_domain': 'Financial Services'
    },
    {
        'name': 'Claims Processing System', 
        'type': 'Java',
        'source_files': ['./legacy/claims/*.java'],
        'business_domain': 'Insurance'
    }
]

# Generate documentation for all systems
for system in legacy_systems:
    outputs = pipeline.process_legacy_system(system)
    print(f"Generated documentation for {system['name']}: {outputs.keys()}")
```

### CI/CD Integration

```yaml
# GitHub Actions workflow for automated documentation
name: Generate Documentation

on:
  push:
    branches: [ main ]
    paths:
      - 'legacy_systems/**'
      - 'business_rules/**'
  
  schedule:
    - cron: '0 2 * * 0'  # Weekly on Sunday at 2 AM

jobs:
  generate-docs:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    
    - name: Generate Business Documentation
      run: |
        python scripts/generate_documentation.py \
          --input ./business_rules \
          --output ./docs/generated \
          --formats markdown,pdf,json \
          --template business_comprehensive
    
    - name: Generate Technical Documentation
      run: |
        python scripts/generate_documentation.py \
          --input ./business_rules \
          --output ./docs/technical \
          --formats markdown,html \
          --template technical_implementation
    
    - name: Upload Documentation Artifacts
      uses: actions/upload-artifact@v3
      with:
        name: generated-documentation
        path: docs/generated/
        retention-days: 90
    
    - name: Deploy to Documentation Site
      if: github.ref == 'refs/heads/main'
      run: |
        mkdocs build
        mkdocs gh-deploy
```

---

## 🛠️ Advanced Features

### Interactive Documentation

```python
# Generate interactive HTML documentation with search
interactive_config = {
    'enable_search': True,
    'include_filters': True,
    'responsive_design': True,
    'navigation_sidebar': True,
    'interactive_elements': [
        'rule_complexity_slider',
        'domain_filter_dropdown',
        'priority_matrix_view',
        'implementation_timeline'
    ],
    'javascript_features': [
        'live_search',
        'dynamic_filtering',
        'chart_interactions',
        'export_functionality'
    ]
}

interactive_doc = doc_generator.generate_interactive_documentation(
    rules_data=business_rules,
    config=interactive_config,
    output_format='html',
    include_assets=True
)

print(f"Interactive documentation: {interactive_doc['index_file']}")
print(f"Features enabled: {interactive_doc['features']}")
```

### Version Control Integration

```python
# Integrate with version control for documentation tracking
class DocumentationVersionControl:
    def __init__(self, repo_path, doc_generator):
        self.repo_path = repo_path
        self.doc_generator = doc_generator
        
    def generate_versioned_documentation(self, rules_data, version_tag):
        """Generate documentation with version control"""
        
        # Create version-specific directory
        version_dir = Path(self.repo_path) / "docs" / "versions" / version_tag
        version_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate documentation
        documentation = self.doc_generator.generate_documentation(
            rules_data=rules_data,
            output_directory=str(version_dir),
            include_version_info=True,
            version_tag=version_tag
        )
        
        # Commit to version control
        self.commit_documentation(version_tag, documentation)
        
        return documentation
    
    def commit_documentation(self, version_tag, documentation):
        """Commit documentation to git"""
        import subprocess
        
        # Add generated files
        subprocess.run(['git', 'add', 'docs/versions/'], cwd=self.repo_path)
        
        # Commit with descriptive message
        commit_message = f"docs: Generate documentation for {version_tag}\n\n" \
                        f"- Rules documented: {documentation['rules_count']}\n" \
                        f"- Output formats: {', '.join(documentation['formats'])}\n" \
                        f"- Generated: {documentation['timestamp']}"
        
        subprocess.run(['git', 'commit', '-m', commit_message], cwd=self.repo_path)
        
        # Tag the commit
        subprocess.run(['git', 'tag', f"docs-{version_tag}"], cwd=self.repo_path)

# Use version control integration
vc_integration = DocumentationVersionControl(
    repo_path="./",
    doc_generator=doc_generator
)

versioned_docs = vc_integration.generate_versioned_documentation(
    rules_data=business_rules,
    version_tag="v2.1.0"
)
```

---

## 🎯 Best Practices

### Documentation Quality Guidelines

```python
# Quality validation for generated documentation
class DocumentationQualityValidator:
    def __init__(self):
        self.quality_metrics = {
            'completeness': 0.95,      # 95% rule coverage required
            'clarity': 0.90,           # 90% clarity score required
            'accuracy': 0.99,          # 99% accuracy required
            'consistency': 0.95        # 95% consistency required
        }
    
    def validate_documentation(self, documentation):
        """Validate documentation quality"""
        validation_results = {}
        
        # Check completeness
        validation_results['completeness'] = self.check_completeness(documentation)
        
        # Check clarity
        validation_results['clarity'] = self.check_clarity(documentation)
        
        # Check accuracy
        validation_results['accuracy'] = self.check_accuracy(documentation)
        
        # Check consistency
        validation_results['consistency'] = self.check_consistency(documentation)
        
        # Overall quality score
        overall_score = sum(validation_results.values()) / len(validation_results)
        validation_results['overall_quality'] = overall_score
        
        # Quality recommendations
        validation_results['recommendations'] = self.generate_recommendations(validation_results)
        
        return validation_results
    
    def check_completeness(self, documentation):
        """Check if all rules are properly documented"""
        total_rules = documentation['total_rules']
        documented_rules = len(documentation['business_rules'])
        
        completeness_score = documented_rules / total_rules
        return min(completeness_score, 1.0)
    
    def generate_recommendations(self, validation_results):
        """Generate quality improvement recommendations"""
        recommendations = []
        
        for metric, score in validation_results.items():
            if metric != 'overall_quality' and score < self.quality_metrics.get(metric, 0.9):
                recommendations.append({
                    'metric': metric,
                    'current_score': score,
                    'target_score': self.quality_metrics[metric],
                    'improvement_actions': self.get_improvement_actions(metric, score)
                })
        
        return recommendations

# Validate documentation quality
validator = DocumentationQualityValidator()
quality_report = validator.validate_documentation(generated_documentation)

if quality_report['overall_quality'] >= 0.90:
    print("✅ Documentation meets quality standards")
else:
    print("⚠️ Documentation quality improvements needed:")
    for rec in quality_report['recommendations']:
        print(f"  - {rec['metric']}: {rec['current_score']:.2f} → {rec['target_score']:.2f}")
```

### Performance Optimization

```python
# Optimize documentation generation for large rule sets
class OptimizedDocumentationGenerator:
    def __init__(self, base_generator):
        self.base_generator = base_generator
        self.cache = {}
        
    def generate_with_caching(self, rules_data, cache_key=None):
        """Generate documentation with intelligent caching"""
        
        if cache_key and cache_key in self.cache:
            cached_doc = self.cache[cache_key]
            
            # Check if rules have changed
            rules_hash = self.calculate_rules_hash(rules_data)
            if cached_doc['rules_hash'] == rules_hash:
                print("📋 Using cached documentation")
                return cached_doc['documentation']
        
        # Generate new documentation
        documentation = self.base_generator.generate_documentation(rules_data)
        
        # Cache the result
        if cache_key:
            self.cache[cache_key] = {
                'documentation': documentation,
                'rules_hash': self.calculate_rules_hash(rules_data),
                'generated_at': datetime.now()
            }
        
        return documentation
    
    def parallel_generation(self, rule_sets):
        """Generate documentation for multiple rule sets in parallel"""
        import concurrent.futures
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = []
            
            for i, rules in enumerate(rule_sets):
                future = executor.submit(
                    self.generate_with_caching,
                    rules,
                    f"ruleset_{i}"
                )
                futures.append(future)
            
            # Collect results
            results = []
            for future in concurrent.futures.as_completed(futures):
                results.append(future.result())
            
            return results

# Use optimized generator for large-scale documentation
optimized_generator = OptimizedDocumentationGenerator(doc_generator)

# Process multiple legacy systems efficiently
large_rule_sets = [
    extract_rules_from_system("system_1"),
    extract_rules_from_system("system_2"), 
    extract_rules_from_system("system_3"),
    extract_rules_from_system("system_4")
]

parallel_docs = optimized_generator.parallel_generation(large_rule_sets)
print(f"Generated {len(parallel_docs)} documentation sets in parallel")
```

---

## 🎯 Next Steps

1. **[Configure Templates](../getting-started/configuration.md)** - Set up documentation templates
2. **[API Reference](../api/agents/rule-documentation-generator.md)** - Complete API documentation
3. **[Business Rule Extraction](business-rule-extraction.md)** - Extract rules for documentation
4. **[Enterprise Integration](../examples/enterprise-integration.md)** - Production deployment patterns

---

*Built for enterprise documentation excellence. Powered by intelligent automation and multi-format output capabilities.*