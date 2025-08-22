#!/usr/bin/env python3

"""
Enhanced Input Validation System

Provides comprehensive input validation for file paths, parameters, and data
with security-focused validation patterns to prevent injection attacks and
ensure data integrity across all agent operations.
"""

import os
import re
import json
from pathlib import Path, PurePath
from typing import Any, Dict, List, Optional, Union, Callable, Type
from urllib.parse import urlparse

from Agents.Exceptions import ValidationError


class InputValidator:
    """
    Comprehensive input validation system with security-focused patterns.
    """
    
    # Security patterns to block dangerous inputs
    DANGEROUS_PATH_PATTERNS = [
        r'\.\.[\\/]',           # Directory traversal
        r'[\\/]\.\.[\\/]',      # Directory traversal
        r'^\.\.[\\/]',          # Directory traversal at start
        r'[\\/]\.',             # Hidden files/directories
        r'[<>:"|?*]',           # Windows invalid characters
        r'\x00',                # Null bytes
        r'[\x01-\x1f]',         # Control characters
        r'^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])$',  # Windows reserved names
        r'^(con|prn|aux|nul|com[1-9]|lpt[1-9])$',  # Case insensitive reserved names
    ]
    
    DANGEROUS_INPUT_PATTERNS = [
        r'<script[^>]*>.*?</script>',  # Script tags
        r'javascript:',                # JavaScript protocol
        r'vbscript:',                 # VBScript protocol
        r'data:',                     # Data protocol
        r'\\x[0-9a-fA-F]{2}',        # Hex-encoded characters
        r'%[0-9a-fA-F]{2}',          # URL-encoded characters
        r'&#[0-9]+;',                # HTML entities
        r'&#x[0-9a-fA-F]+;',         # Hex HTML entities
        r'\${.*}',                   # Template injection
        r'#{.*}',                    # Template injection
        r'\|[^|]*\|',               # Command injection pipes
        r';.*[;&|]',                # Command separators
        r'`.*`',                    # Backticks (command substitution)
    ]
    
    # Valid file extensions for different operations
    ALLOWED_DOCUMENT_EXTENSIONS = {
        '.txt', '.md', '.doc', '.docx', '.pdf', '.rtf', '.odt',
        '.csv', '.tsv', '.json', '.xml', '.html', '.htm',
        '.py', '.java', '.cpp', '.c', '.js', '.ts', '.sql',
        '.cobol', '.cob', '.cbl', '.for', '.f90', '.pas', '.pl'
    }
    
    ALLOWED_CONFIG_EXTENSIONS = {
        '.yaml', '.yml', '.json', '.ini', '.cfg', '.conf', '.toml'
    }
    
    @staticmethod
    def validate_file_path(
        file_path: str,
        must_exist: bool = False,
        allowed_extensions: Optional[set] = None,
        max_path_length: int = 260,
        allow_relative: bool = True,
        request_id: Optional[str] = None
    ) -> str:
        """
        Validate file path for security and correctness.
        
        Args:
            file_path: Path to validate
            must_exist: Whether file must exist on filesystem
            allowed_extensions: Set of allowed file extensions
            max_path_length: Maximum allowed path length
            allow_relative: Whether to allow relative paths
            request_id: Request ID for error correlation
            
        Returns:
            Normalized absolute path
            
        Raises:
            ValidationError: If path is invalid or dangerous
        """
        if not isinstance(file_path, str):
            raise ValidationError(
                f"Invalid file path type: expected string, got {type(file_path).__name__}",
                context={"field": "file_path", "value_type": type(file_path).__name__},
                request_id=request_id
            )
        
        if not file_path.strip():
            raise ValidationError(
                "File path cannot be empty",
                context={"field": "file_path"},
                request_id=request_id
            )
        
        # Check path length
        if len(file_path) > max_path_length:
            raise ValidationError(
                f"File path too long: {len(file_path)} characters (max: {max_path_length})",
                context={"field": "file_path", "length": len(file_path), "max_length": max_path_length},
                request_id=request_id
            )
        
        # Check for dangerous patterns
        for pattern in InputValidator.DANGEROUS_PATH_PATTERNS:
            if re.search(pattern, file_path, re.IGNORECASE):
                raise ValidationError(
                    f"File path contains dangerous pattern: {pattern}",
                    context={"field": "file_path", "dangerous_pattern": pattern},
                    request_id=request_id
                )
        
        # Normalize and validate path
        try:
            normalized_path = os.path.normpath(file_path)
            path_obj = Path(normalized_path)
            
            # Check if relative paths are allowed
            if not allow_relative and not path_obj.is_absolute():
                raise ValidationError(
                    "Relative paths not allowed",
                    context={"field": "file_path", "path": file_path},
                    request_id=request_id
                )
            
            # Convert to absolute path for consistency
            if not path_obj.is_absolute():
                abs_path = path_obj.resolve()
            else:
                abs_path = path_obj
            
            # Check for path traversal after normalization
            if '..' in abs_path.parts:
                raise ValidationError(
                    "Path traversal detected in normalized path",
                    context={"field": "file_path", "normalized_path": str(abs_path)},
                    request_id=request_id
                )
            
            # Validate file extension if specified
            if allowed_extensions:
                file_extension = abs_path.suffix.lower()
                if file_extension not in allowed_extensions:
                    raise ValidationError(
                        f"Invalid file extension: {file_extension}",
                        context={
                            "field": "file_path",
                            "extension": file_extension,
                            "allowed_extensions": list(allowed_extensions)
                        },
                        request_id=request_id
                    )
            
            # Check existence if required
            if must_exist and not abs_path.exists():
                raise ValidationError(
                    f"File does not exist: {abs_path}",
                    context={"field": "file_path", "path": str(abs_path)},
                    request_id=request_id
                )
            
            return str(abs_path)
            
        except (OSError, ValueError) as e:
            raise ValidationError(
                f"Invalid file path: {str(e)}",
                context={"field": "file_path", "path": file_path, "error": str(e)},
                request_id=request_id
            )
    
    @staticmethod
    def validate_string_input(
        value: str,
        field_name: str,
        min_length: int = 0,
        max_length: int = 10000,
        allow_empty: bool = False,
        allowed_chars: Optional[str] = None,
        disallowed_patterns: Optional[List[str]] = None,
        request_id: Optional[str] = None
    ) -> str:
        """
        Validate string input with security checks.
        
        Args:
            value: String value to validate
            field_name: Name of the field being validated
            min_length: Minimum string length
            max_length: Maximum string length
            allow_empty: Whether empty strings are allowed
            allowed_chars: Regex pattern of allowed characters
            disallowed_patterns: List of disallowed regex patterns
            request_id: Request ID for error correlation
            
        Returns:
            Validated string
            
        Raises:
            ValidationError: If string is invalid
        """
        if not isinstance(value, str):
            raise ValidationError(
                f"Invalid {field_name} type: expected string, got {type(value).__name__}",
                context={"field": field_name, "value_type": type(value).__name__},
                request_id=request_id
            )
        
        # Check empty value
        if not value.strip() and not allow_empty:
            raise ValidationError(
                f"{field_name} cannot be empty",
                context={"field": field_name},
                request_id=request_id
            )
        
        # Check length constraints
        if len(value) < min_length:
            raise ValidationError(
                f"{field_name} too short: {len(value)} characters (min: {min_length})",
                context={"field": field_name, "length": len(value), "min_length": min_length},
                request_id=request_id
            )
        
        if len(value) > max_length:
            raise ValidationError(
                f"{field_name} too long: {len(value)} characters (max: {max_length})",
                context={"field": field_name, "length": len(value), "max_length": max_length},
                request_id=request_id
            )
        
        # Check for dangerous patterns
        for pattern in InputValidator.DANGEROUS_INPUT_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                raise ValidationError(
                    f"{field_name} contains dangerous pattern",
                    context={"field": field_name, "dangerous_pattern": pattern},
                    request_id=request_id
                )
        
        # Check custom disallowed patterns
        if disallowed_patterns:
            for pattern in disallowed_patterns:
                if re.search(pattern, value, re.IGNORECASE):
                    raise ValidationError(
                        f"{field_name} contains disallowed pattern",
                        context={"field": field_name, "pattern": pattern},
                        request_id=request_id
                    )
        
        # Check allowed characters
        if allowed_chars and not re.match(f'^[{allowed_chars}]*$', value):
            raise ValidationError(
                f"{field_name} contains invalid characters",
                context={"field": field_name, "allowed_chars": allowed_chars},
                request_id=request_id
            )
        
        return value
    
    @staticmethod
    def validate_json_input(
        value: str,
        field_name: str,
        max_size: int = 1000000,  # 1MB
        required_keys: Optional[List[str]] = None,
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Validate JSON input string.
        
        Args:
            value: JSON string to validate
            field_name: Name of the field being validated
            max_size: Maximum JSON size in bytes
            required_keys: List of required top-level keys
            request_id: Request ID for error correlation
            
        Returns:
            Parsed JSON object
            
        Raises:
            ValidationError: If JSON is invalid
        """
        if not isinstance(value, str):
            raise ValidationError(
                f"Invalid {field_name} type: expected string, got {type(value).__name__}",
                context={"field": field_name, "value_type": type(value).__name__},
                request_id=request_id
            )
        
        # Check size
        if len(value.encode('utf-8')) > max_size:
            raise ValidationError(
                f"{field_name} too large: {len(value.encode('utf-8'))} bytes (max: {max_size})",
                context={"field": field_name, "size": len(value.encode('utf-8')), "max_size": max_size},
                request_id=request_id
            )
        
        # Parse JSON
        try:
            json_obj = json.loads(value)
        except json.JSONDecodeError as e:
            raise ValidationError(
                f"Invalid JSON in {field_name}: {str(e)}",
                context={"field": field_name, "json_error": str(e)},
                request_id=request_id
            )
        
        # Check required keys
        if required_keys and isinstance(json_obj, dict):
            missing_keys = [key for key in required_keys if key not in json_obj]
            if missing_keys:
                raise ValidationError(
                    f"Missing required keys in {field_name}: {missing_keys}",
                    context={"field": field_name, "missing_keys": missing_keys},
                    request_id=request_id
                )
        
        return json_obj
    
    @staticmethod
    def validate_numeric_input(
        value: Union[int, float, str],
        field_name: str,
        value_type: Type = int,
        min_value: Optional[Union[int, float]] = None,
        max_value: Optional[Union[int, float]] = None,
        request_id: Optional[str] = None
    ) -> Union[int, float]:
        """
        Validate numeric input.
        
        Args:
            value: Numeric value to validate
            field_name: Name of the field being validated
            value_type: Expected numeric type (int or float)
            min_value: Minimum allowed value
            max_value: Maximum allowed value
            request_id: Request ID for error correlation
            
        Returns:
            Validated numeric value
            
        Raises:
            ValidationError: If value is invalid
        """
        # Convert string to numeric if needed
        if isinstance(value, str):
            try:
                if value_type == int:
                    value = int(value)
                elif value_type == float:
                    value = float(value)
                else:
                    raise ValueError(f"Unsupported numeric type: {value_type}")
            except ValueError as e:
                raise ValidationError(
                    f"Invalid {field_name}: cannot convert '{value}' to {value_type.__name__}",
                    context={"field": field_name, "value": str(value), "target_type": value_type.__name__},
                    request_id=request_id
                )
        
        # Check type
        if not isinstance(value, (int, float)) or (value_type == int and isinstance(value, float) and value != int(value)):
            raise ValidationError(
                f"Invalid {field_name} type: expected {value_type.__name__}, got {type(value).__name__}",
                context={"field": field_name, "value_type": type(value).__name__, "expected_type": value_type.__name__},
                request_id=request_id
            )
        
        # Convert to target type
        if value_type == int:
            value = int(value)
        elif value_type == float:
            value = float(value)
        
        # Check range
        if min_value is not None and value < min_value:
            raise ValidationError(
                f"{field_name} too small: {value} (min: {min_value})",
                context={"field": field_name, "value": value, "min_value": min_value},
                request_id=request_id
            )
        
        if max_value is not None and value > max_value:
            raise ValidationError(
                f"{field_name} too large: {value} (max: {max_value})",
                context={"field": field_name, "value": value, "max_value": max_value},
                request_id=request_id
            )
        
        return value
    
    @staticmethod
    def validate_list_input(
        value: List[Any],
        field_name: str,
        min_length: int = 0,
        max_length: int = 1000,
        item_validator: Optional[Callable] = None,
        allowed_types: Optional[tuple] = None,
        request_id: Optional[str] = None
    ) -> List[Any]:
        """
        Validate list input.
        
        Args:
            value: List to validate
            field_name: Name of the field being validated
            min_length: Minimum list length
            max_length: Maximum list length
            item_validator: Function to validate each item
            allowed_types: Tuple of allowed types for list items
            request_id: Request ID for error correlation
            
        Returns:
            Validated list
            
        Raises:
            ValidationError: If list is invalid
        """
        if not isinstance(value, list):
            raise ValidationError(
                f"Invalid {field_name} type: expected list, got {type(value).__name__}",
                context={"field": field_name, "value_type": type(value).__name__},
                request_id=request_id
            )
        
        # Check length
        if len(value) < min_length:
            raise ValidationError(
                f"{field_name} too short: {len(value)} items (min: {min_length})",
                context={"field": field_name, "length": len(value), "min_length": min_length},
                request_id=request_id
            )
        
        if len(value) > max_length:
            raise ValidationError(
                f"{field_name} too long: {len(value)} items (max: {max_length})",
                context={"field": field_name, "length": len(value), "max_length": max_length},
                request_id=request_id
            )
        
        # Validate items
        for i, item in enumerate(value):
            # Check item type
            if allowed_types and not isinstance(item, allowed_types):
                raise ValidationError(
                    f"Invalid item type in {field_name}[{i}]: expected {allowed_types}, got {type(item).__name__}",
                    context={"field": field_name, "index": i, "item_type": type(item).__name__, "allowed_types": str(allowed_types)},
                    request_id=request_id
                )
            
            # Custom item validation
            if item_validator:
                try:
                    item_validator(item)
                except ValidationError as e:
                    raise ValidationError(
                        f"Invalid item in {field_name}[{i}]: {e.message}",
                        context={"field": field_name, "index": i, "item_error": e.message},
                        request_id=request_id
                    )
        
        return value


# Convenience validation functions for common scenarios
def validate_agent_file_path(file_path: str, request_id: Optional[str] = None) -> str:
    """Validate file path for agent document processing."""
    return InputValidator.validate_file_path(
        file_path=file_path,
        allowed_extensions=InputValidator.ALLOWED_DOCUMENT_EXTENSIONS,
        must_exist=True,
        request_id=request_id
    )


def validate_config_file_path(file_path: str, request_id: Optional[str] = None) -> str:
    """Validate file path for configuration files."""
    return InputValidator.validate_file_path(
        file_path=file_path,
        allowed_extensions=InputValidator.ALLOWED_CONFIG_EXTENSIONS,
        must_exist=True,
        request_id=request_id
    )


def validate_agent_id(agent_id: str, request_id: Optional[str] = None) -> str:
    """Validate agent ID format."""
    return InputValidator.validate_string_input(
        value=agent_id,
        field_name="agent_id",
        min_length=1,
        max_length=100,
        allowed_chars=r'a-zA-Z0-9_\-',
        request_id=request_id
    )


def validate_request_id(request_id: str, request_id_context: Optional[str] = None) -> str:
    """Validate request ID format."""
    return InputValidator.validate_string_input(
        value=request_id,
        field_name="request_id",
        min_length=1,
        max_length=100,
        allowed_chars=r'a-zA-Z0-9_\-',
        request_id=request_id_context
    )


def validate_user_input(user_input: str, request_id: Optional[str] = None) -> str:
    """Validate user input with security filtering."""
    return InputValidator.validate_string_input(
        value=user_input,
        field_name="user_input",
        min_length=1,
        max_length=50000,
        request_id=request_id
    )


# Export key components
__all__ = [
    'InputValidator',
    'validate_agent_file_path',
    'validate_config_file_path', 
    'validate_agent_id',
    'validate_request_id',
    'validate_user_input'
]