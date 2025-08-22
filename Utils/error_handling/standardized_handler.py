#!/usr/bin/env python3

"""
Standardized Error Handler

Provides unified error handling patterns across all agents with consistent
exception handling, logging, recovery, and audit trail integration.
"""

import traceback
from typing import Any, Dict, Optional, Callable, Union, Type
from datetime import datetime
from functools import wraps

# Import both exception hierarchies for unified handling
from Agents.Exceptions import (
    AgentException, ConfigurationError, PIIProcessingError, 
    RuleExtractionError, TriageProcessingError, DocumentationError,
    AuditingError, APITimeoutError, ValidationError, ToolIntegrationError
)
from Utils.shared_components.exceptions import (
    StandardizedException, PerformanceException, 
    ConfigurationException, ToolIntegrationException as UtilsToolError
)


class StandardizedErrorHandler:
    """
    Unified error handling system providing consistent patterns across all agents.
    """

    # Exception type mapping for automatic conversion
    EXCEPTION_MAPPING = {
        'config': ConfigurationError,
        'configuration': ConfigurationError,
        'pii': PIIProcessingError,
        'scrubbing': PIIProcessingError,
        'rule': RuleExtractionError,
        'extraction': RuleExtractionError,
        'triage': TriageProcessingError,
        'submission': TriageProcessingError,
        'documentation': DocumentationError,
        'doc': DocumentationError,
        'audit': AuditingError,
        'auditing': AuditingError,
        'api': APITimeoutError,
        'timeout': APITimeoutError,
        'validation': ValidationError,
        'tool': ToolIntegrationError,
        'performance': PerformanceException
    }

    @staticmethod
    def handle_agent_error(
        operation: str,
        agent_type: str,
        original_error: Exception,
        context: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None,
        logger: Optional[Any] = None,
        retry_count: int = 0,
        max_retries: int = 0
    ) -> AgentException:
        """
        Standardized error handling for agent operations.
        
        Args:
            operation: Description of the operation that failed
            agent_type: Type of agent (pii, rule, triage, etc.)
            original_error: The original exception that occurred
            context: Additional context information
            request_id: Request ID for audit correlation
            logger: Logger instance for error recording
            retry_count: Current retry attempt
            max_retries: Maximum retry attempts allowed
            
        Returns:
            Appropriate AgentException subclass
        """
        # Determine appropriate exception type
        exception_class = StandardizedErrorHandler._get_exception_class(agent_type)
        
        # Create comprehensive context
        error_context = {
            'operation': operation,
            'agent_type': agent_type,
            'original_error_type': type(original_error).__name__,
            'retry_count': retry_count,
            'max_retries': max_retries,
            'traceback_summary': traceback.format_exc().split('\n')[-3:-1]  # Last 2 lines
        }
        
        if context:
            error_context.update(context)
        
        # Create error message
        if retry_count > 0:
            message = f"{operation} failed (attempt {retry_count + 1}/{max_retries + 1}): {str(original_error)}"
        else:
            message = f"{operation} failed: {str(original_error)}"
        
        # Create standardized exception
        standardized_exception = exception_class(
            message=message,
            context=error_context,
            request_id=request_id
        )
        
        # Log the error if logger provided
        if logger:
            StandardizedErrorHandler._log_error(
                logger, standardized_exception, operation, agent_type, retry_count
            )
        
        return standardized_exception

    @staticmethod
    def safe_operation_wrapper(
        operation_name: str,
        agent_type: str,
        request_id: Optional[str] = None,
        logger: Optional[Any] = None,
        max_retries: int = 0,
        retry_delay: float = 1.0,
        allowed_exceptions: Optional[tuple] = None
    ) -> Callable:
        """
        Decorator for wrapping agent operations with standardized error handling.
        
        Args:
            operation_name: Human-readable operation name
            agent_type: Type of agent operation
            request_id: Request ID for audit correlation
            logger: Logger instance
            max_retries: Number of retry attempts
            retry_delay: Delay between retries in seconds
            allowed_exceptions: Tuple of exception types to let through without wrapping
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs) -> Any:
                last_exception = None
                
                for attempt in range(max_retries + 1):
                    try:
                        result = func(*args, **kwargs)
                        
                        # Log successful retry if this wasn't the first attempt
                        if attempt > 0 and logger:
                            logger.info(
                                f"{operation_name} succeeded on retry attempt {attempt + 1}",
                                extra={'request_id': request_id, 'operation': operation_name}
                            )
                        
                        return result
                        
                    except Exception as e:
                        last_exception = e
                        
                        # Check if this exception should pass through unchanged
                        if allowed_exceptions and isinstance(e, allowed_exceptions):
                            raise e
                        
                        # If this is already an AgentException, don't double-wrap
                        if isinstance(e, AgentException):
                            if attempt >= max_retries:
                                raise e
                            continue
                        
                        # If we've exhausted retries, create standardized exception
                        if attempt >= max_retries:
                            break
                            
                        # Log retry attempt
                        if logger:
                            logger.warning(
                                f"{operation_name} failed, attempt {attempt + 1}/{max_retries + 1}, retrying in {retry_delay}s",
                                extra={'request_id': request_id, 'error': str(e)}
                            )
                        
                        # Wait before retry
                        import time
                        time.sleep(retry_delay)
                
                # Create and raise standardized exception
                raise StandardizedErrorHandler.handle_agent_error(
                    operation=operation_name,
                    agent_type=agent_type,
                    original_error=last_exception,
                    request_id=request_id,
                    logger=logger,
                    retry_count=max_retries,
                    max_retries=max_retries
                )
            
            return wrapper
        return decorator

    @staticmethod
    def validate_input(
        field_name: str,
        value: Any,
        expected_type: Type,
        request_id: Optional[str] = None,
        additional_validators: Optional[list] = None
    ) -> None:
        """
        Standardized input validation with consistent error messages.
        
        Args:
            field_name: Name of the field being validated
            value: Value to validate
            expected_type: Expected type for the value
            request_id: Request ID for audit correlation
            additional_validators: List of (validator_func, error_message) tuples
            
        Raises:
            ValidationError: If validation fails
        """
        # Type validation
        if not isinstance(value, expected_type):
            raise ValidationError(
                f"Invalid {field_name}: expected {expected_type.__name__}, got {type(value).__name__}",
                context={
                    'field': field_name,
                    'expected_type': expected_type.__name__,
                    'actual_type': type(value).__name__,
                    'value_preview': str(value)[:100]  # First 100 chars
                },
                request_id=request_id
            )
        
        # Additional custom validators
        if additional_validators:
            for validator_func, error_message in additional_validators:
                if not validator_func(value):
                    raise ValidationError(
                        f"Invalid {field_name}: {error_message}",
                        context={
                            'field': field_name,
                            'validation_error': error_message,
                            'value_preview': str(value)[:100]
                        },
                        request_id=request_id
                    )

    @staticmethod
    def _get_exception_class(agent_type: str) -> Type[AgentException]:
        """Get appropriate exception class for agent type."""
        agent_type_lower = agent_type.lower()
        return StandardizedErrorHandler.EXCEPTION_MAPPING.get(agent_type_lower, AgentException)

    @staticmethod
    def _log_error(
        logger: Any,
        exception: AgentException,
        operation: str,
        agent_type: str,
        retry_count: int
    ) -> None:
        """Log error with standardized format."""
        log_level = 'error' if retry_count == 0 else 'warning'
        log_message = f"{agent_type.upper()} {operation} failed: {exception.message}"
        
        # Prepare structured logging data
        log_extra = {
            'error_code': exception.error_code,
            'request_id': exception.request_id,
            'agent_type': agent_type,
            'operation': operation,
            'error_context': exception.context
        }
        
        # Log with appropriate level
        if hasattr(logger, log_level):
            getattr(logger, log_level)(log_message, extra=log_extra)
        else:
            # Fallback for simple loggers
            print(f"{log_level.upper()}: {log_message}")


# Convenience functions for common error scenarios
def handle_config_error(message: str, config_name: str = None, request_id: str = None) -> ConfigurationError:
    """Create standardized configuration error."""
    context = {'config_name': config_name} if config_name else {}
    return ConfigurationError(message, context=context, request_id=request_id)


def handle_validation_error(field: str, value: Any, expected: str, request_id: str = None) -> ValidationError:
    """Create standardized validation error."""
    return ValidationError(
        f"Invalid {field}: expected {expected}, got {type(value).__name__}",
        context={'field': field, 'expected': expected, 'actual_type': type(value).__name__},
        request_id=request_id
    )


def handle_processing_error(operation: str, agent_type: str, details: str, request_id: str = None) -> AgentException:
    """Create standardized processing error."""
    exception_class = StandardizedErrorHandler._get_exception_class(agent_type)
    return exception_class(
        f"{operation} failed: {details}",
        context={'operation': operation, 'agent_type': agent_type, 'details': details},
        request_id=request_id
    )


# Export key components for easy importing
__all__ = [
    'StandardizedErrorHandler',
    'handle_config_error', 
    'handle_validation_error',
    'handle_processing_error'
]