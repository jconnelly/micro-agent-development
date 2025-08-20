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
from typing import Any, Callable, Dict, List, Optional, Pattern, Tuple, Union, Protocol

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


# =============================================================================
# Tool Interface Contracts (Phase 11 Architecture Improvement)
# =============================================================================

class WriteToolInterface(Protocol):
    """
    Protocol defining the interface for Write tool operations.
    
    Provides type-safe contract for file writing operations with Claude Code tools.
    Replaces raw Callable injections with structured interface.
    """
    
    def __call__(self, file_path: str, content: str) -> None:
        """
        Write content to a file with atomic operations.
        
        Args:
            file_path: Absolute path to the file to write
            content: Content to write to the file
            
        Raises:
            FileNotFoundError: If parent directory doesn't exist
            PermissionError: If write access is denied
            IOError: If write operation fails
        """
        ...


class ReadToolInterface(Protocol):
    """
    Protocol defining the interface for Read tool operations.
    
    Provides type-safe contract for file reading operations with Claude Code tools.
    """
    
    def __call__(self, file_path: str, offset: Optional[int] = None, limit: Optional[int] = None) -> str:
        """
        Read content from a file with optional offset and limit.
        
        Args:
            file_path: Absolute path to the file to read
            offset: Optional line number to start reading from
            limit: Optional maximum number of lines to read
            
        Returns:
            File content as string
            
        Raises:
            FileNotFoundError: If file doesn't exist
            PermissionError: If read access is denied
            IOError: If read operation fails
        """
        ...


class GrepToolInterface(Protocol):
    """
    Protocol defining the interface for Grep tool operations.
    
    Provides type-safe contract for high-performance regex searching operations.
    """
    
    def __call__(self, pattern: str, path: Optional[str] = None, 
                 output_mode: str = "files_with_matches", 
                 multiline: bool = False, **kwargs) -> str:
        """
        Search for patterns using optimized regex engine.
        
        Args:
            pattern: Regular expression pattern to search for
            path: Optional path to search in (defaults to current directory)
            output_mode: Output format ("content", "files_with_matches", "count")
            multiline: Whether to enable multiline matching
            **kwargs: Additional ripgrep options
            
        Returns:
            Search results as string
            
        Raises:
            ValueError: If pattern is invalid
            IOError: If search operation fails
        """
        ...


class ToolContainer:
    """
    Container for tool instances with type-safe interfaces.
    
    Provides structured access to Claude Code tools with proper typing
    and validation. Replaces raw Callable injections.
    """
    
    def __init__(self, 
                 write_tool: Optional[WriteToolInterface] = None,
                 read_tool: Optional[ReadToolInterface] = None, 
                 grep_tool: Optional[GrepToolInterface] = None):
        """
        Initialize tool container with optional tool instances.
        
        Args:
            write_tool: Write tool implementation
            read_tool: Read tool implementation  
            grep_tool: Grep tool implementation
        """
        self.write_tool = write_tool
        self.read_tool = read_tool
        self.grep_tool = grep_tool
    
    def has_write_tool(self) -> bool:
        """Check if write tool is available."""
        return self.write_tool is not None
    
    def has_read_tool(self) -> bool:
        """Check if read tool is available."""
        return self.read_tool is not None
    
    def has_grep_tool(self) -> bool:
        """Check if grep tool is available."""
        return self.grep_tool is not None
    
    def get_available_tools(self) -> List[str]:
        """Get list of available tool names."""
        tools = []
        if self.has_write_tool():
            tools.append("write")
        if self.has_read_tool():
            tools.append("read")
        if self.has_grep_tool():
            tools.append("grep")
        return tools
    
    def validate_tool_availability(self, required_tools: List[str]) -> bool:
        """
        Validate that all required tools are available.
        
        Args:
            required_tools: List of tool names that must be available
            
        Returns:
            True if all required tools are available
        """
        available = self.get_available_tools()
        return all(tool in available for tool in required_tools)


# =============================================================================
# Centralized Configuration Management (Phase 11 Architecture Improvement)
# =============================================================================

