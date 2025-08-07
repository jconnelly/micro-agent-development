"""
JSON Utilities - Safe JSON parsing and serialization functions.

Provides robust JSON handling with consistent error handling across agents.
"""

import json
from typing import Any, Dict, List, Optional, Union


class JsonUtils:
    """Utility class for safe JSON operations across agents."""
    
    @staticmethod
    def safe_loads(
        json_string: str, 
        default: Any = None,
        raise_on_error: bool = False
    ) -> Any:
        """
        Safely parse JSON string with error handling.
        
        Args:
            json_string: JSON string to parse
            default: Default value to return on parse error
            raise_on_error: Whether to raise exception on error
            
        Returns:
            Parsed JSON object or default value
            
        Raises:
            json.JSONDecodeError: If raise_on_error is True and parsing fails
        """
        try:
            return json.loads(json_string)
        except (json.JSONDecodeError, TypeError) as e:
            if raise_on_error:
                raise e
            return default
    
    @staticmethod
    def safe_dumps(
        data: Any, 
        indent: int = 2, 
        default: Optional[str] = None,
        raise_on_error: bool = False,
        ensure_ascii: bool = False
    ) -> str:
        """
        Safely serialize object to JSON string with error handling.
        
        Args:
            data: Object to serialize
            indent: JSON indentation level
            default: Default string to return on error
            raise_on_error: Whether to raise exception on error
            ensure_ascii: Whether to escape non-ASCII characters
            
        Returns:
            JSON string or default value
            
        Raises:
            TypeError: If raise_on_error is True and serialization fails
        """
        try:
            return json.dumps(data, indent=indent, ensure_ascii=ensure_ascii)
        except (TypeError, ValueError) as e:
            if raise_on_error:
                raise e
            return str(data) if default is None else default
    
    @staticmethod
    def safe_loads_dict(
        json_string: str, 
        default: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Safely parse JSON string ensuring result is a dictionary.
        
        Args:
            json_string: JSON string to parse
            default: Default dict to return on error
            
        Returns:
            Dictionary object or default
        """
        if default is None:
            default = {}
            
        try:
            result = json.loads(json_string)
            if isinstance(result, dict):
                return result
            else:
                return default
        except (json.JSONDecodeError, TypeError):
            return default
    
    @staticmethod
    def safe_loads_list(
        json_string: str, 
        default: Optional[List] = None
    ) -> List[Any]:
        """
        Safely parse JSON string ensuring result is a list.
        
        Args:
            json_string: JSON string to parse
            default: Default list to return on error
            
        Returns:
            List object or default
        """
        if default is None:
            default = []
            
        try:
            result = json.loads(json_string)
            if isinstance(result, list):
                return result
            else:
                return default
        except (json.JSONDecodeError, TypeError):
            return default
    
    @staticmethod
    def extract_json_from_text(text: str) -> Optional[Dict[str, Any]]:
        """
        Extract JSON object from text that may contain other content.
        
        Looks for text between ```json and ``` or { and } blocks.
        
        Args:
            text: Text containing JSON
            
        Returns:
            Extracted JSON dict or None
        """
        import re
        
        # Try to find JSON in code blocks first
        json_block_match = re.search(r'```json\s*\n(.*?)\n```', text, re.DOTALL | re.IGNORECASE)
        if json_block_match:
            json_text = json_block_match.group(1).strip()
            result = JsonUtils.safe_loads_dict(json_text)
            if result:
                return result
        
        # Try to find standalone JSON objects
        brace_matches = re.finditer(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text, re.DOTALL)
        for match in brace_matches:
            json_text = match.group(0).strip()
            result = JsonUtils.safe_loads_dict(json_text)
            if result:
                return result
        
        return None
    
    @staticmethod
    def validate_json_structure(
        data: Any, 
        required_keys: List[str] = None,
        expected_types: Dict[str, type] = None
    ) -> tuple[bool, List[str]]:
        """
        Validate JSON structure against requirements.
        
        Args:
            data: Data to validate
            required_keys: Keys that must be present (for dict validation)
            expected_types: Expected types for specific keys
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        if required_keys and isinstance(data, dict):
            for key in required_keys:
                if key not in data:
                    errors.append(f"Missing required key: {key}")
        
        if expected_types and isinstance(data, dict):
            for key, expected_type in expected_types.items():
                if key in data and not isinstance(data[key], expected_type):
                    errors.append(f"Key '{key}' expected type {expected_type.__name__}, got {type(data[key]).__name__}")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def merge_json_objects(
        base: Dict[str, Any], 
        updates: Dict[str, Any], 
        deep_merge: bool = True
    ) -> Dict[str, Any]:
        """
        Merge two JSON objects together.
        
        Args:
            base: Base dictionary
            updates: Dictionary with updates to merge
            deep_merge: Whether to perform deep merge for nested dicts
            
        Returns:
            Merged dictionary
        """
        result = base.copy()
        
        for key, value in updates.items():
            if (deep_merge and 
                key in result and 
                isinstance(result[key], dict) and 
                isinstance(value, dict)):
                result[key] = JsonUtils.merge_json_objects(result[key], value, deep_merge)
            else:
                result[key] = value
        
        return result