"""
Comprehensive Input Validation Framework for Agent Platform

This module provides standardized input validation and sanitization across all agents,
implementing Phase 14 Medium Priority Task #6: Improve input validation and strengthen
file path validation.

Key features:
- Secure file path validation with path traversal prevention
- Parameter type checking and data sanitization
- Integration with standardized error handling
- Business-logic validation for agent-specific inputs
- Enterprise security patterns and OWASP compliance
"""

import os
import re
import uuid
from pathlib import Path, PurePath
from typing import Any, Dict, List, Optional, Union, Callable, Type, Tuple
from urllib.parse import unquote
from enum import Enum
from datetime import datetime, timezone

from Agents.Exceptions import ValidationError


class ValidationSeverity(Enum):
    """Severity levels for validation failures."""
    INFO = 1                # Minor issues that can be auto-corrected
    WARNING = 2             # Issues that should be noted but not fatal
    ERROR = 3               # Issues that prevent operation but allow retry
    CRITICAL = 4            # Security-critical issues that require immediate attention
    
    def __lt__(self, other):
        if self.__class__ is other.__class__:
            return self.value < other.value
        return NotImplemented
    
    def __le__(self, other):
        if self.__class__ is other.__class__:
            return self.value <= other.value
        return NotImplemented
    
    def __gt__(self, other):
        if self.__class__ is other.__class__:
            return self.value > other.value
        return NotImplemented
    
    def __ge__(self, other):
        if self.__class__ is other.__class__:
            return self.value >= other.value
        return NotImplemented
    
    @property
    def name_str(self) -> str:
        """Get string representation of severity level."""
        names = {1: "info", 2: "warning", 3: "error", 4: "critical"}
        return names[self.value]


