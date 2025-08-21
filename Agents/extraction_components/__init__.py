"""
Extraction Components Module for Business Rule Extraction

This module contains the modularized components of the BusinessRuleExtractionAgent,
broken down for improved maintainability, performance, and testability.

Created as part of Phase 16 Task 2: BusinessRuleExtractionAgent Modularization.

Components:
- LanguageProcessor: Language detection and context extraction
- ChunkProcessor: File chunking and processing strategy
- RuleValidator: Rule validation, deduplication, and completeness analysis
- ExtractionEngine: Core LLM interaction and rule extraction
"""

from .LanguageProcessor import LanguageProcessor
from .ChunkProcessor import ChunkProcessor
from .RuleValidator import RuleValidator
from .ExtractionEngine import ExtractionEngine

__all__ = [
    'LanguageProcessor',
    'ChunkProcessor', 
    'RuleValidator',
    'ExtractionEngine'
]

__version__ = '1.0.0'
__author__ = 'Phase 16 Performance Optimization'