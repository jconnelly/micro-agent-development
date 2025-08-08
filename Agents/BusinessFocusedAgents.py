#!/usr/bin/env python3

"""
Business-Focused Agent Aliases

This module provides business-friendly names for all agent classes while
maintaining backward compatibility with existing code.

Target audience: Business teams, analysts, product owners

Author: AI Development Team
Version: 1.0.0
"""

# Import original technical classes
from .LegacyRuleExtractionAndTranslatorAgent import LegacyRuleExtractionAgent
from .IntelligentSubmissionTriageAgent import IntelligentSubmissionTriageAgent
from .PIIScrubbingAgent import PIIScrubbingAgent
from .RuleDocumentationAgent import RuleDocumentationAgent
from .AuditingAgent import AgentAuditing
from .ToolIntegratedDocumentationAgent import ToolIntegratedDocumentationAgent

# Create business-focused aliases
BusinessRuleExtractorAgent = LegacyRuleExtractionAgent
ApplicationTriageAgent = IntelligentSubmissionTriageAgent
PersonalDataProtectionAgent = PIIScrubbingAgent
RuleDocumentationGeneratorAgent = RuleDocumentationAgent
ComplianceMonitoringAgent = AgentAuditing
AdvancedDocumentationAgent = ToolIntegratedDocumentationAgent

# Export all business-focused names
__all__ = [
    'BusinessRuleExtractorAgent',
    'ApplicationTriageAgent', 
    'PersonalDataProtectionAgent',
    'RuleDocumentationGeneratorAgent',
    'ComplianceMonitoringAgent',
    'AdvancedDocumentationAgent'
]