class PathValidationResult:
    """Result object for file path validation operations."""
    
    def __init__(self, 
                 is_valid: bool,
                 sanitized_path: Optional[Path] = None,
                 severity: ValidationSeverity = ValidationSeverity.ERROR,
                 issues: List[str] = None,
                 recommendations: List[str] = None):
        """
        Initialize path validation result.
        
        Args:
            is_valid: Whether the path passed validation
            sanitized_path: Sanitized version of the path if valid
            severity: Severity level of any issues found
            issues: List of validation issues found
            recommendations: List of recommendations to fix issues
        """
        self.is_valid = is_valid
        self.sanitized_path = sanitized_path
        self.severity = severity
        self.issues = issues or []
        self.recommendations = recommendations or []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for logging/serialization."""
        return {
            'is_valid': self.is_valid,
            'sanitized_path': str(self.sanitized_path) if self.sanitized_path else None,
            'severity': self.severity.name_str,
            'issues': self.issues,
            'recommendations': self.recommendations
        }


class SecureFilePathValidator:
    """
    Enterprise-grade file path validator with security hardening.
    
    Prevents path traversal attacks, validates against whitelisted directories,
    and provides comprehensive path sanitization.
    """
    
    # Dangerous path patterns that should be blocked
    DANGEROUS_PATTERNS = [
        r'\.\.[\\/]',           # Path traversal attempts
        r'^[\\/]',              # Absolute paths (can be dangerous)
        r'[\\/]\.\.[\\/]',      # Mid-path traversals
        r'[\\/]\.\.$',          # Path ending with traversal
        r'[<>:"|?*]',           # Windows reserved characters
        r'[\x00-\x1f]',         # Control characters
        r'^\s+|\s+$',           # Leading/trailing whitespace
        r'\.{3,}',              # Multiple consecutive dots
        r'[\\/]{2,}',           # Multiple consecutive slashes
    ]
    
    # Reserved filenames (Windows)
    RESERVED_NAMES = {
        'CON', 'PRN', 'AUX', 'NUL',
        'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
        'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
    }
    
    def __init__(self, 
                 allowed_base_dirs: List[Union[str, Path]] = None,
                 allowed_extensions: List[str] = None,
                 max_path_length: int = 260,
                 max_filename_length: int = 255):
        """
        Initialize secure file path validator.
        
        Args:
            allowed_base_dirs: List of allowed base directories (whitelist)
            allowed_extensions: List of allowed file extensions (e.g., ['.txt', '.json'])
            max_path_length: Maximum allowed path length (260 for Windows compatibility)
            max_filename_length: Maximum allowed filename length
        """
        self.allowed_base_dirs = [Path(d).resolve() for d in (allowed_base_dirs or [])]
        self.allowed_extensions = [ext.lower() for ext in (allowed_extensions or [])]
        self.max_path_length = max_path_length
        self.max_filename_length = max_filename_length
        
        # Compile regex patterns for performance
        self.dangerous_pattern_regex = [re.compile(pattern, re.IGNORECASE) for pattern in self.DANGEROUS_PATTERNS]
    
    def validate_path(self, path: Union[str, Path], 
                     operation_context: str = "file_operation") -> PathValidationResult:
        """
        Comprehensively validate a file path for security and correctness.
        
        Args:
            path: File path to validate
            operation_context: Description of the operation for error context
            
        Returns:
            PathValidationResult with validation outcome and details
        """
        issues = []
        recommendations = []
        severity = ValidationSeverity.INFO
        
        # Convert to string for initial validation
        path_str = str(path).strip()
        
        # Basic null/empty checks
        if not path_str:
            return PathValidationResult(
                is_valid=False,
                severity=ValidationSeverity.ERROR,
                issues=["Path is empty or None"],
                recommendations=["Provide a valid file path string"]
            )
        
        # URL decode if path appears to be URL-encoded
        if '%' in path_str:
            try:
                path_str = unquote(path_str)
                recommendations.append("Path was URL-decoded")
            except Exception:
                issues.append("Path contains invalid URL encoding")
                severity = ValidationSeverity.ERROR
        
        # Check for dangerous patterns
        for i, pattern_regex in enumerate(self.dangerous_pattern_regex):
            if pattern_regex.search(path_str):
                issues.append(f"Path contains dangerous pattern: {self.DANGEROUS_PATTERNS[i]}")
                severity = ValidationSeverity.CRITICAL
        
        # Convert to Path object for further validation
        try:
            path_obj = Path(path_str)
        except Exception as e:
            return PathValidationResult(
                is_valid=False,
                severity=ValidationSeverity.ERROR,
                issues=[f"Invalid path format: {e}"],
                recommendations=["Ensure path uses valid characters and format"]
            )
        
        # Check path length limits
        if len(path_str) > self.max_path_length:
            issues.append(f"Path too long ({len(path_str)} > {self.max_path_length})")
            severity = max(severity, ValidationSeverity.ERROR)
        
        # Check filename length if it has a name component
        if path_obj.name and len(path_obj.name) > self.max_filename_length:
            issues.append(f"Filename too long ({len(path_obj.name)} > {self.max_filename_length})")
            severity = max(severity, ValidationSeverity.ERROR)
        
        # Check for reserved filenames (Windows)
        if path_obj.stem.upper() in self.RESERVED_NAMES:
            issues.append(f"Filename '{path_obj.stem}' is reserved")
            severity = max(severity, ValidationSeverity.ERROR)
            recommendations.append("Use a different filename")
        
        # Check file extension if whitelist provided
        if self.allowed_extensions and path_obj.suffix:
            if path_obj.suffix.lower() not in self.allowed_extensions:
                issues.append(f"File extension '{path_obj.suffix}' not allowed")
                severity = max(severity, ValidationSeverity.ERROR)
                recommendations.append(f"Use one of: {', '.join(self.allowed_extensions)}")
        
        # Resolve path and check against allowed base directories
        sanitized_path = None
        try:
            resolved_path = path_obj.resolve()
            
            if self.allowed_base_dirs:
                is_within_allowed = False
                for base_dir in self.allowed_base_dirs:
                    try:
                        # Check if resolved path is within allowed base directory
                        resolved_path.relative_to(base_dir)
                        is_within_allowed = True
                        break
                    except ValueError:
                        continue
                
                if not is_within_allowed:
                    issues.append("Path is outside allowed directories")
                    severity = ValidationSeverity.CRITICAL
                    recommendations.append(f"Path must be within: {[str(d) for d in self.allowed_base_dirs]}")
                else:
                    sanitized_path = resolved_path
            else:
                sanitized_path = resolved_path
                
        except Exception as e:
            issues.append(f"Could not resolve path: {e}")
            severity = max(severity, ValidationSeverity.ERROR)
        
        # Additional security checks for relative paths
        if not path_obj.is_absolute() and any('../' in part or '..\\'in part for part in path_obj.parts):
            issues.append("Relative path contains parent directory references")
            severity = ValidationSeverity.CRITICAL
        
        # Determine if validation passed (only INFO and WARNING are considered valid)
        is_valid = severity in [ValidationSeverity.INFO, ValidationSeverity.WARNING]
        
        return PathValidationResult(
            is_valid=is_valid,
            sanitized_path=sanitized_path if is_valid else None,
            severity=severity,
            issues=issues,
            recommendations=recommendations
        )
    
    def sanitize_path(self, path: Union[str, Path]) -> Path:
        """
        Sanitize a path by removing dangerous elements and normalizing format.
        
        Args:
            path: Path to sanitize
            
        Returns:
            Sanitized Path object
            
        Raises:
            ValidationError: If path cannot be safely sanitized
        """
        validation_result = self.validate_path(path, "path_sanitization")
        
        if not validation_result.is_valid:
            raise ValidationError(
                f"Cannot sanitize unsafe path: {'; '.join(validation_result.issues)}",
                context={
                    'original_path': str(path),
                    'issues': validation_result.issues,
                    'severity': validation_result.severity.value
                }
            )
        
        return validation_result.sanitized_path


class ParameterValidator:
    """
    Comprehensive parameter validation for agent inputs.
    
    Validates data types, ranges, formats, and business logic constraints
    across all agent operations.
    """
    
    def __init__(self):
        """Initialize parameter validator with standard validation rules."""
        # Common validation patterns
        self.patterns = {
            'request_id': re.compile(r'^[a-zA-Z0-9_-]{1,50}$'),
            'agent_name': re.compile(r'^[a-zA-Z][a-zA-Z0-9_]{2,50}$'),
            'audit_level': re.compile(r'^[0-4]$'),
            'email': re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'),
            'safe_string': re.compile(r'^[a-zA-Z0-9\s\-_.,!?()]+$'),
        }
        
        # Data type validators
        self.type_validators = {
            str: self._validate_string,
            int: self._validate_integer, 
            float: self._validate_float,
            bool: self._validate_boolean,
            dict: self._validate_dictionary,
            list: self._validate_list
        }
    
    def validate_parameter(self, 
                          name: str,
                          value: Any, 
                          expected_type: Type = None,
                          min_value: Union[int, float] = None,
                          max_value: Union[int, float] = None,
                          min_length: int = None,
                          max_length: int = None,
                          pattern: str = None,
                          allowed_values: List[Any] = None,
                          required: bool = True) -> Tuple[bool, Any, List[str]]:
        """
        Validate a single parameter with comprehensive checks.
        
        Args:
            name: Parameter name for error messages
            value: Value to validate
            expected_type: Expected Python type
            min_value: Minimum numeric value
            max_value: Maximum numeric value  
            min_length: Minimum string/list length
            max_length: Maximum string/list length
            pattern: Regex pattern name or custom pattern
            allowed_values: List of allowed values (whitelist)
            required: Whether parameter is required
            
        Returns:
            Tuple of (is_valid, sanitized_value, issues)
        """
        issues = []
        sanitized_value = value
        
        # Handle None/missing values
        if value is None:
            if required:
                issues.append(f"Parameter '{name}' is required but was None")
                return False, None, issues
            else:
                return True, None, []
        
        # Type validation
        if expected_type and not isinstance(value, expected_type):
            # Try type coercion for basic types
            try:
                if expected_type in [int, float, str, bool]:
                    sanitized_value = expected_type(value)
                else:
                    issues.append(f"Parameter '{name}' must be {expected_type.__name__}, got {type(value).__name__}")
                    return False, value, issues
            except (ValueError, TypeError):
                issues.append(f"Parameter '{name}' cannot be converted to {expected_type.__name__}")
                return False, value, issues
        
        # Use type-specific validator
        if expected_type in self.type_validators:
            type_valid, type_issues = self.type_validators[expected_type](name, sanitized_value)
            if not type_valid:
                issues.extend(type_issues)
        
        # Range validation for numeric types
        if isinstance(sanitized_value, (int, float)):
            if min_value is not None and sanitized_value < min_value:
                issues.append(f"Parameter '{name}' ({sanitized_value}) is below minimum ({min_value})")
            if max_value is not None and sanitized_value > max_value:
                issues.append(f"Parameter '{name}' ({sanitized_value}) exceeds maximum ({max_value})")
        
        # Length validation for strings and lists
        if hasattr(sanitized_value, '__len__'):
            length = len(sanitized_value)
            if min_length is not None and length < min_length:
                issues.append(f"Parameter '{name}' length ({length}) is below minimum ({min_length})")
            if max_length is not None and length > max_length:
                issues.append(f"Parameter '{name}' length ({length}) exceeds maximum ({max_length})")
        
        # Pattern validation
        if pattern and isinstance(sanitized_value, str):
            if pattern in self.patterns:
                regex = self.patterns[pattern]
            else:
                try:
                    regex = re.compile(pattern)
                except re.error:
                    issues.append(f"Invalid regex pattern for parameter '{name}': {pattern}")
                    return False, sanitized_value, issues
            
            if not regex.match(sanitized_value):
                issues.append(f"Parameter '{name}' does not match required pattern")
        
        # Allowed values validation (whitelist)
        if allowed_values and sanitized_value not in allowed_values:
            issues.append(f"Parameter '{name}' must be one of: {allowed_values}")
        
        is_valid = len(issues) == 0
        return is_valid, sanitized_value, issues
    
    def validate_parameters(self, 
                           parameters: Dict[str, Any],
                           validation_rules: Dict[str, Dict[str, Any]]) -> Tuple[bool, Dict[str, Any], Dict[str, List[str]]]:
        """
        Validate multiple parameters according to validation rules.
        
        Args:
            parameters: Dictionary of parameter names to values
            validation_rules: Dictionary of parameter names to validation rule dictionaries
            
        Returns:
            Tuple of (all_valid, sanitized_parameters, issues_by_parameter)
        """
        all_valid = True
        sanitized_parameters = {}
        issues_by_parameter = {}
        
        # Validate each parameter according to its rules
        for param_name, rules in validation_rules.items():
            param_value = parameters.get(param_name)
            
            is_valid, sanitized_value, issues = self.validate_parameter(
                param_name, param_value, **rules
            )
            
            sanitized_parameters[param_name] = sanitized_value
            if issues:
                issues_by_parameter[param_name] = issues
                all_valid = False
        
        # Check for unexpected parameters
        expected_params = set(validation_rules.keys())
        provided_params = set(parameters.keys())
        unexpected_params = provided_params - expected_params
        
        if unexpected_params:
            issues_by_parameter['_unexpected'] = [
                f"Unexpected parameters: {', '.join(unexpected_params)}"
            ]
            all_valid = False
        
        return all_valid, sanitized_parameters, issues_by_parameter
    
    def _validate_string(self, name: str, value: str) -> Tuple[bool, List[str]]:
        """Validate string parameter."""
        issues = []
        
        # Check for potential injection attempts
        dangerous_patterns = [
            r'<script[^>]*>',      # Script tags
            r'javascript:',        # JavaScript URLs
            r'on\w+\s*=',         # Event handlers
            r'[\x00-\x08\x0B\x0C\x0E-\x1F]',  # Control characters
            r'\$\([^)]*\)',       # jQuery selectors (potential)
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, value, re.IGNORECASE):
                issues.append(f"String parameter '{name}' contains potentially dangerous content")
                break
        
        return len(issues) == 0, issues
    
    def _validate_integer(self, name: str, value: int) -> Tuple[bool, List[str]]:
        """Validate integer parameter.""" 
        issues = []
        
        # Check for reasonable integer bounds
        if value < -2**31 or value > 2**31 - 1:
            issues.append(f"Integer parameter '{name}' is outside reasonable bounds")
        
        return len(issues) == 0, issues
    
    def _validate_float(self, name: str, value: float) -> Tuple[bool, List[str]]:
        """Validate float parameter."""
        issues = []
        
        # Check for special float values
        if not (-1e10 <= value <= 1e10):  # Reasonable bounds
            issues.append(f"Float parameter '{name}' is outside reasonable bounds")
        
        return len(issues) == 0, issues
    
    def _validate_boolean(self, name: str, value: bool) -> Tuple[bool, List[str]]:
        """Validate boolean parameter."""
        # Boolean validation is straightforward
        return True, []
    
    def _validate_dictionary(self, name: str, value: dict) -> Tuple[bool, List[str]]:
        """Validate dictionary parameter."""
        issues = []
        
        # Check dictionary size
        if len(value) > 1000:  # Reasonable limit
            issues.append(f"Dictionary parameter '{name}' has too many keys")
        
        # Check for deeply nested structures
        max_depth = self._calculate_dict_depth(value)
        if max_depth > 10:
            issues.append(f"Dictionary parameter '{name}' is too deeply nested")
        
        return len(issues) == 0, issues
    
    def _validate_list(self, name: str, value: list) -> Tuple[bool, List[str]]:
        """Validate list parameter."""
        issues = []
        
        # Check list size
        if len(value) > 10000:  # Reasonable limit
            issues.append(f"List parameter '{name}' has too many items")
        
        return len(issues) == 0, issues
    
    def _calculate_dict_depth(self, d: dict, current_depth: int = 0) -> int:
        """Calculate maximum nesting depth of a dictionary."""
        if not isinstance(d, dict):
            return current_depth
        
        max_depth = current_depth
        for value in d.values():
            if isinstance(value, dict):
                depth = self._calculate_dict_depth(value, current_depth + 1)
                max_depth = max(max_depth, depth)
        
        return max_depth


class InputValidationError(ValidationError):
    """
    Specialized exception for input validation failures.
    """
    
    def __init__(self, message: str, parameter_name: str = None, 
                 validation_issues: Dict[str, List[str]] = None, **kwargs):
        """
        Initialize input validation error.
        
        Args:
            message: Error message
            parameter_name: Name of the parameter that failed validation
            validation_issues: Dictionary of validation issues by parameter
            **kwargs: Additional context for parent ValidationError
        """
        super().__init__(message, **kwargs)
        self.parameter_name = parameter_name
        self.validation_issues = validation_issues or {}


# Export commonly used components
__all__ = [
    'ValidationSeverity',
    'PathValidationResult',
    'SecureFilePathValidator',
    'ParameterValidator',
    'InputValidationError'
]