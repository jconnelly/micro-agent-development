"""
Enterprise Privacy Components Module

This module contains the modularized components of the EnterpriseDataPrivacyAgent,
broken down for improved maintainability, performance, and testability.

Created as part of Medium Priority Task 1: Breaking down large classes into focused modules.

Components:
- PiiDetectionEngine: Core PII detection with grep tool integration and high-performance pattern matching
- FileProcessor: Standard file processing, encoding detection, and content handling
- StreamingProcessor: Large file streaming operations and memory optimization for enterprise-scale documents
- BatchProcessor: Batch processing, concurrent operations, and parallel file handling
"""

from .PiiDetectionEngine import PiiDetectionEngine
from .FileProcessor import FileProcessor
from .StreamingProcessor import StreamingProcessor
from .BatchProcessor import BatchProcessor

__all__ = [
    'PiiDetectionEngine',
    'FileProcessor', 
    'StreamingProcessor',
    'BatchProcessor'
]

__version__ = '1.0.0'
__author__ = 'Medium Priority Task 1 - Large Class Modularization'