class ConfigurationManager:
    """
    Centralized configuration management system for all agents.
    
    Eliminates configuration loading pattern duplication across agents
    and provides consistent fallback handling with caching.
    
    Part of Phase 11 Performance & Architecture optimizations.
    """
    
    _instance = None
    _config_cache = {}
    _config_loader = None
    
    def __new__(cls):
        """Singleton pattern to ensure single configuration manager instance."""
        if cls._instance is None:
            cls._instance = super(ConfigurationManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize configuration manager with lazy config loader import."""
        if self._config_loader is None:
            try:
                # Import config_loader using standardized import utility
                utils = ImportUtils.import_utils('config_loader')
                self._config_loader = utils['config_loader']
            except Exception:
                self._config_loader = None  # Will use fallback mode
    
    def load_agent_config(self, config_name: str, fallback_config: Dict[str, Any], 
                         agent_name: str = "Agent", cache_key: str = None) -> Dict[str, Any]:
        """
        Load configuration with standardized fallback handling and caching.
        
        Args:
            config_name: Name of the configuration to load
            fallback_config: Fallback configuration dictionary
            agent_name: Name of the agent requesting configuration (for logging)
            cache_key: Optional cache key (defaults to config_name)
            
        Returns:
            Configuration dictionary (either loaded or fallback)
        """
        cache_key = cache_key or config_name
        
        # Check cache first
        if cache_key in self._config_cache:
            return self._config_cache[cache_key]
        
        # Try to load configuration
        if self._config_loader:
            try:
                config = self._config_loader.load_config(config_name, fallback_config)
                # Cache successful loads
                self._config_cache[cache_key] = config
                return config
            except Exception as e:
                # Log warning but continue with fallback
                print(f"[{agent_name}] Warning: Failed to load {config_name} configuration: {e}. Using fallback.")
                
        # Use fallback configuration
        self._config_cache[cache_key] = fallback_config
        return fallback_config
    
    def get_pii_patterns_config(self, agent_name: str = "PIIAgent") -> Dict[str, Any]:
        """Get PII patterns configuration with standard fallback."""
        fallback_patterns = {
            'patterns': {
                'ssn': {
                    'pattern': r'\b\d{3}-\d{2}-\d{4}\b',
                    'weight': 5,
                    'description': 'Social Security Number'
                },
                'credit_card': {
                    'pattern': r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
                    'weight': 5,
                    'description': 'Credit Card Number'
                },
                'phone': {
                    'pattern': r'\b\(\d{3}\)\s?\d{3}-\d{4}\b|\b\d{3}[-.\s]\d{3}[-.\s]\d{4}\b',
                    'weight': 3,
                    'description': 'Phone Number'
                },
                'email': {
                    'pattern': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                    'weight': 3,
                    'description': 'Email Address'
                }
            }
        }
        return self.load_agent_config("pii_patterns", fallback_patterns, agent_name)
    
    def get_domain_keywords_config(self, agent_name: str = "DocumentationAgent") -> Dict[str, Any]:
        """Get domain keywords configuration with standard fallback."""
        fallback_domain_keywords = {
            'domains': {
                'financial': {
                    'keywords': ['account', 'balance', 'payment', 'loan', 'credit', 'debit', 'transaction', 'banking', 'finance'],
                    'weight': 2
                },
                'healthcare': {
                    'keywords': ['patient', 'medical', 'diagnosis', 'treatment', 'health', 'doctor', 'hospital', 'clinic'],
                    'weight': 2
                },
                'insurance': {
                    'keywords': ['policy', 'claim', 'coverage', 'premium', 'deductible', 'beneficiary', 'insurance'],
                    'weight': 2
                },
                'legal': {
                    'keywords': ['contract', 'agreement', 'legal', 'court', 'judge', 'law', 'attorney', 'litigation'],
                    'weight': 2
                },
                'retail': {
                    'keywords': ['inventory', 'product', 'sale', 'customer', 'order', 'shipping', 'retail', 'store'],
                    'weight': 2
                },
                'general': {
                    'keywords': ['rule', 'condition', 'if', 'then', 'else', 'when', 'validate', 'check'],
                    'weight': 1
                }
            }
        }
        return self.load_agent_config("domains", fallback_domain_keywords, agent_name)
    
    def get_agent_defaults_config(self, agent_name: str = "BaseAgent") -> Dict[str, Any]:
        """Get agent defaults configuration with standard fallback."""
        fallback_config = {
            'timeouts': {
                'api_call_timeout': 30,
                'request_timeout': 60,
                'chunk_processing_timeout': 120
            },
            'retries': {
                'max_retries': 3,
                'base_delay': 1.0,
                'exponential_base': 2.0,
                'max_delay': 60.0
            },
            'caching': {
                'ip_cache_ttl': 300,
                'default_cache_size': 128,
                'pii_cache_size': 256
            },
            'performance': {
                'chunk_size': 1024,
                'batch_size': 50,
                'rate_limit_per_minute': 60
            }
        }
        return self.load_agent_config("agent_defaults", fallback_config, agent_name)
    
    def clear_cache(self) -> None:
        """Clear all cached configurations."""
        self._config_cache.clear()
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Get information about cached configurations."""
        return {
            'cached_configs': list(self._config_cache.keys()),
            'cache_size': len(self._config_cache),
            'config_loader_available': self._config_loader is not None
        }


# Global configuration manager instance
config_manager = ConfigurationManager()

# Common regex patterns used across agents
COMMON_PATTERNS = {
    'safe_filename': re.compile(r'[<>:"/\\|?*\x00-\x1f]'),
    'path_traversal': re.compile(r'\.\.[/\\]'),
    'whitespace_cleanup': re.compile(r'\s+')
}


class StreamingFileProcessor:
    """
    High-performance streaming file processor for large files (>100MB).
    
    Implements memory-efficient chunked processing to handle enterprise-scale
    files without loading entire contents into memory.
    
    Part of Phase 11 Performance & Architecture optimizations.
    """
    
    # Configuration constants for optimal performance
    DEFAULT_CHUNK_SIZE = 1024 * 1024  # 1MB chunks for good memory/performance balance
    MAX_CHUNK_SIZE = 10 * 1024 * 1024  # 10MB maximum chunk size
    MIN_CHUNK_SIZE = 64 * 1024  # 64KB minimum chunk size
    OVERLAP_SIZE = 1024  # 1KB overlap between chunks to avoid splitting entities
    
    @staticmethod
    def process_large_file_streaming(file_path: PathType, 
                                   chunk_processor: Callable[[str, Dict[str, Any]], Any],
                                   chunk_size: int = None,
                                   encoding: str = 'utf-8',
                                   metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process a large file in streaming chunks to minimize memory usage.
        
        Args:
            file_path: Path to the file to process
            chunk_processor: Function to process each chunk (chunk_text, chunk_metadata) -> result
            chunk_size: Size of each chunk in bytes (defaults to 1MB)
            encoding: File encoding (default: utf-8)
            metadata: Additional metadata to pass to chunk processor
            
        Returns:
            Dictionary with processing results and performance metrics
        """
        file_path = Path(file_path)
        chunk_size = chunk_size or StreamingFileProcessor.DEFAULT_CHUNK_SIZE
        metadata = metadata or {}
        
        # Validate parameters
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if chunk_size < StreamingFileProcessor.MIN_CHUNK_SIZE:
            chunk_size = StreamingFileProcessor.MIN_CHUNK_SIZE
        elif chunk_size > StreamingFileProcessor.MAX_CHUNK_SIZE:
            chunk_size = StreamingFileProcessor.MAX_CHUNK_SIZE
        
        # Get file info
        file_size = file_path.stat().st_size
        estimated_chunks = max(1, file_size // chunk_size)
        
        start_time = dt.now(timezone.utc)
        results = []
        total_bytes_processed = 0
        chunk_number = 0
        overlap_buffer = ""
        
        try:
            with open(file_path, 'r', encoding=encoding, buffering=8192) as file:
                while True:
                    # Read chunk with overlap consideration
                    chunk_data = file.read(chunk_size)
                    if not chunk_data:
                        break
                    
                    chunk_number += 1
                    
                    # Apply overlap from previous chunk
                    if overlap_buffer:
                        chunk_data = overlap_buffer + chunk_data
                        overlap_buffer = ""
                    
                    # Prepare overlap for next chunk (last 1KB of current chunk)
                    if len(chunk_data) > StreamingFileProcessor.OVERLAP_SIZE:
                        overlap_buffer = chunk_data[-StreamingFileProcessor.OVERLAP_SIZE:]
                    
                    total_bytes_processed += len(chunk_data.encode(encoding))
                    
                    # Prepare chunk metadata
                    chunk_metadata = {
                        'chunk_number': chunk_number,
                        'chunk_size': len(chunk_data),
                        'total_chunks_estimated': estimated_chunks,
                        'total_bytes_processed': total_bytes_processed,
                        'file_size': file_size,
                        'progress_percentage': min(100.0, (total_bytes_processed / file_size) * 100),
                        'file_path': str(file_path),
                        **metadata
                    }
                    
                    # Process chunk
                    chunk_result = chunk_processor(chunk_data, chunk_metadata)
                    results.append({
                        'chunk_number': chunk_number,
                        'chunk_metadata': chunk_metadata,
                        'result': chunk_result
                    })
        
        except Exception as e:
            return {
                'success': False,
                'error': f"Streaming processing failed: {e}",
                'chunks_processed': chunk_number,
                'bytes_processed': total_bytes_processed,
                'duration_ms': (dt.now(timezone.utc) - start_time).total_seconds() * 1000
            }
        
        # Calculate final statistics
        end_time = dt.now(timezone.utc)
        duration_ms = (end_time - start_time).total_seconds() * 1000
        
        return {
            'success': True,
            'total_chunks': chunk_number,
            'total_bytes_processed': total_bytes_processed,
            'file_size': file_size,
            'duration_ms': duration_ms,
            'throughput_mb_per_sec': (total_bytes_processed / (1024 * 1024)) / (duration_ms / 1000) if duration_ms > 0 else 0,
            'chunks_per_second': chunk_number / (duration_ms / 1000) if duration_ms > 0 else 0,
            'results': results,
            'performance_metrics': {
                'memory_efficient': True,
                'streaming_method': 'chunk_based',
                'chunk_size_bytes': chunk_size,
                'overlap_size_bytes': StreamingFileProcessor.OVERLAP_SIZE,
                'estimated_vs_actual_chunks': f"{estimated_chunks} estimated, {chunk_number} actual"
            }
        }
    
    @staticmethod
    def get_file_size_category(file_path: PathType) -> str:
        """
        Categorize file size for processing strategy selection.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Size category string: 'small', 'medium', 'large', 'huge'
        """
        try:
            size_bytes = Path(file_path).stat().st_size
            size_mb = size_bytes / (1024 * 1024)
            
            if size_mb < 1:
                return 'small'
            elif size_mb < 10:
                return 'medium'
            elif size_mb < 100:
                return 'large'
            else:
                return 'huge'
        except (OSError, FileNotFoundError):
            return 'unknown'
    
    @staticmethod
    def should_use_streaming(file_path: PathType, threshold_mb: int = 10) -> bool:
        """
        Determine if a file should use streaming processing based on size.
        
        Args:
            file_path: Path to the file
            threshold_mb: Size threshold in MB (default: 10MB)
            
        Returns:
            True if file should use streaming processing
        """
        try:
            size_bytes = Path(file_path).stat().st_size
            size_mb = size_bytes / (1024 * 1024)
            return size_mb >= threshold_mb
        except (OSError, FileNotFoundError):
            return False


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


# Export commonly used items for easy importing
__all__ = [
    # Standard library re-exports
    'datetime', 'json', 'os', 're', 'sys', 'uuid', 'Path',
    
    # Type annotations
    'Any', 'Callable', 'Dict', 'List', 'Optional', 'Pattern', 'Tuple', 'Union', 'Protocol',
    
    # DateTime utilities 
    'dt', 'timezone',
    
    # Custom types
    'JsonType', 'CallableType', 'PathType',
    
    # Tool interface contracts
    'WriteToolInterface', 'ReadToolInterface', 'GrepToolInterface', 'ToolContainer',
    
    # Utilities
    'ImportUtils', 'get_common_utils', 'COMMON_PATTERNS',
    
    # Configuration management
    'ConfigurationManager', 'config_manager',
    
    # Performance utilities  
    'StreamingFileProcessor',
    
    # Security utilities
    'SecureMessageFormatter',
    
    # Exception handling
    'StandardizedException', 'PerformanceException', 'ConfigurationException', 'ToolIntegrationException'
]