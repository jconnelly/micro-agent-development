#!/usr/bin/env python3

"""
Standardized Import Utilities for Agent Framework (Phase 14 Refactored)

Provides consistent import patterns and utilities across all agent classes,
now organized into focused modules for better maintainability.

This module was refactored as part of Phase 14 Medium Priority Task #1:
Breaking down large class files into focused modules.
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

# Import focused shared components
try:
    # Try relative import first (when running as part of package)
    from ..Utils.shared_components import (
        # Import utilities
        ImportUtils, get_common_utils, JsonType, CallableType, PathType,
        
        # Tool interfaces
        WriteToolInterface, ReadToolInterface, GrepToolInterface, ToolContainer,
        
        # Configuration management
        ConfigurationManager, config_manager, COMMON_PATTERNS,
        
        # File processing
        StreamingFileProcessor,
        
        # Security
        SecureMessageFormatter,
        
        # Exceptions
        StandardizedException, PerformanceException, 
        ConfigurationException, ToolIntegrationException
    )
except ImportError:
    # Fallback to absolute import (when running standalone)
    import sys
    import os
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    
    from Utils.shared_components import (
        # Import utilities
        ImportUtils, get_common_utils, JsonType, CallableType, PathType,
        
        # Tool interfaces
        WriteToolInterface, ReadToolInterface, GrepToolInterface, ToolContainer,
        
        # Configuration management
        ConfigurationManager, config_manager, COMMON_PATTERNS,
        
        # File processing
        StreamingFileProcessor,
        
        # Security
        SecureMessageFormatter,
        
        # Exceptions
        StandardizedException, PerformanceException, 
        ConfigurationException, ToolIntegrationException
    )


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