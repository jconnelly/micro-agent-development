"""
Standardized Error Handling Utilities for Agent Framework

This module provides consistent error handling patterns across all agents,
implementing Phase 14 Medium Priority Task #5: Standardize error handling patterns.

Key features:
- Consistent exception mapping and categorization
- Standardized error recovery strategies  
- Unified logging and audit integration
- Context preservation across error boundaries
- Business-friendly error messages for stakeholders
"""

import json
import time
import traceback
import uuid
from contextlib import contextmanager
from typing import Any, Dict, List, Optional, Callable, Union, Type
from enum import Enum
from datetime import datetime, timezone

# Import standardized exceptions
from Agents.Exceptions import (
    ValidationError,
    APITimeoutError, 
    ConfigurationError,
    PIIProcessingError,
    RuleExtractionError,
    DocumentationError,
    AuditingError,
    TriageProcessingError,
    ToolIntegrationError
)


class ErrorSeverity(Enum):
    """Standardized error severity levels for consistent classification."""
    LOW = "low"           # Minor issues that don't affect core functionality
    MEDIUM = "medium"     # Issues that affect some functionality but system remains stable
    HIGH = "high"         # Serious issues that significantly impact functionality
    CRITICAL = "critical" # System-threatening issues requiring immediate attention


class ErrorCategory(Enum):
    """Standardized error categories for consistent error classification."""
    VALIDATION = "validation"         # Input validation and data format errors
    API = "api"                      # LLM API and external service errors
    CONFIGURATION = "configuration"  # Configuration and setup errors
    PROCESSING = "processing"        # Data processing and business logic errors
    SYSTEM = "system"                # System resource and infrastructure errors
    NETWORK = "network"              # Network connectivity and timeout errors
    SECURITY = "security"            # Security and authentication errors
    DATA = "data"                    # Data integrity and storage errors


class ErrorRecoveryStrategy(Enum):
    """Standardized error recovery strategies."""
    RETRY = "retry"                   # Retry the operation with exponential backoff
    FALLBACK = "fallback"            # Use fallback method or default values
    SKIP = "skip"                    # Skip the failing operation and continue
    ABORT = "abort"                  # Abort the entire operation
    PARTIAL = "partial"              # Continue with partial results
    USER_INPUT = "user_input"        # Require user intervention


class StandardErrorContext:
    """
    Standardized error context container for comprehensive error information.
    """
    
    def __init__(self,
                 operation: str,
                 agent_name: str,
                 request_id: str = None,
                 user_context: Dict[str, Any] = None,
                 system_context: Dict[str, Any] = None):
        """
        Initialize error context.
        
        Args:
            operation: Name of the operation that failed
            agent_name: Name of the agent where error occurred
            request_id: Optional request ID for tracking
            user_context: User-provided context (sanitized for security)
            system_context: System context (performance metrics, resource usage)
        """
        self.operation = operation
        self.agent_name = agent_name
        self.request_id = request_id or f"err_{uuid.uuid4().hex[:8]}"
        self.user_context = user_context or {}
        self.system_context = system_context or {}
        self.timestamp = datetime.now(timezone.utc)
        self.error_id = f"err_{uuid.uuid4().hex[:12]}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error context to dictionary for logging/serialization."""
        return {
            'error_id': self.error_id,
            'operation': self.operation,
            'agent_name': self.agent_name,
            'request_id': self.request_id,
            'timestamp': self.timestamp.isoformat(),
            'user_context': self.user_context,
            'system_context': self.system_context
        }


