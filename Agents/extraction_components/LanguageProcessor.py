"""
Language Processing Component for Business Rule Extraction

This module handles language detection, file context extraction, and language-specific
processing parameters for the BusinessRuleExtractionAgent.

Extracted from BusinessRuleExtractionAgent.py as part of Phase 16 Task 2 modularization.
"""

import time
from typing import Dict, Any, List, Optional, Tuple
from functools import lru_cache

# Import Language Detection System (Phase 15A)
from Utils.language_detection import LanguageDetector, DetectionResult, LanguageDetectionError


class LanguageProcessor:
    """
    Handles language detection and context extraction for business rule extraction.
    
    Responsibilities:
    - Language detection from file content and extensions
    - File context extraction for enhanced processing
    - Language-specific chunking parameter determination
    """
    
    def __init__(self, agent_config: Dict[str, Any]):
        """Initialize the language processor with configuration."""
        self.agent_config = agent_config
        self.language_detector = LanguageDetector()
        
        # Cache configuration
        processing_config = self.agent_config.get('processing_limits', {})
        self._max_context_lines = processing_config.get('max_context_lines', 50)
        
    def detect_language_and_get_chunking_params(self, filename: str, content: str) -> Tuple[DetectionResult, Dict[str, Any]]:
        """
        Detect language and determine optimal chunking parameters.
        
        Args:
            filename: Name of the file being processed
            content: File content for language detection
            
        Returns:
            Tuple of (DetectionResult, chunking_parameters)
        """
        start_time = time.time()
        
        try:
            # Use the language detector to identify the programming language
            detection_result = self.language_detector.detect_language(content, filename)
            
            # Get language-specific chunking parameters
            chunking_params = self.language_detector.get_chunking_params(detection_result.language)
            
            detection_time = time.time() - start_time
            
            # Log detection results
            self._log_detection_result(detection_result, chunking_params, detection_time)
            
            return detection_result, chunking_params
            
        except LanguageDetectionError as e:
            # Fall back to default parameters if detection fails
            fallback_params = {
                'preferred_size': self.agent_config.get('processing_limits', {}).get('chunking_line_threshold', 175),
                'overlap_size': self.agent_config.get('processing_limits', {}).get('chunk_overlap_size', 25),
                'min_size': self.agent_config.get('processing_limits', {}).get('min_chunk_lines', 10)
            }
            
            # Create fallback detection result
            fallback_result = DetectionResult(
                language="unknown",
                confidence=0.0,
                file_extension=filename.split('.')[-1] if '.' in filename else "",
                detected_patterns=[],
                business_domain="general"
            )
            
            return fallback_result, fallback_params
    
    def extract_file_context(self, lines: List[str], max_lines: int = None) -> List[str]:
        """
        Extract context lines from the beginning of the file.
        
        Args:
            lines: All lines from the file
            max_lines: Maximum number of context lines to extract
            
        Returns:
            List of context lines
        """
        if max_lines is None:
            max_lines = self._max_context_lines
            
        context_lines = []
        
        # Extract header comments, imports, and initial declarations
        for line in lines[:max_lines]:
            stripped = line.strip()
            
            # Include comments, imports, class/function declarations
            if (stripped.startswith(('*', '//', '#', 'import', 'from', 'package', 'using', 'include')) or
                'class ' in line or 'def ' in line or 'function ' in line or
                'IDENTIFICATION DIVISION' in line or 'PROGRAM-ID' in line):
                context_lines.append(line)
                
        return context_lines[:max_lines]
    
    @lru_cache(maxsize=256)
    def cached_extract_file_context(self, lines_tuple: tuple, max_lines: int = None) -> tuple:
        """
        Cached version of file context extraction.
        
        Args:
            lines_tuple: Tuple of file lines (for caching)
            max_lines: Maximum number of context lines
            
        Returns:
            Tuple of context lines
        """
        if max_lines is None:
            max_lines = self._max_context_lines
            
        lines = list(lines_tuple)
        context_lines = self.extract_file_context(lines, max_lines)
        return tuple(context_lines)
    
    def _log_detection_result(self, detection_result: DetectionResult, 
                            chunking_params: Dict[str, Any], detection_time: float) -> None:
        """Log language detection results."""
        # This would typically use the agent's logging system
        # For now, we'll keep it simple
        pass
    
    def get_language_specific_prompt_enhancements(self, language: str) -> Dict[str, str]:
        """
        Get language-specific prompt enhancements for better rule extraction.
        
        Args:
            language: Detected programming language
            
        Returns:
            Dictionary with language-specific prompt additions
        """
        language_enhancements = {
            'cobol': {
                'context_info': 'Legacy COBOL mainframe application with embedded business rules',
                'pattern_hints': 'Look for PERFORM statements, conditional logic (IF-THEN-ELSE), and data validation routines',
                'business_focus': 'Insurance, banking, and financial services business logic'
            },
            'java': {
                'context_info': 'Enterprise Java application with object-oriented business logic',
                'pattern_hints': 'Look for business logic in service classes, validation methods, and configuration',
                'business_focus': 'Enterprise application business rules and workflows'
            },
            'pascal': {
                'context_info': 'Legacy Pascal application with procedural business logic',
                'pattern_hints': 'Look for procedure calls, case statements, and validation logic',
                'business_focus': 'Scientific, educational, or legacy system business rules'
            },
            'default': {
                'context_info': 'Legacy application with embedded business rules',
                'pattern_hints': 'Look for conditional logic, validation routines, and decision points',
                'business_focus': 'General business logic and workflows'
            }
        }
        
        return language_enhancements.get(language.lower(), language_enhancements['default'])