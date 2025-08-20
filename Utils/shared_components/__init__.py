"""
Shared Components Package for Agent Framework

Provides focused, modular components split from StandardImports.py
for better maintainability and reduced complexity.

Components:
- import_utils: Import handling utilities
- tool_interfaces: Tool interface protocols and containers  
- configuration: Configuration management
- file_processing: Streaming file processing utilities
- message_security: Secure message formatting
- exceptions: Standardized exception hierarchy
"""

# Import all shared components for easy access
from .import_utils import ImportUtils, get_common_utils, JsonType, CallableType, PathType
from .tool_interfaces import (
    WriteToolInterface, ReadToolInterface, GrepToolInterface, 
    ToolContainer
)
from .configuration import ConfigurationManager, config_manager, COMMON_PATTERNS
from .file_processing import StreamingFileProcessor
from .message_security import SecureMessageFormatter
from .exceptions import (
    StandardizedException, PerformanceException, 
    ConfigurationException, ToolIntegrationException
)

__all__ = [
    # Import utilities
    'ImportUtils', 'get_common_utils', 'JsonType', 'CallableType', 'PathType',
    
    # Tool interfaces
    'WriteToolInterface', 'ReadToolInterface', 'GrepToolInterface',
    'ToolContainer',
    
    # Configuration
    'ConfigurationManager', 'config_manager', 'COMMON_PATTERNS',
    
    # File processing
    'StreamingFileProcessor',
    
    # Security
    'SecureMessageFormatter',
    
    # Exceptions
    'StandardizedException', 'PerformanceException',
    'ConfigurationException', 'ToolIntegrationException'
]