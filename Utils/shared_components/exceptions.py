#!/usr/bin/env python3

"""
Standardized Exception Hierarchy

Enhanced exception classes for standardized error handling across agents
with security features, context management, and troubleshooting information.

This module was extracted from StandardImports.py as part of Phase 14
code quality improvements to break down large class files.
"""

import uuid
from datetime import datetime as dt, timezone
from typing import Any, Dict, List

from .message_security import SecureMessageFormatter


class StandardizedException(Exception):
    """
    Enhanced base exception class for standardized error handling across agents.
    
    Phase 11 Enhancement: Improved exception hierarchy with better context management,
    sanitized error messages, and performance tracking capabilities.
    """
    
    def __init__(self, message: str, error_code: str = None, 
                 context: Dict[str, Any] = None, original_error: Exception = None,
                 request_id: str = None, agent_name: str = None):
        """
        Initialize standardized exception with enhanced context.
        
        Args:
            message: Human-readable error message
            error_code: Machine-readable error code
            context: Additional context information
            original_error: Original exception that caused this error
            request_id: Associated request ID for audit trail
            agent_name: Name of the agent that raised this exception
        """
        # Sanitize the error message for security
        sanitized_message = SecureMessageFormatter.sanitize_error_message(message, request_id)
        super().__init__(sanitized_message)
        
        self.error_code = error_code or "STANDARD_ERROR"
        self.context = SecureMessageFormatter.create_safe_context_dict(context or {})
        self.original_error = original_error
        self.request_id = request_id
        self.agent_name = agent_name
        self.timestamp = dt.now(timezone.utc)
        self.error_id = f"err_{uuid.uuid4().hex[:8]}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for logging/serialization."""
        return {
            'error_id': self.error_id,
            'message': str(self),
            'error_code': self.error_code,
            'context': self.context,
            'timestamp': self.timestamp.isoformat(),
            'request_id': self.request_id,
            'agent_name': self.agent_name,
            'original_error': str(self.original_error) if self.original_error else None,
            'error_category': self.__class__.__name__
        }
    
    def get_troubleshooting_info(self) -> Dict[str, List[str]]:
        """Get troubleshooting information for this error type."""
        return {
            'common_causes': [
                'Invalid input parameters',
                'System resource constraints',
                'Configuration issues'
            ],
            'suggested_solutions': [
                'Check input parameter format and values',
                'Verify system resources are available',
                'Review agent configuration settings'
            ]
        }


class PerformanceException(StandardizedException):
    """
    Exception for performance-related issues in Phase 11 optimizations.
    """
    
    def __init__(self, message: str, performance_metrics: Dict[str, Any] = None, **kwargs):
        super().__init__(message, error_code="PERFORMANCE_ERROR", **kwargs)
        self.performance_metrics = performance_metrics or {}
    
    def get_troubleshooting_info(self) -> Dict[str, List[str]]:
        return {
            'common_causes': [
                'Large file processing without streaming',
                'Inefficient algorithm implementation',
                'Memory constraints',
                'Network latency issues'
            ],
            'suggested_solutions': [
                'Enable streaming processing for large files',
                'Use optimized single-pass algorithms',
                'Increase memory allocation',
                'Implement retry logic with exponential backoff'
            ]
        }


class ConfigurationException(StandardizedException):
    """
    Exception for configuration management issues.
    """
    
    def __init__(self, config_name: str, **kwargs):
        message = f"Configuration error for '{config_name}'"
        super().__init__(message, error_code="CONFIG_ERROR", **kwargs)
        self.config_name = config_name
    
    def get_troubleshooting_info(self) -> Dict[str, List[str]]:
        return {
            'common_causes': [
                'Missing configuration files',
                'Invalid configuration format',
                'Permission issues accessing config directory',
                'Corrupted configuration data'
            ],
            'suggested_solutions': [
                'Verify configuration files exist in config/ directory',
                'Validate configuration file syntax (YAML/JSON)',
                'Check file permissions for configuration directory',
                'Use fallback configuration if external config fails'
            ]
        }


class ToolIntegrationException(StandardizedException):
    """
    Exception for tool integration and interface contract issues.
    """
    
    def __init__(self, tool_name: str, operation: str = None, **kwargs):
        message = f"Tool integration error for '{tool_name}'"
        if operation:
            message += f" during '{operation}'"
        super().__init__(message, error_code="TOOL_ERROR", **kwargs)
        self.tool_name = tool_name
        self.operation = operation
    
    def get_troubleshooting_info(self) -> Dict[str, List[str]]:
        return {
            'common_causes': [
                'Tool interface contract violations',
                'Missing tool dependencies',
                'Invalid tool parameters',
                'Tool execution environment issues'
            ],
            'suggested_solutions': [
                'Verify tool implements required interface protocols',
                'Check tool availability and installation',
                'Validate input parameters match tool interface',
                'Use tool fallback mechanisms when available'
            ]
        }