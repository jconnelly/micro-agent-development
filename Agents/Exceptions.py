#!/usr/bin/env python3

"""
Custom Exception Classes for Agent System

Provides a hierarchical exception system for better error handling and debugging
across all agents. Each exception type includes structured error information
and integrates with the audit logging system.

Author: AI Development Team  
Version: 1.0.0
"""

from typing import Dict, Any, Optional


class AgentException(Exception):
    """
    Base exception class for all agent-related errors.
    
    Provides structured error information and integrates with audit logging.
    All agent exceptions should inherit from this base class.
    
    Attributes:
        message: Human-readable error description
        error_code: Unique error code for programmatic handling
        context: Additional context information about the error
        request_id: Associated request ID for audit trail correlation
    """
    
    def __init__(
        self, 
        message: str,
        error_code: str = "AGENT_ERROR",
        context: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None
    ):
        self.message = message
        self.error_code = error_code
        self.context = context or {}
        self.request_id = request_id
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for JSON serialization."""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "error_code": self.error_code,
            "context": self.context,
            "request_id": self.request_id
        }
    
    def __str__(self) -> str:
        """String representation including error code and request ID."""
        parts = [self.message]
        if self.error_code:
            parts.append(f"[{self.error_code}]")
        if self.request_id:
            parts.append(f"(Request: {self.request_id})")
        return " ".join(parts)


class ConfigurationError(AgentException):
    """
    Exception raised for configuration-related errors.
    
    Used when configuration files are missing, invalid, or contain
    incompatible settings that prevent agent initialization or operation.
    """
    
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None, request_id: Optional[str] = None):
        super().__init__(message, "CONFIG_ERROR", context, request_id)


class PIIProcessingError(AgentException):
    """
    Exception raised during PII detection, scrubbing, or tokenization operations.
    
    Used for errors in pattern compilation, text processing, masking strategy
    application, or tokenization/detokenization operations.
    """
    
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None, request_id: Optional[str] = None):
        super().__init__(message, "PII_PROCESSING_ERROR", context, request_id)


class RuleExtractionError(AgentException):
    """
    Exception raised during rule extraction and translation operations.
    
    Used for errors in legacy code parsing, LLM processing, rule formatting,
    or output generation during the rule extraction process.
    """
    
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None, request_id: Optional[str] = None):
        super().__init__(message, "RULE_EXTRACTION_ERROR", context, request_id)


class TriageProcessingError(AgentException):
    """
    Exception raised during submission triage and decision-making operations.
    
    Used for errors in submission analysis, LLM triage processing, tool call
    execution, or decision generation during the triage process.
    """
    
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None, request_id: Optional[str] = None):
        super().__init__(message, "TRIAGE_PROCESSING_ERROR", context, request_id)


class DocumentationError(AgentException):
    """
    Exception raised during rule documentation and visualization operations.
    
    Used for errors in documentation generation, format conversion, file I/O
    operations, or template processing during documentation creation.
    """
    
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None, request_id: Optional[str] = None):
        super().__init__(message, "DOCUMENTATION_ERROR", context, request_id)


class AuditingError(AgentException):
    """
    Exception raised during audit logging and compliance operations.
    
    Used for errors in audit log creation, storage, retrieval, or compliance
    validation that don't prevent main operation but affect audit trail.
    """
    
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None, request_id: Optional[str] = None):
        super().__init__(message, "AUDITING_ERROR", context, request_id)


class APITimeoutError(AgentException):
    """
    Exception raised when API calls exceed timeout limits.
    
    Used for LLM service timeouts, network timeouts, or other time-based
    failures that can be retried with appropriate backoff strategies.
    """
    
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None, request_id: Optional[str] = None):
        super().__init__(message, "API_TIMEOUT_ERROR", context, request_id)


class ValidationError(AgentException):
    """
    Exception raised for input validation errors.
    
    Used when user input, configuration values, or data formats don't meet
    required specifications or constraints for proper agent operation.
    """
    
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None, request_id: Optional[str] = None):
        super().__init__(message, "VALIDATION_ERROR", context, request_id)


class ToolIntegrationError(AgentException):
    """
    Exception raised during tool integration operations.
    
    Used for errors in Write/Read/Grep tool operations, file I/O failures,
    or tool unavailability that affects enhanced agent functionality.
    """
    
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None, request_id: Optional[str] = None):
        super().__init__(message, "TOOL_INTEGRATION_ERROR", context, request_id)


# Convenience functions for common error scenarios
def create_config_error(config_type: str, details: str, request_id: Optional[str] = None) -> ConfigurationError:
    """Create a standardized configuration error."""
    return ConfigurationError(
        f"Configuration error in {config_type}: {details}",
        context={"config_type": config_type, "details": details},
        request_id=request_id
    )


def create_validation_error(field: str, value: Any, expected: str, request_id: Optional[str] = None) -> ValidationError:
    """Create a standardized validation error."""
    return ValidationError(
        f"Invalid {field}: expected {expected}, got {type(value).__name__}",
        context={"field": field, "value": str(value), "expected": expected},
        request_id=request_id
    )


def create_processing_error(operation: str, details: str, agent_type: str, request_id: Optional[str] = None) -> AgentException:
    """Create a standardized processing error based on agent type."""
    context = {"operation": operation, "details": details, "agent_type": agent_type}
    
    if agent_type.lower() in ["pii", "scrubbing"]:
        return PIIProcessingError(f"PII {operation} failed: {details}", context, request_id)
    elif agent_type.lower() in ["rule", "extraction"]:
        return RuleExtractionError(f"Rule {operation} failed: {details}", context, request_id)
    elif agent_type.lower() in ["triage", "submission"]:
        return TriageProcessingError(f"Triage {operation} failed: {details}", context, request_id)
    elif agent_type.lower() in ["documentation", "doc"]:
        return DocumentationError(f"Documentation {operation} failed: {details}", context, request_id)
    else:
        return AgentException(f"{operation} failed: {details}", "PROCESSING_ERROR", context, request_id)