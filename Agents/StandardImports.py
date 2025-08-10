#!/usr/bin/env python3

"""
Standardized Import Utilities for Agent Framework

Provides consistent import patterns and utilities across all agent classes,
eliminating code duplication and ensuring consistent import behavior.

This module is part of Phase 10 Security & Code Quality improvements.
"""

# Standard library imports - standardized across all agents
import datetime
import json
import os
import re
import sys
import uuid
from pathlib import Path

# Type annotations - standardized set used across framework
from typing import Any, Callable, Dict, List, Optional, Pattern, Tuple, Union

# DateTime utilities - standardized import pattern
from datetime import datetime as dt, timezone


class ImportUtils:
    """
    Utility class for handling common import patterns and dependencies.
    
    Centralizes the logic for importing Utils modules with fallback handling
    that all agents currently duplicate.
    """
    
    @staticmethod
    def import_utils(*module_names: str) -> Dict[str, Any]:
        """
        Import Utils modules with automatic fallback from relative to absolute imports.
        
        Args:
            *module_names: Names of modules to import from Utils package
            
        Returns:
            Dictionary mapping module names to imported modules
            
        Raises:
            ImportError: If modules cannot be imported via either method
        """
        imported_modules = {}
        
        for module_name in module_names:
            try:
                # Try relative import first (when running as part of package)
                relative_import = f"..Utils.{module_name}"
                module = __import__(relative_import, fromlist=[module_name], level=1)
                imported_modules[module_name] = getattr(module, module_name)
            except (ImportError, ValueError):
                try:
                    # Fallback to absolute import (when running standalone)
                    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                    if parent_dir not in sys.path:
                        sys.path.insert(0, parent_dir)
                    
                    absolute_import = f"Utils.{module_name}"
                    module = __import__(absolute_import, fromlist=[module_name])
                    imported_modules[module_name] = getattr(module, module_name)
                except ImportError as e:
                    raise ImportError(f"Could not import {module_name} from Utils: {e}")
        
        return imported_modules
    
    @staticmethod
    def import_single_utils_module(module_name: str) -> Any:
        """
        Import a single Utils module with automatic fallback handling.
        
        Args:
            module_name: Name of the module to import from Utils
            
        Returns:
            The imported module
            
        Raises:
            ImportError: If module cannot be imported
        """
        result = ImportUtils.import_utils(module_name)
        return result[module_name]


# Pre-import commonly used Utils modules for convenience
def get_common_utils() -> Dict[str, Any]:
    """
    Get commonly used Utils modules with standardized import handling.
    
    Returns:
        Dictionary with commonly used utility modules
    """
    try:
        return ImportUtils.import_utils(
            'RequestIdGenerator',
            'TimeUtils', 
            'JsonUtils',
            'TextProcessingUtils',
            'config_loader'
        )
    except ImportError:
        # Return None if utils not available - agents should handle gracefully
        return {}


# Standardized import aliases for consistency across agents
JsonType = Union[Dict[str, Any], List[Any], str, int, float, bool, None]
CallableType = Callable[..., Any]
PathType = Union[str, Path]

# Common regex patterns used across agents
COMMON_PATTERNS = {
    'safe_filename': re.compile(r'[<>:"/\\|?*\x00-\x1f]'),
    'path_traversal': re.compile(r'\.\.[/\\]'),
    'whitespace_cleanup': re.compile(r'\s+')
}


