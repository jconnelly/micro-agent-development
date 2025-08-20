"""
BaseAgent - Abstract base class for all AI agents.

This class provides common functionality that is shared across all agent implementations,
eliminating code duplication and ensuring consistency in behavior, logging, and error handling.
"""

import socket
import asyncio
import time
import uuid
from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import Any, Dict, Optional, Callable, Union, List, Protocol
from datetime import datetime, timezone
from pathlib import Path

from .Logger import AgentLogger
from .Exceptions import ConfigurationError, APITimeoutError


class AuditSystemInterface(Protocol):
    """
    Protocol interface for audit systems used by BaseAgent.
    
    This protocol defines the minimal interface required by BaseAgent for audit
    logging, eliminating circular import dependencies while maintaining type safety.
    
    Any audit system that implements these methods can be used with BaseAgent.
    """
    
    def log_agent_activity(self, **kwargs) -> Dict[str, Any]:
        """Log agent activity with flexible keyword arguments."""
        ...


# Import Utils and config loader - handle both relative and absolute imports
try:
    from ..Utils import RequestIdGenerator, TimeUtils
    from ..Utils.config_loader import get_config_loader
    from ..Utils.llm_providers import LLMProvider, get_default_llm_provider
    from ..Utils.resource_managers import (
        managed_llm_client, managed_audit_session, get_resource_tracker,
        safe_llm_operation, safe_audit_operation
    )
    from ..Utils.audit_framework import (
        StandardAuditTrail, AuditOperationType, AuditOutcome, AuditSeverity, audited_operation
    )
except ImportError:
    import sys
    import os
    # Add parent directory to path for Utils
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    from Utils import RequestIdGenerator, TimeUtils
    from Utils.config_loader import get_config_loader
    from Utils.llm_providers import LLMProvider, get_default_llm_provider
    from Utils.resource_managers import (
        managed_llm_client, managed_audit_session, get_resource_tracker,
        safe_llm_operation, safe_audit_operation
    )
    from Utils.audit_framework import (
        StandardAuditTrail, AuditOperationType, AuditOutcome, AuditSeverity, audited_operation
    )