class StandardErrorHandler:
    """
    Centralized error handler providing consistent error processing across all agents.
    """
    
    # Exception type mapping to categories
    EXCEPTION_CATEGORY_MAP = {
        ValidationError: ErrorCategory.VALIDATION,
        APITimeoutError: ErrorCategory.API,
        ConfigurationError: ErrorCategory.CONFIGURATION,
        PIIProcessingError: ErrorCategory.PROCESSING,
        RuleExtractionError: ErrorCategory.PROCESSING,
        DocumentationError: ErrorCategory.PROCESSING,
        AuditingError: ErrorCategory.SYSTEM,
        TriageProcessingError: ErrorCategory.PROCESSING,
        ToolIntegrationError: ErrorCategory.SYSTEM,
        ConnectionError: ErrorCategory.NETWORK,
        TimeoutError: ErrorCategory.NETWORK,
        FileNotFoundError: ErrorCategory.VALIDATION,
        PermissionError: ErrorCategory.SECURITY,
        json.JSONDecodeError: ErrorCategory.DATA,
        KeyboardInterrupt: ErrorCategory.SYSTEM
    }
    
    # Default recovery strategies by category
    DEFAULT_RECOVERY_STRATEGIES = {
        ErrorCategory.VALIDATION: ErrorRecoveryStrategy.ABORT,
        ErrorCategory.API: ErrorRecoveryStrategy.RETRY,
        ErrorCategory.CONFIGURATION: ErrorRecoveryStrategy.FALLBACK,
        ErrorCategory.PROCESSING: ErrorRecoveryStrategy.PARTIAL,
        ErrorCategory.SYSTEM: ErrorRecoveryStrategy.ABORT,
        ErrorCategory.NETWORK: ErrorRecoveryStrategy.RETRY,
        ErrorCategory.SECURITY: ErrorRecoveryStrategy.ABORT,
        ErrorCategory.DATA: ErrorRecoveryStrategy.FALLBACK
    }
    
    def __init__(self, logger: Any = None, audit_system: Any = None):
        """
        Initialize error handler with logging and audit capabilities.
        
        Args:
            logger: Agent logger instance for error logging
            audit_system: Audit system for compliance logging
        """
        self.logger = logger
        self.audit_system = audit_system
        self.error_history = []  # Track recent errors for pattern analysis
        self.max_history = 100   # Keep last 100 errors
    
    def handle_error(self,
                    exception: Exception,
                    context: StandardErrorContext,
                    recovery_strategy: ErrorRecoveryStrategy = None,
                    severity: ErrorSeverity = None) -> Dict[str, Any]:
        """
        Handle an error with standardized processing.
        
        Args:
            exception: The exception that occurred
            context: Error context information
            recovery_strategy: Override default recovery strategy
            severity: Override default severity assessment
            
        Returns:
            Dictionary with error analysis and recovery recommendations
        """
        # Categorize the error
        category = self._categorize_error(exception)
        severity = severity or self._assess_severity(exception, category)
        recovery_strategy = recovery_strategy or self.DEFAULT_RECOVERY_STRATEGIES.get(
            category, ErrorRecoveryStrategy.ABORT
        )
        
        # Create comprehensive error record
        error_record = {
            'error_id': context.error_id,
            'timestamp': context.timestamp.isoformat(),
            'exception_type': type(exception).__name__,
            'exception_message': str(exception),
            'category': category.value,
            'severity': severity.value,
            'recovery_strategy': recovery_strategy.value,
            'context': context.to_dict(),
            'stack_trace': self._get_safe_stack_trace(),
            'troubleshooting': self._generate_troubleshooting_info(exception, category)
        }
        
        # Log the error appropriately based on severity
        self._log_error(error_record, severity)
        
        # Audit the error if audit system available
        self._audit_error(error_record)
        
        # Store in history for pattern analysis
        self._add_to_history(error_record)
        
        return error_record
    
    def _categorize_error(self, exception: Exception) -> ErrorCategory:
        """Categorize an exception based on its type."""
        exception_type = type(exception)
        
        # Check direct mapping first
        if exception_type in self.EXCEPTION_CATEGORY_MAP:
            return self.EXCEPTION_CATEGORY_MAP[exception_type]
        
        # Check inheritance hierarchy
        for exc_type, category in self.EXCEPTION_CATEGORY_MAP.items():
            if isinstance(exception, exc_type):
                return category
        
        # Default to processing error
        return ErrorCategory.PROCESSING
    
    def _assess_severity(self, exception: Exception, category: ErrorCategory) -> ErrorSeverity:
        """Assess the severity of an error based on type and category."""
        if isinstance(exception, (KeyboardInterrupt, SystemExit)):
            return ErrorSeverity.CRITICAL
        elif isinstance(exception, (APITimeoutError, ConnectionError)):
            return ErrorSeverity.HIGH
        elif isinstance(exception, (ValidationError, ConfigurationError)):
            return ErrorSeverity.MEDIUM
        elif category == ErrorCategory.SECURITY:
            return ErrorSeverity.CRITICAL
        else:
            return ErrorSeverity.MEDIUM
    
    def _get_safe_stack_trace(self, limit: int = 10) -> List[str]:
        """Get a sanitized stack trace for error analysis."""
        try:
            stack_lines = traceback.format_tb(None, limit)
            # Sanitize file paths and sensitive information
            sanitized_lines = []
            for line in stack_lines:
                # Remove full file paths, keep just filename
                import os
                if 'File "' in line:
                    parts = line.split('File "')
                    if len(parts) > 1:
                        file_part = parts[1].split('"')[0]
                        filename = os.path.basename(file_part)
                        line = line.replace(file_part, filename)
                sanitized_lines.append(line.strip())
            return sanitized_lines
        except Exception:
            return ["Stack trace unavailable"]
    
    def _generate_troubleshooting_info(self, exception: Exception, 
                                     category: ErrorCategory) -> Dict[str, List[str]]:
        """Generate troubleshooting information based on error type."""
        # Check if exception has built-in troubleshooting info
        if hasattr(exception, 'get_troubleshooting_info'):
            return exception.get_troubleshooting_info()
        
        # Generate category-based troubleshooting
        troubleshooting = {
            'common_causes': [],
            'suggested_solutions': []
        }
        
        if category == ErrorCategory.VALIDATION:
            troubleshooting['common_causes'] = [
                'Invalid input parameter format',
                'Missing required fields',
                'Data type mismatch',
                'Out of range values'
            ]
            troubleshooting['suggested_solutions'] = [
                'Verify input parameter format and types',
                'Check for required fields in request',
                'Validate data ranges and constraints',
                'Review API documentation for correct usage'
            ]
        elif category == ErrorCategory.API:
            troubleshooting['common_causes'] = [
                'Network connectivity issues',
                'LLM provider service outage',
                'API rate limiting',
                'Authentication failures'
            ]
            troubleshooting['suggested_solutions'] = [
                'Check network connectivity',
                'Verify API credentials and permissions',
                'Implement exponential backoff retry',
                'Consider alternative LLM provider'
            ]
        elif category == ErrorCategory.CONFIGURATION:
            troubleshooting['common_causes'] = [
                'Missing configuration files',
                'Invalid configuration format',
                'Permission issues accessing config',
                'Environment variable not set'
            ]
            troubleshooting['suggested_solutions'] = [
                'Verify configuration files exist',
                'Validate configuration file syntax',
                'Check file permissions',
                'Set required environment variables'
            ]
        
        return troubleshooting
    
    def _log_error(self, error_record: Dict[str, Any], severity: ErrorSeverity) -> None:
        """Log error with appropriate level based on severity."""
        if not self.logger:
            return
        
        message = f"[{error_record['error_id']}] {error_record['exception_type']}: {error_record['exception_message']}"
        
        if severity == ErrorSeverity.CRITICAL:
            self.logger.error(f"CRITICAL ERROR - {message}")
        elif severity == ErrorSeverity.HIGH:
            self.logger.error(f"HIGH SEVERITY - {message}")
        elif severity == ErrorSeverity.MEDIUM:
            self.logger.warning(f"MEDIUM SEVERITY - {message}")
        else:
            self.logger.info(f"LOW SEVERITY - {message}")
    
    def _audit_error(self, error_record: Dict[str, Any]) -> None:
        """Send error to audit system if available."""
        if not self.audit_system or not hasattr(self.audit_system, 'log_agent_activity'):
            return
        
        try:
            self.audit_system.log_agent_activity(
                activity_type="error_occurrence",
                activity_data={
                    'error_id': error_record['error_id'],
                    'exception_type': error_record['exception_type'],
                    'category': error_record['category'],
                    'severity': error_record['severity'],
                    'agent_name': error_record['context']['agent_name'],
                    'operation': error_record['context']['operation'],
                    'recovery_strategy': error_record['recovery_strategy']
                },
                audit_level=2  # Standard audit level for errors
            )
        except Exception as audit_error:
            # Don't let audit failures break error handling
            if self.logger:
                self.logger.warning(f"Failed to audit error: {audit_error}")
    
    def _add_to_history(self, error_record: Dict[str, Any]) -> None:
        """Add error to history for pattern analysis."""
        self.error_history.append(error_record)
        if len(self.error_history) > self.max_history:
            self.error_history = self.error_history[-self.max_history:]
    
    def get_error_patterns(self, time_window_minutes: int = 60) -> Dict[str, Any]:
        """Analyze recent error patterns for monitoring and alerting."""
        cutoff_time = datetime.now(timezone.utc).timestamp() - (time_window_minutes * 60)
        recent_errors = [
            err for err in self.error_history 
            if datetime.fromisoformat(err['timestamp']).timestamp() > cutoff_time
        ]
        
        if not recent_errors:
            return {'total_errors': 0, 'patterns': {}}
        
        # Analyze patterns
        patterns = {
            'by_category': {},
            'by_severity': {},
            'by_agent': {},
            'by_exception_type': {},
            'frequent_operations': {}
        }
        
        for error in recent_errors:
            # Count by category
            category = error['category']
            patterns['by_category'][category] = patterns['by_category'].get(category, 0) + 1
            
            # Count by severity
            severity = error['severity']
            patterns['by_severity'][severity] = patterns['by_severity'].get(severity, 0) + 1
            
            # Count by agent
            agent = error['context']['agent_name']
            patterns['by_agent'][agent] = patterns['by_agent'].get(agent, 0) + 1
            
            # Count by exception type
            exc_type = error['exception_type']
            patterns['by_exception_type'][exc_type] = patterns['by_exception_type'].get(exc_type, 0) + 1
            
            # Count by operation
            operation = error['context']['operation']
            patterns['frequent_operations'][operation] = patterns['frequent_operations'].get(operation, 0) + 1
        
        return {
            'total_errors': len(recent_errors),
            'time_window_minutes': time_window_minutes,
            'patterns': patterns,
            'analysis_timestamp': datetime.now(timezone.utc).isoformat()
        }


@contextmanager
def standardized_error_handling(operation: str, 
                              agent_name: str,
                              logger: Any = None,
                              audit_system: Any = None,
                              request_id: str = None,
                              user_context: Dict[str, Any] = None):
    """
    Context manager for standardized error handling across agent operations.
    
    Usage:
        with standardized_error_handling("rule_extraction", "BusinessRuleAgent", logger, audit) as eh:
            # Operation that might raise exceptions
            result = risky_operation()
            return result
    """
    context = StandardErrorContext(
        operation=operation,
        agent_name=agent_name,
        request_id=request_id,
        user_context=user_context
    )
    
    error_handler = StandardErrorHandler(logger, audit_system)
    
    try:
        yield error_handler
    except Exception as e:
        error_record = error_handler.handle_error(e, context)
        
        # Re-raise with enhanced context
        if hasattr(e, 'error_id'):
            e.error_id = error_record['error_id']
        raise e


# Export commonly used items
__all__ = [
    'ErrorSeverity',
    'ErrorCategory', 
    'ErrorRecoveryStrategy',
    'StandardErrorContext',
    'StandardErrorHandler',
    'standardized_error_handling'
]