class SecureMessageFormatter:
    """
    Utility class for sanitizing error messages and log entries to prevent
    information disclosure vulnerabilities.
    
    Part of Phase 10 Security & Code Quality improvements.
    """
    
    # Patterns that should be redacted from error messages
    SENSITIVE_PATTERNS = {
        'file_path': re.compile(r'[/\\][^/\\]+[/\\][^/\\]+[/\\][^/\\]+'),  # Redact deep file paths
        'pii_content': re.compile(r'\b\d{3}-\d{2}-\d{4}\b|\b\d{16}\b|\b\d{3}-\d{3}-\d{4}\b'),  # SSN, CC, phone patterns
        'api_keys': re.compile(r'[A-Za-z0-9]{32,}'),  # Long alphanumeric strings (API keys)
        'tokens': re.compile(r'token[_-]?\w+', re.IGNORECASE),
        'passwords': re.compile(r'password[_-]?\w+', re.IGNORECASE)
    }
    
    @staticmethod
    def sanitize_error_message(message: str, request_id: str = None) -> str:
        """
        Sanitize error message to remove potentially sensitive information.
        
        Args:
            message: Original error message
            request_id: Optional request ID for tracking
            
        Returns:
            Sanitized error message safe for logging
        """
        if not message:
            return "Unknown error occurred"
        
        sanitized = str(message)
        
        # Apply sanitization patterns
        for pattern_name, pattern in SecureMessageFormatter.SENSITIVE_PATTERNS.items():
            sanitized = pattern.sub(f'[REDACTED_{pattern_name.upper()}]', sanitized)
        
        # Truncate very long messages to prevent log flooding
        if len(sanitized) > 500:
            sanitized = sanitized[:497] + "..."
        
        # Add request ID if available for tracking
        if request_id:
            sanitized = f"[{request_id}] {sanitized}"
        
        return sanitized
    
    @staticmethod
    def sanitize_data_for_logging(data: Any, max_length: int = 100) -> str:
        """
        Safely format data for logging without exposing sensitive information.
        
        Args:
            data: Data to format for logging
            max_length: Maximum length of logged data
            
        Returns:
            Safe representation of data for logging
        """
        if data is None:
            return "None"
        
        # Convert to string representation
        if isinstance(data, (dict, list)):
            data_str = f"{type(data).__name__} with {len(data)} items"
        elif isinstance(data, str):
            # Check if it looks like PII and redact
            for pattern in SecureMessageFormatter.SENSITIVE_PATTERNS.values():
                if pattern.search(data):
                    return f"[REDACTED_SENSITIVE_STRING] (length: {len(data)})"
            
            # Truncate long strings
            if len(data) > max_length:
                data_str = data[:max_length-3] + "..."
            else:
                data_str = data
        else:
            data_str = str(data)[:max_length]
        
        return data_str
    
    @staticmethod
    def create_safe_context_dict(context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a safe version of context dictionary for logging.
        
        Args:
            context: Original context dictionary
            
        Returns:
            Sanitized context dictionary
        """
        if not context:
            return {}
        
        safe_context = {}
        for key, value in context.items():
            # Redact sensitive keys
            if any(sensitive in key.lower() for sensitive in ['password', 'token', 'key', 'secret', 'pii']):
                safe_context[key] = "[REDACTED]"
            else:
                safe_context[key] = SecureMessageFormatter.sanitize_data_for_logging(value)
        
        return safe_context


class StandardizedException(Exception):
    """
    Base exception class for standardized error handling across agents.
    
    Provides consistent exception structure and metadata for better
    error tracking and debugging across the agent framework.
    """
    
    def __init__(self, message: str, error_code: str = None, 
                 context: Dict[str, Any] = None, original_error: Exception = None):
        """
        Initialize standardized exception.
        
        Args:
            message: Human-readable error message
            error_code: Machine-readable error code
            context: Additional context information
            original_error: Original exception that caused this error
        """
        super().__init__(message)
        self.error_code = error_code
        self.context = context or {}
        self.original_error = original_error
        self.timestamp = dt.now(timezone.utc)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for logging/serialization."""
        return {
            'message': str(self),
            'error_code': self.error_code,
            'context': self.context,
            'timestamp': self.timestamp.isoformat(),
            'original_error': str(self.original_error) if self.original_error else None
        }


# Export commonly used items for easy importing
__all__ = [
    # Standard library re-exports
    'datetime', 'json', 'os', 're', 'sys', 'uuid', 'Path',
    
    # Type annotations
    'Any', 'Callable', 'Dict', 'List', 'Optional', 'Pattern', 'Tuple', 'Union',
    
    # DateTime utilities 
    'dt', 'timezone',
    
    # Custom types
    'JsonType', 'CallableType', 'PathType',
    
    # Utilities
    'ImportUtils', 'get_common_utils', 'COMMON_PATTERNS',
    
    # Security utilities
    'SecureMessageFormatter',
    
    # Exception handling
    'StandardizedException'
]