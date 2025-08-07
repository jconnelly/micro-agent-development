"""
BaseAgent - Abstract base class for all AI agents.

This class provides common functionality that is shared across all agent implementations,
eliminating code duplication and ensuring consistency in behavior, logging, and error handling.
"""

import socket
import asyncio
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from datetime import datetime, timezone

from .Logger import AgentLogger
from .AuditingAgent import AgentAuditing

# Import Utils - handle both relative and absolute imports
try:
    from ..Utils import RequestIdGenerator, TimeUtils
except ImportError:
    import sys
    import os
    # Add parent directory to path for Utils
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    from Utils import RequestIdGenerator, TimeUtils


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
        audit_system: AgentAuditing, 
        agent_id: str = None,
        log_level: int = 0,
        model_name: str = "unknown",
        llm_provider: str = "unknown",
        agent_name: str = "BaseAgent"
    ):
        """
        Initialize base agent with common configuration.
        
        Args:
            audit_system: The auditing system instance for logging
            agent_id: Unique identifier for this agent instance
            log_level: 0 for production (silent), 1 for development (verbose)
            model_name: Name of the LLM model being used
            llm_provider: Name of the LLM provider (e.g., "openai", "anthropic")
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
        
        # LLM configuration
        self.model_name = model_name
        self.llm_provider = llm_provider
        
        # System dependencies
        self.audit_system = audit_system
        
        # Initialize logger
        self.logger = AgentLogger(
            log_level=log_level,
            agent_name=agent_name
        )
        
        # Common configuration constants
        self.API_DELAY_SECONDS = 1.0
        self.API_TIMEOUT_SECONDS = 30.0
        self.MAX_RETRIES = 3
        self.TOTAL_OPERATION_TIMEOUT = 300.0  # 5 minutes
        
        # Cache for expensive operations
        self._ip_address_cache = None
        
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
            # If audit logging fails, fall back to regular logging
            self.logger.error(f"Failed to log exception to audit: {str(audit_error)}")
            self.logger.error(f"Original exception: {str(exception)}")
    
    async def _api_call_with_retry_async(
        self, 
        api_call_func,
        *args,
        max_retries: Optional[int] = None,
        timeout_seconds: Optional[float] = None,
        **kwargs
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
                    raise TimeoutError(f"API call failed after {max_retries} attempts due to timeouts")
                    
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
        api_call_func,
        *args,
        max_retries: Optional[int] = None,
        timeout_seconds: Optional[float] = None,
        **kwargs
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
        async def async_wrapper():
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