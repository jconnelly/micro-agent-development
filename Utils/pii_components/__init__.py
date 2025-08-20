"""
PII Components Package

Focused components for Personal Data Protection Agent functionality,
split from the large PersonalDataProtectionAgent.py file for better
maintainability and organization.

Components:
- security: Secure token storage and encryption utilities
- types: PII type definitions and enums (PIIType, MaskingStrategy, PIIContext)
- core_agent: Main PersonalDataProtectionAgent class (will be created)

This package was created as part of Phase 14 code quality improvements
to break down large class files into focused modules.
"""

# Import all PII components for easy access
from .security import SecureTokenStorage
from .types import PIIType, MaskingStrategy, PIIContext

__all__ = [
    # Security components
    'SecureTokenStorage',
    
    # Type definitions
    'PIIType', 'MaskingStrategy', 'PIIContext'
]