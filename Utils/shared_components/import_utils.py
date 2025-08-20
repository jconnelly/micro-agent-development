#!/usr/bin/env python3

"""
Import Utilities for Agent Framework

Provides standardized import patterns and utilities across all agent classes,
eliminating code duplication and ensuring consistent import behavior.

This module was extracted from StandardImports.py as part of Phase 14
code quality improvements to break down large class files.
"""

import os
import sys
from typing import Any, Dict, List, Union, Callable
from pathlib import Path


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