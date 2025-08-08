"""
Micro-Agent Development Platform - AI Agents Package

This package contains enterprise-grade AI agents for business process automation,
legacy system modernization, and compliance management.

Available Agents:
- BusinessRuleExtractionAgent: Extract business rules from legacy systems
- ApplicationTriageAgent: Intelligent document processing and routing
- PersonalDataProtectionAgent: GDPR/CCPA compliant PII detection and protection
- RuleDocumentationGeneratorAgent: Automated business rule documentation
- ComplianceMonitoringAgent: Enterprise audit trail and compliance management
- AdvancedDocumentationAgent: Tool-integrated documentation platform
- EnterpriseDataPrivacyAgent: High-performance PII processing for large-scale operations

Foundation:
- BaseAgent: Abstract base class providing common functionality
- Exception classes: Comprehensive error handling hierarchy
"""

# Import all agents for easier access
from .BusinessRuleExtractionAgent import BusinessRuleExtractionAgent
from .ApplicationTriageAgent import ApplicationTriageAgent
from .PersonalDataProtectionAgent import PersonalDataProtectionAgent
from .RuleDocumentationGeneratorAgent import RuleDocumentationGeneratorAgent
from .ComplianceMonitoringAgent import ComplianceMonitoringAgent
from .AdvancedDocumentationAgent import AdvancedDocumentationAgent
from .EnterpriseDataPrivacyAgent import EnterpriseDataPrivacyAgent

# Import foundation classes
from .BaseAgent import BaseAgent
from .Exceptions import *

__all__ = [
    # Core Agents
    'BusinessRuleExtractionAgent',
    'ApplicationTriageAgent', 
    'PersonalDataProtectionAgent',
    'RuleDocumentationGeneratorAgent',
    'ComplianceMonitoringAgent',
    
    # Enhanced Agents
    'AdvancedDocumentationAgent',
    'EnterpriseDataPrivacyAgent',
    
    # Foundation
    'BaseAgent',
    
    # Exception classes exported from Exceptions module
    'AgentError',
    'ConfigurationError',
    'ValidationError',
    'RuleExtractionError',
    'PIIDetectionError',
    'DocumentationError',
    'ComplianceError',
    'PerformanceError',
    'IntegrationError',
    'SecurityError'
]

# Package metadata
__version__ = "1.0.0"
__author__ = "Micro-Agent Development Team"
__description__ = "Enterprise AI Agent Platform for Business Process Automation"