class BaseAgent(ABC):
    """
    Abstract base class for all AI agents providing common functionality.
    
    This class consolidates shared behavior across all agents including:
    - Standardized initialization patterns
    - IP address resolution with fallback
    - Exception logging to audit trail
    - Retry logic for API calls
    - Common utility methods
    
    All agent implementations should inherit from this class.
    """
    
    def __init__(
        self, 
        audit_system: AuditSystemInterface, 
        agent_id: str = None,
        log_level: int = 0,
        model_name: str = None,
        llm_provider: Union[LLMProvider, str] = None,
        agent_name: str = "BaseAgent"
    ):
        """
        Initialize base agent with common configuration.
        
        Args:
            audit_system: The auditing system instance implementing AuditSystemInterface
            agent_id: Unique identifier for this agent instance
            log_level: 0 for production (silent), 1 for development (verbose)
            model_name: Name of the LLM model being used (optional, inferred from provider)
            llm_provider: LLM provider instance or provider type string (defaults to Gemini)
            agent_name: Human-readable name for this agent
        """
        # Core agent identification
        if agent_id is None:
            clean_name = agent_name.replace(' ', '').lower()
            self.agent_id = RequestIdGenerator.create_request_id(clean_name, 8)
        else:
            self.agent_id = agent_id
        self.agent_name = agent_name
        self.version = "1.0.0"
        
        # LLM configuration - handle both provider instances and legacy strings
        if isinstance(llm_provider, str):
            # Legacy string provider name (for backward compatibility)
            self.llm_provider_name = llm_provider
            self.llm_provider = None  # Will use legacy approach
            self.model_name = model_name or "unknown"
        elif llm_provider is None:
            # Default to Gemini provider
            try:
                self.llm_provider = get_default_llm_provider()
                self.llm_provider_name = self.llm_provider.get_provider_type().value
                self.model_name = model_name or self.llm_provider.get_model_name()
            except Exception:
                # Fallback to legacy if LLM provider fails to initialize
                self.llm_provider = None
                self.llm_provider_name = "gemini"
                self.model_name = model_name or "gemini-1.5-flash"
        else:
            # Custom LLM provider instance
            self.llm_provider = llm_provider
            self.llm_provider_name = llm_provider.get_provider_type().value
            self.model_name = model_name or llm_provider.get_model_name()
        
        # System dependencies
        self.audit_system = audit_system
        
        # Initialize logger (ensure log_level is integer)
        self.logger = AgentLogger(
            log_level=int(log_level) if isinstance(log_level, (str, float)) else log_level,
            agent_name=agent_name
        )
        
        # Lazy-load configuration only when needed (50-70% initialization speedup)
        # Configuration will be loaded on first access via agent_config property
        
        # Cache for expensive operations
        self._ip_address_cache = None
        self._agent_config_cache = None
        
        # Standardized audit trail integration
        self.audit_trail = StandardAuditTrail(
            audit_system=audit_system,
            default_audit_level=2,  # Default to LEVEL_2 for business operations
            environment="production" if not hasattr(self, '_debug_mode') else "development",
            version=self.version
        )
        
    def _load_agent_configuration(self) -> Dict[str, Any]:
        """
        Load agent configuration from external files with graceful fallback to defaults.
        
        Loads configuration from agent_defaults.yaml and applies agent-specific overrides.
        Falls back to hardcoded defaults if configuration loading fails.
        """
        # Hardcoded fallback configuration
        fallback_config = {
            'agent_defaults': {
                'api_settings': {
                    'timeout_seconds': 30.0,
                    'max_retries': 3,
                    'total_operation_timeout': 300.0,
                    'retry_backoff_base': 2.0,
                    'retry_backoff_max': 16.0
                },
                'caching': {
                    'default_lru_cache_size': 128,
                    'ip_resolution_cache_ttl': 300
                },
                'processing_limits': {
                    'max_file_chunks': 50,
                    'min_chunk_lines': 10,
                    'chunking_line_threshold': 175
                }
            }
        }
        
        try:
            config_loader = get_config_loader()
            agent_config = config_loader.load_config("agent_defaults", fallback_config)
            
            # Extract API settings
            api_settings = agent_config['agent_defaults']['api_settings']
            self.API_TIMEOUT_SECONDS = float(api_settings.get('timeout_seconds', 30.0))
            self.MAX_RETRIES = int(api_settings.get('max_retries', 3))
            self.TOTAL_OPERATION_TIMEOUT = float(api_settings.get('total_operation_timeout', 300.0))
            self.API_DELAY_SECONDS = 1.0  # Keep default for now
            
            # Store config for subclasses
            self._agent_config = agent_config
            
            self.logger.debug(f"Loaded agent configuration from external file")
            
        except Exception as e:
            self.logger.warning(f"Failed to load agent configuration: {e}. Using fallback.")
            # Use hardcoded fallback values
            self.API_TIMEOUT_SECONDS = 30.0
            self.MAX_RETRIES = 3
            self.TOTAL_OPERATION_TIMEOUT = 300.0
            self.API_DELAY_SECONDS = 1.0
            self._agent_config = fallback_config
    
    @property
    def agent_config(self) -> Dict[str, Any]:
        """Lazy-load agent configuration on first access."""
        if not hasattr(self, '_agent_config') or self._agent_config is None:
            self._load_agent_configuration()
        return self._agent_config
    
    def get_agent_config(self, path: str = None) -> Dict[str, Any]:
        """
        Get agent configuration value by path.
        
        Args:
            path: Dot-separated path to config value (e.g., 'api_settings.timeout_seconds')
                 If None, returns the entire config
                 
        Returns:
            Configuration value or entire config dict
        """
        if path is None:
            return self.agent_config
            
        config = self.agent_config
        for key in path.split('.'):
            if isinstance(config, dict) and key in config:
                config = config[key]
            else:
                return None
        return config
        
    def get_ip_address(self) -> str:
        """
        Get the current machine's IP address with caching and fallback.
        
        Returns:
            String IP address, or "127.0.0.1" as fallback
        """
        # Return cached value if available
        if self._ip_address_cache is not None:
            return self._ip_address_cache
            
        try:
            hostname = socket.gethostname()
            ip_address = socket.gethostbyname(hostname)
            self._ip_address_cache = ip_address
            return ip_address
        except (socket.gaierror, Exception) as e:
            self.logger.warning(f"Could not resolve hostname to IP address: {str(e)}")
            self._ip_address_cache = "127.0.0.1"
            return "127.0.0.1"
    
    def _get_ip_address(self) -> str:
        """
        Private method for backward compatibility.
        Delegates to the public get_ip_address() method.
        """
        return self.get_ip_address()
    
    def _log_exception_to_audit(
        self, 
        request_id: str, 
        exception: Exception, 
        error_type: str, 
        context: Dict[str, Any],
        operation_name: str = "agent_operation"
    ) -> None:
        """
        Log exception details to the audit system with processing context.
        
        Args:
            request_id: The request ID for tracking
            exception: The exception that occurred
            error_type: Type of error for categorization
            context: Additional context about the processing state
            operation_name: Name of the operation that failed
        """
        try:
            # Create audit summary with logger session data
            audit_summary = self.logger.create_audit_summary(
                operation_name=f"{operation_name}_exception",
                request_id=request_id,
                status="FAILED",
                error_type=error_type,
                exception_message=str(exception),
                exception_type=type(exception).__name__,
                processing_context=context
            )
            
            # Log to audit system if available
            if self.audit_system:
                self.audit_system.log_agent_activity(
                    request_id=request_id,
                    user_id="system",
                    session_id=request_id,
                    ip_address=self.get_ip_address(),
                    agent_id=self.agent_id,
                    agent_name=self.agent_name,
                    agent_version=self.version,
                    step_type="EXCEPTION_HANDLING",
                    llm_model_name=self.model_name,
                    llm_provider=self.llm_provider,
                    llm_input={"error_type": error_type},
                    llm_output=audit_summary,
                    tokens_input=0,
                    tokens_output=0,
                    duration_ms=0,
                    success=False,
                    error_details=str(exception),
                    audit_level=1  # Always log exceptions
                )
        except Exception as audit_error:
            # If audit logging fails, fall back to regular logging (using standardized error handling)
            try:
                from Utils.error_handling import StandardErrorHandler, StandardErrorContext
                context = StandardErrorContext(
                    operation="audit_logging_failure",
                    agent_name=self.__class__.__name__,
                    system_context={"original_exception": str(exception)}
                )
                error_handler = StandardErrorHandler(self.logger, None)  # No audit for audit errors
                error_handler.handle_error(audit_error, context)
            except Exception:
                # Final fallback if standardized error handling fails
                self.logger.error(f"Failed to log exception to audit: {str(audit_error)}")
                self.logger.error(f"Original exception: {str(exception)}")
    
    async def _api_call_with_retry_async(
        self, 
        api_call_func: Callable[..., Any],
        *args: Any,
        max_retries: Optional[int] = None,
        timeout_seconds: Optional[float] = None,
        **kwargs: Any
    ) -> Any:
        """
        Async API call with retry logic and timeout handling.
        
        Args:
            api_call_func: The API function to call
            *args: Arguments to pass to the API function
            max_retries: Maximum number of retry attempts (defaults to self.MAX_RETRIES)
            timeout_seconds: Timeout in seconds (defaults to self.API_TIMEOUT_SECONDS)
            **kwargs: Keyword arguments to pass to the API function
            
        Returns:
            API response
            
        Raises:
            TimeoutError: If all retries fail due to timeouts
            Exception: If all retries fail due to other errors
        """
        # Ensure configuration is loaded
        if not hasattr(self, 'MAX_RETRIES'):
            _ = self.agent_config  # Trigger lazy loading
            
        max_retries = max_retries or self.MAX_RETRIES
        timeout_seconds = timeout_seconds or self.API_TIMEOUT_SECONDS
        
        for attempt in range(max_retries):
            try:
                # Use asyncio.wait_for for timeout handling
                response = await asyncio.wait_for(
                    api_call_func(*args, **kwargs),
                    timeout=timeout_seconds
                )
                return response
                
            except asyncio.TimeoutError:
                self.logger.warning(f"API call timed out after {timeout_seconds} seconds")
                if attempt == max_retries - 1:
                    raise APITimeoutError(
                        f"API call failed after {max_retries} attempts due to timeouts",
                        context={"max_retries": max_retries, "timeout_seconds": timeout_seconds}
                    )
                    
            except Exception as e:
                self.logger.warning(f"API call failed (attempt {attempt + 1}/{max_retries}): {str(e)}")
                if attempt == max_retries - 1:
                    raise e
                
            # Exponential backoff: wait 2^attempt seconds
            wait_time = 2 ** attempt
            self.logger.warning(f"Retrying in {wait_time}s...")
            await asyncio.sleep(wait_time)
    
    def _api_call_with_retry(
        self, 
        api_call_func: Callable[..., Any],
        *args: Any,
        max_retries: Optional[int] = None,
        timeout_seconds: Optional[float] = None,
        **kwargs: Any
    ) -> Any:
        """
        Synchronous wrapper for async API retry logic.
        
        Args:
            api_call_func: The API function to call
            *args: Arguments to pass to the API function
            max_retries: Maximum number of retry attempts
            timeout_seconds: Timeout in seconds
            **kwargs: Keyword arguments to pass to the API function
            
        Returns:
            API response
        """
        async def async_wrapper() -> Any:
            return await self._api_call_with_retry_async(
                api_call_func, *args, 
                max_retries=max_retries,
                timeout_seconds=timeout_seconds,
                **kwargs
            )
        
        return asyncio.run(async_wrapper())
    
    def _create_request_id(self, prefix: str = "req") -> str:
        """
        Create a unique request ID for tracking operations.
        
        Args:
            prefix: Prefix for the request ID
            
        Returns:
            Unique request ID string
        """
        return RequestIdGenerator.create_request_id(prefix)
    
    def _get_current_timestamp(self) -> datetime:
        """
        Get current UTC timestamp.
        
        Returns:
            Current UTC datetime
        """
        return TimeUtils.get_current_utc_timestamp()
    
    def _calculate_duration_ms(self, start_time: datetime, end_time: Optional[datetime] = None) -> float:
        """
        Calculate duration in milliseconds between two timestamps.
        
        Args:
            start_time: Start timestamp
            end_time: End timestamp (defaults to current time)
            
        Returns:
            Duration in milliseconds
        """
        return TimeUtils.calculate_duration_ms(start_time, end_time)
    
    def _call_llm(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        Make an LLM call using the configured provider with fallback support.
        
        This method abstracts LLM calls to work with both new LLM providers
        and legacy agent implementations, providing seamless backward compatibility.
        
        Args:
            prompt: Text prompt to send to the LLM
            **kwargs: Provider-specific parameters (temperature, max_tokens, etc.)
            
        Returns:
            Dict containing:
            - content: LLM response text
            - model_name: Model that generated the response
            - provider_type: Provider type used
            - usage_stats: Token usage information (if available)
            - response_time_ms: Response time in milliseconds
            - error: Error message if call failed
        """
        if self.llm_provider is not None:
            # Use new LLM provider abstraction
            try:
                response = self.llm_provider.generate_content(prompt, **kwargs)
                
                return {
                    "content": response.content,
                    "model_name": response.model_name,
                    "provider_type": response.provider_type.value,
                    "usage_stats": response.usage_stats,
                    "response_time_ms": response.response_time_ms,
                    "request_id": response.request_id,
                    "error": response.error,
                    "success": response.error is None
                }
                
            except Exception as e:
                return {
                    "content": "",
                    "model_name": self.model_name,
                    "provider_type": self.llm_provider_name,
                    "usage_stats": None,
                    "response_time_ms": None,
                    "request_id": None,
                    "error": f"LLM provider call failed: {str(e)}",
                    "success": False
                }
        else:
            # Legacy mode - return structure indicating legacy handling needed
            return {
                "content": "",
                "model_name": self.model_name,
                "provider_type": self.llm_provider_name,
                "usage_stats": None,
                "response_time_ms": None,
                "request_id": None,
                "error": "Legacy LLM mode - subclass must handle LLM call",
                "success": False,
                "legacy_mode": True
            }
    
    @abstractmethod
    def get_agent_info(self) -> Dict[str, Any]:
        """
        Get agent information including capabilities and configuration.
        
        This method must be implemented by all subclasses to provide
        agent-specific information.
        
        Returns:
            Dictionary containing agent information
        """
        pass
    
    def __str__(self) -> str:
        """String representation of the agent."""
        return f"{self.agent_name} (ID: {self.agent_id})"
    
    def __repr__(self) -> str:
        """Developer representation of the agent."""
        return f"{self.__class__.__name__}(agent_id='{self.agent_id}', model='{self.model_name}')"
    
    # ===== Resource Management Methods (Phase 14 High Priority Task #3) =====
    
    def managed_llm_operation(self, operation_context: str = "agent_operation") -> Any:
        """
        Create a managed LLM operation context for this agent.
        
        Provides automatic resource management for LLM operations with
        proper cleanup and monitoring.
        
        Args:
            operation_context: Description of the operation for tracking
            
        Returns:
            Context manager for LLM operations
            
        Example:
            with self.managed_llm_operation("rule_extraction") as llm:
                response = llm.generate_content(prompt)
        """
        if self.llm_provider:
            return managed_llm_client(self.llm_provider, operation_context)
        else:
            # For legacy compatibility, create a mock context manager
            from contextlib import contextmanager
            
            @contextmanager
            def legacy_llm_context() -> Any:
                yield self  # Return self for legacy _call_llm usage
            
            return legacy_llm_context()
    
    def managed_audit_operation(self, operation_type: str, metadata: Optional[Dict[str, Any]] = None) -> Any:
        """
        Create a managed audit operation context for this agent.
        
        Ensures audit sessions are properly started and ended with
        automatic cleanup on exceptions.
        
        Args:
            operation_type: Type of operation being audited
            metadata: Additional metadata for the audit session
            
        Returns:
            Context manager yielding audit session ID
            
        Example:
            with self.managed_audit_operation("data_processing", {"file": "input.txt"}) as session_id:
                # Perform audited operations
                result = self.process_data()
        """
        return managed_audit_session(self.audit_system, operation_type, metadata)
    
    def get_resource_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive resource usage summary for this agent.
        
        Provides insights into current resource usage, potential leaks,
        and performance metrics for monitoring and debugging.
        
        Returns:
            Dictionary containing resource usage summary
        """
        tracker = get_resource_tracker()
        summary = tracker.get_resource_summary()
        
        # Add agent-specific context
        summary['agent_info'] = {
            'agent_id': self.agent_id,
            'agent_name': self.agent_name,
            'model_name': self.model_name,
            'llm_provider': self.llm_provider_name if hasattr(self, 'llm_provider_name') else 'unknown'
        }
        
        # Add audit trail status
        if hasattr(self, 'audit_trail') and self.audit_trail:
            summary['audit_trail'] = self.audit_trail.get_operation_summary()
        
        return summary
    
    def check_resource_leaks(self) -> List[str]:
        """
        Check for potential resource leaks in this agent's operations.
        
        Scans for resources that have been active longer than expected
        and may indicate resource leaks or improper cleanup.
        
        Returns:
            List of potential resource leak descriptions
        """
        tracker = get_resource_tracker()
        return tracker.check_for_leaks()
    
    def cleanup_agent_resources(self) -> Dict[str, Any]:
        """
        Perform cleanup of any leaked resources associated with this agent.
        
        Should be called during agent shutdown or periodically in
        long-running applications to prevent resource accumulation.
        
        Returns:
            Summary of cleanup actions taken
        """
        from Utils.resource_managers import cleanup_leaked_resources
        
        cleanup_summary = cleanup_leaked_resources()
        
        # Log cleanup results
        if cleanup_summary['leaks_detected'] > 0:
            self.logger.warning(f"Cleaned up {cleanup_summary['leaks_detected']} leaked resources")
        else:
            self.logger.debug("No resource leaks detected during cleanup")
        
        return cleanup_summary
    
    def handle_error_standardized(self, 
                                 exception: Exception,
                                 operation: str,
                                 request_id: str = None,
                                 user_context: Dict[str, Any] = None,
                                 system_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Handle an error using standardized error handling patterns.
        
        This method provides a convenient way for agents to use standardized
        error handling without importing and setting up the error handling components.
        
        Args:
            exception: The exception that occurred
            operation: Name of the operation that failed  
            request_id: Optional request ID for tracking
            user_context: User-provided context (sanitized for security)
            system_context: System context (performance metrics, resource usage)
            
        Returns:
            Dictionary with error analysis and recovery recommendations
        """
        try:
            from Utils.error_handling import StandardErrorHandler, StandardErrorContext
            context = StandardErrorContext(
                operation=operation,
                agent_name=self.__class__.__name__,
                request_id=request_id,
                user_context=user_context or {},
                system_context=system_context or {}
            )
            error_handler = StandardErrorHandler(self.logger, self.audit_system)
            return error_handler.handle_error(exception, context)
        except Exception as handling_error:
            # Fallback if standardized error handling fails
            self.logger.error(f"Standardized error handling failed: {handling_error}")
            self.logger.error(f"Original exception: {exception}")
            return {
                'error_id': f"fallback_{uuid.uuid4().hex[:8]}",
                'exception_type': type(exception).__name__,
                'exception_message': str(exception),
                'fallback_used': True
            }
    
    def validate_input(self,
                      parameters: Dict[str, Any],
                      validation_rules: Dict[str, Dict[str, Any]],
                      operation_context: str = "agent_operation") -> Dict[str, Any]:
        """
        Validate input parameters using standardized validation framework.
        
        This method provides a convenient way for agents to validate inputs
        without directly importing and setting up validation components.
        
        Args:
            parameters: Dictionary of parameter names to values
            validation_rules: Dictionary of parameter names to validation rule dictionaries
            operation_context: Description of the operation for error context
            
        Returns:
            Dictionary of sanitized parameters
            
        Raises:
            InputValidationError: If validation fails
            
        Example:
            rules = {
                'file_path': {'expected_type': str, 'required': True, 'max_length': 260},
                'audit_level': {'expected_type': int, 'min_value': 0, 'max_value': 4}
            }
            sanitized = self.validate_input(parameters, rules)
        """
        try:
            from Utils.input_validation import ParameterValidator, InputValidationError
            
            validator = ParameterValidator()
            all_valid, sanitized_parameters, issues_by_parameter = validator.validate_parameters(
                parameters, validation_rules
            )
            
            if not all_valid:
                # Create detailed error message
                error_details = []
                for param, issues in issues_by_parameter.items():
                    error_details.extend([f"{param}: {issue}" for issue in issues])
                
                raise InputValidationError(
                    f"Input validation failed for {operation_context}: {'; '.join(error_details)}",
                    validation_issues=issues_by_parameter,
                    context={'operation': operation_context, 'agent': self.__class__.__name__}
                )
            
            return sanitized_parameters
            
        except ImportError:
            # Fallback if validation framework not available
            self.logger.warning("Input validation framework not available, using basic validation")
            return parameters
    
    def validate_file_path(self,
                          file_path: Union[str, Path], 
                          allowed_base_dirs: List[Union[str, Path]] = None,
                          allowed_extensions: List[str] = None,
                          operation_context: str = "file_operation") -> Path:
        """
        Validate and sanitize a file path for secure file operations.
        
        Args:
            file_path: File path to validate
            allowed_base_dirs: List of allowed base directories (whitelist)
            allowed_extensions: List of allowed file extensions
            operation_context: Description of the operation for error context
            
        Returns:
            Sanitized Path object
            
        Raises:
            ValidationError: If path validation fails
        """
        try:
            from Utils.input_validation import SecureFilePathValidator
            
            validator = SecureFilePathValidator(
                allowed_base_dirs=allowed_base_dirs,
                allowed_extensions=allowed_extensions
            )
            
            return validator.sanitize_path(file_path)
            
        except ImportError:
            # Fallback if validation framework not available
            self.logger.warning("Path validation framework not available, using basic validation")
            return Path(file_path).resolve()
    
    @contextmanager
    def managed_operation(self, operation_name: str, 
                         audit_metadata: Optional[Dict[str, Any]] = None) -> Any:
        """
        Create a comprehensive managed operation context.
        
        Combines LLM and audit management in a single context manager
        for complete resource management in agent operations.
        
        Args:
            operation_name: Name of the operation
            audit_metadata: Metadata for audit logging
            
        Yields:
            Tuple of (llm_client, audit_session_id)
            
        Example:
            with self.managed_operation("complex_processing") as (llm, session_id):
                response = llm.generate_content(prompt)
                # Audit session automatically tracks the operation
        """
        with self.managed_audit_operation(operation_name, audit_metadata) as session_id:
            with self.managed_llm_operation(operation_name) as llm:
                yield llm, session_id
    
    # ===== Standardized Audit Trail Methods (Phase 14 Medium Priority Task #7) =====
    
    def log_operation_start(self,
                           operation_type: Union[AuditOperationType, str],
                           operation_name: str,
                           user_context: Dict[str, Any] = None,
                           audit_level: int = None) -> str:
        """
        Log the start of an operation using standardized audit trail.
        
        Args:
            operation_type: Type of operation (from AuditOperationType enum)
            operation_name: Specific name of the operation
            user_context: User-related context information
            audit_level: Audit verbosity level
            
        Returns:
            Request ID for tracking the operation
        """
        if hasattr(self, 'audit_trail') and self.audit_trail:
            return self.audit_trail.log_operation_start(
                operation_type=operation_type,
                operation_name=operation_name,
                agent_name=self.agent_name,
                user_context=user_context,
                audit_level=audit_level
            )
        else:
            # Fallback to basic request ID generation
            return self._create_request_id("op")
    
    def log_operation_complete(self,
                              request_id: str,
                              outcome: AuditOutcome = AuditOutcome.SUCCESS,
                              result_summary: str = "",
                              error_details: str = None,
                              business_context: Dict[str, Any] = None,
                              compliance_flags: List[str] = None,
                              security_flags: List[str] = None) -> Optional[Dict[str, Any]]:
        """
        Log the completion of a tracked operation.
        
        Args:
            request_id: Request identifier for the operation
            outcome: Final outcome of the operation
            result_summary: Summary of operation results
            error_details: Error details if operation failed
            business_context: Business-related context information
            compliance_flags: Compliance-related flags or violations
            security_flags: Security-related flags or issues
            
        Returns:
            Complete audit entry if audit trail is available, None otherwise
        """
        if hasattr(self, 'audit_trail') and self.audit_trail:
            return self.audit_trail.log_operation_complete(
                request_id=request_id,
                outcome=outcome,
                result_summary=result_summary,
                error_details=error_details,
                business_context=business_context,
                compliance_flags=compliance_flags,
                security_flags=security_flags
            ).to_dict()
        return None
    
    def log_immediate_event(self,
                           operation_type: Union[AuditOperationType, str],
                           operation_name: str,
                           outcome: AuditOutcome = AuditOutcome.SUCCESS,
                           result_summary: str = "",
                           user_context: Dict[str, Any] = None,
                           audit_level: int = None) -> Optional[Dict[str, Any]]:
        """
        Log an immediate event that doesn't require start/complete tracking.
        
        Args:
            operation_type: Type of operation/event
            operation_name: Specific name of the operation/event
            outcome: Outcome of the event
            result_summary: Summary of event results
            user_context: User-related context information
            audit_level: Audit verbosity level
            
        Returns:
            Audit entry if audit trail is available, None otherwise
        """
        if hasattr(self, 'audit_trail') and self.audit_trail:
            return self.audit_trail.log_immediate_event(
                operation_type=operation_type,
                operation_name=operation_name,
                agent_name=self.agent_name,
                outcome=outcome,
                result_summary=result_summary,
                user_context=user_context,
                audit_level=audit_level
            ).to_dict()
        return None
    
    @contextmanager
    def audited_operation_context(self,
                                 operation_type: Union[AuditOperationType, str],
                                 operation_name: str,
                                 user_context: Dict[str, Any] = None,
                                 audit_level: int = None):
        """
        Context manager for automatic audit trail logging of operations.
        
        This integrates with the standardized audit framework to provide
        automatic start/complete logging with proper error handling.
        
        Args:
            operation_type: Type of operation being audited
            operation_name: Specific name of the operation
            user_context: User-related context information
            audit_level: Audit verbosity level
            
        Yields:
            Request ID for the operation
            
        Example:
            with self.audited_operation_context(AuditOperationType.PII_DETECTION, "scan_document") as req_id:
                result = self.scan_for_pii(document_text)
                return result
        """
        if hasattr(self, 'audit_trail') and self.audit_trail:
            with audited_operation(
                audit_trail=self.audit_trail,
                operation_type=operation_type,
                operation_name=operation_name,
                agent_name=self.agent_name,
                user_context=user_context,
                audit_level=audit_level
            ) as request_id:
                yield request_id
        else:
            # Fallback context manager
            yield self._create_request_id("audit")