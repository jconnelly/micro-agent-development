#!/usr/bin/env python3

"""
Secure Message Formatting Utilities

Utility class for sanitizing error messages and log entries to prevent
information disclosure vulnerabilities.

This module was extracted from StandardImports.py as part of Phase 14
code quality improvements to break down large class files.
"""

import re
from typing import Any, Dict


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