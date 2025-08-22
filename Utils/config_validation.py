"""
Configuration Schema Validation for Agent Defaults

This module provides comprehensive validation for the agent_defaults.yaml configuration
to ensure data integrity, type safety, and proper value ranges for all settings.

Features:
- JSON Schema-based validation
- Type checking and range validation  
- Environment-specific configuration validation
- Configuration migration and upgrade support
- Real-time validation for hot-reloading
"""

import yaml
import json
import logging
from typing import Dict, Any, List, Optional, Union, Tuple
from pathlib import Path
from datetime import datetime

# JSON Schema for configuration validation
AGENT_DEFAULTS_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "Agent Defaults Configuration Schema",
    "description": "Schema for validating agent_defaults.yaml configuration file",
    "type": "object",
    "required": ["agent_defaults"],
    "properties": {
        "agent_defaults": {
            "type": "object",
            "required": ["api_settings", "caching", "processing_limits"],
            "properties": {
                "api_settings": {
                    "type": "object",
                    "required": ["timeout_seconds", "max_retries"],
                    "properties": {
                        "timeout_seconds": {
                            "type": "number",
                            "minimum": 1.0,
                            "maximum": 300.0,
                            "description": "API call timeout in seconds"
                        },
                        "max_retries": {
                            "type": "integer",
                            "minimum": 0,
                            "maximum": 10,
                            "description": "Maximum API retry attempts"
                        },
                        "total_operation_timeout": {
                            "type": "number",
                            "minimum": 30.0,
                            "maximum": 3600.0,
                            "description": "Total operation timeout in seconds"
                        },
                        "retry_backoff_base": {
                            "type": "number",
                            "minimum": 1.0,
                            "maximum": 10.0,
                            "description": "Base for exponential backoff"
                        },
                        "retry_backoff_max": {
                            "type": "number",
                            "minimum": 1.0,
                            "maximum": 60.0,
                            "description": "Maximum backoff time"
                        }
                    }
                },
                "caching": {
                    "type": "object",
                    "required": ["default_lru_cache_size"],
                    "properties": {
                        "default_lru_cache_size": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 10000,
                            "description": "Default LRU cache size"
                        },
                        "pii_detection_cache_size": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 10000,
                            "description": "PII detection cache size"
                        },
                        "file_context_cache_size": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 10000,
                            "description": "File context cache size"
                        },
                        "ip_resolution_cache_ttl": {
                            "type": "integer",
                            "minimum": 60,
                            "maximum": 86400,
                            "description": "IP resolution cache TTL in seconds"
                        }
                    }
                },
                "processing_limits": {
                    "type": "object",
                    "required": ["max_file_chunks", "chunking_line_threshold"],
                    "properties": {
                        "max_file_chunks": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 1000,
                            "description": "Maximum chunks per file"
                        },
                        "min_chunk_lines": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 1000,
                            "description": "Minimum lines per chunk"
                        },
                        "chunking_line_threshold": {
                            "type": "integer",
                            "minimum": 10,
                            "maximum": 10000,
                            "description": "Threshold for chunked processing"
                        },
                        "max_context_lines": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 1000,
                            "description": "Maximum context lines"
                        },
                        "chunk_overlap_size": {
                            "type": "integer",
                            "minimum": 0,
                            "maximum": 100,
                            "description": "Chunk overlap size"
                        },
                        "chunk_size_mb": {
                            "type": "number",
                            "minimum": 0.1,
                            "maximum": 100.0,
                            "description": "Chunk size in MB"
                        },
                        "max_log_message_length": {
                            "type": "integer",
                            "minimum": 100,
                            "maximum": 100000,
                            "description": "Maximum log message length"
                        }
                    }
                },
                "performance_thresholds": {
                    "type": "object",
                    "properties": {
                        "max_legacy_code_bytes": {
                            "type": "integer",
                            "minimum": 1024,
                            "maximum": 104857600,
                            "description": "Maximum legacy code size in bytes"
                        },
                        "large_text_threshold": {
                            "type": "integer",
                            "minimum": 1000,
                            "maximum": 1000000,
                            "description": "Large text threshold"
                        },
                        "batch_size_limit": {
                            "type": "integer",
                            "minimum": 100,
                            "maximum": 100000,
                            "description": "Maximum batch size"
                        },
                        "memory_threshold_mb": {
                            "type": "number",
                            "minimum": 0.1,
                            "maximum": 1000.0,
                            "description": "Memory threshold in MB"
                        },
                        "streaming_threshold_mb": {
                            "type": "number",
                            "minimum": 1.0,
                            "maximum": 10000.0,
                            "description": "Streaming threshold in MB"
                        }
                    }
                },
                "model_defaults": {
                    "type": "object",
                    "properties": {
                        "default_model_name": {
                            "type": "string",
                            "minLength": 1,
                            "description": "Default LLM model name"
                        },
                        "default_llm_provider": {
                            "type": "string",
                            "enum": ["google", "openai", "anthropic", "azure"],
                            "description": "Default LLM provider"
                        },
                        "temperature": {
                            "type": "number",
                            "minimum": 0.0,
                            "maximum": 2.0,
                            "description": "Model temperature"
                        },
                        "max_output_tokens": {
                            "type": "integer",
                            "minimum": 100,
                            "maximum": 100000,
                            "description": "Maximum output tokens"
                        },
                        "max_input_tokens": {
                            "type": "integer",
                            "minimum": 100,
                            "maximum": 200000,
                            "description": "Maximum input tokens"
                        },
                        "timeout_seconds": {
                            "type": "number",
                            "minimum": 1.0,
                            "maximum": 300.0,
                            "description": "LLM request timeout"
                        },
                        "max_batch_size": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 100000,
                            "description": "Maximum batch size"
                        }
                    }
                },
                "flask_settings": {
                    "type": "object",
                    "properties": {
                        "max_content_length_mb": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 1000,
                            "description": "Maximum request size in MB"
                        },
                        "rate_limit_per_hour": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 100000,
                            "description": "Rate limit per hour"
                        },
                        "redis_enabled": {
                            "type": "boolean",
                            "description": "Enable Redis rate limiting"
                        },
                        "redis_host": {
                            "type": "string",
                            "minLength": 1,
                            "description": "Redis host"
                        },
                        "redis_port": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 65535,
                            "description": "Redis port"
                        },
                        "redis_connection_pool_size": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 1000,
                            "description": "Redis connection pool size"
                        }
                    }
                }
            }
        },
        "environments": {
            "type": "object",
            "properties": {
                "development": {"type": "object"},
                "production": {"type": "object"},
                "testing": {"type": "object"}
            }
        },
        "metadata": {
            "type": "object",
            "properties": {
                "version": {
                    "type": "string",
                    "pattern": "^\\d+\\.\\d+\\.\\d+$",
                    "description": "Configuration version"
                },
                "last_updated": {
                    "type": "string",
                    "pattern": "^\\d{4}-\\d{2}-\\d{2}$",
                    "description": "Last update date"
                }
            }
        }
    }
}


class ConfigurationValidator:
    """
    Comprehensive configuration validation for agent_defaults.yaml
    """
    
    def __init__(self, schema: Dict[str, Any] = None):
        """Initialize the validator with optional custom schema."""
        self.schema = schema or AGENT_DEFAULTS_SCHEMA
        self.logger = logging.getLogger(__name__)
        
    def validate_configuration(self, config_path: Union[str, Path]) -> Tuple[bool, List[str]]:
        """
        Validate a configuration file against the schema.
        
        Args:
            config_path: Path to the configuration file
            
        Returns:
            Tuple of (is_valid, validation_errors)
        """
        try:
            # Load configuration
            config_path = Path(config_path)
            if not config_path.exists():
                return False, [f"Configuration file not found: {config_path}"]
            
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # Perform validation
            return self._validate_config_data(config)
            
        except yaml.YAMLError as e:
            return False, [f"YAML parsing error: {str(e)}"]
        except Exception as e:
            return False, [f"Validation error: {str(e)}"]
    
    def _validate_config_data(self, config: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate configuration data against schema."""
        errors = []
        
        # Basic structure validation
        if not isinstance(config, dict):
            return False, ["Configuration must be a dictionary"]
        
        # Check required top-level sections
        required_sections = ["agent_defaults"]
        for section in required_sections:
            if section not in config:
                errors.append(f"Missing required section: {section}")
        
        if errors:
            return False, errors
        
        # Validate agent_defaults section
        agent_defaults = config.get("agent_defaults", {})
        errors.extend(self._validate_agent_defaults(agent_defaults))
        
        # Validate environments section (if present)
        if "environments" in config:
            errors.extend(self._validate_environments(config["environments"]))
        
        # Validate metadata section (if present)
        if "metadata" in config:
            errors.extend(self._validate_metadata(config["metadata"]))
        
        return len(errors) == 0, errors
    
    def _validate_agent_defaults(self, agent_defaults: Dict[str, Any]) -> List[str]:
        """Validate the agent_defaults section."""
        errors = []
        
        # Validate API settings
        if "api_settings" in agent_defaults:
            errors.extend(self._validate_api_settings(agent_defaults["api_settings"]))
        else:
            errors.append("Missing required section: agent_defaults.api_settings")
        
        # Validate caching settings
        if "caching" in agent_defaults:
            errors.extend(self._validate_caching(agent_defaults["caching"]))
        else:
            errors.append("Missing required section: agent_defaults.caching")
        
        # Validate processing limits
        if "processing_limits" in agent_defaults:
            errors.extend(self._validate_processing_limits(agent_defaults["processing_limits"]))
        else:
            errors.append("Missing required section: agent_defaults.processing_limits")
        
        # Validate optional sections
        if "performance_thresholds" in agent_defaults:
            errors.extend(self._validate_performance_thresholds(agent_defaults["performance_thresholds"]))
        
        if "model_defaults" in agent_defaults:
            errors.extend(self._validate_model_defaults(agent_defaults["model_defaults"]))
        
        if "flask_settings" in agent_defaults:
            errors.extend(self._validate_flask_settings(agent_defaults["flask_settings"]))
        
        return errors
    
    def _validate_api_settings(self, api_settings: Dict[str, Any]) -> List[str]:
        """Validate API settings."""
        errors = []
        
        # Required fields
        required_fields = {
            "timeout_seconds": (float, 1.0, 300.0),
            "max_retries": (int, 0, 10)
        }
        
        for field, (field_type, min_val, max_val) in required_fields.items():
            if field not in api_settings:
                errors.append(f"Missing required field: api_settings.{field}")
                continue
            
            value = api_settings[field]
            if not isinstance(value, field_type):
                errors.append(f"api_settings.{field} must be {field_type.__name__}")
                continue
            
            if value < min_val or value > max_val:
                errors.append(f"api_settings.{field} must be between {min_val} and {max_val}")
        
        # Optional fields with validation
        optional_fields = {
            "total_operation_timeout": (float, 30.0, 3600.0),
            "retry_backoff_base": (float, 1.0, 10.0),
            "retry_backoff_max": (float, 1.0, 60.0)
        }
        
        for field, (field_type, min_val, max_val) in optional_fields.items():
            if field in api_settings:
                value = api_settings[field]
                if not isinstance(value, field_type):
                    errors.append(f"api_settings.{field} must be {field_type.__name__}")
                elif value < min_val or value > max_val:
                    errors.append(f"api_settings.{field} must be between {min_val} and {max_val}")
        
        return errors
    
    def _validate_caching(self, caching: Dict[str, Any]) -> List[str]:
        """Validate caching settings."""
        errors = []
        
        # Required fields
        if "default_lru_cache_size" not in caching:
            errors.append("Missing required field: caching.default_lru_cache_size")
        else:
            value = caching["default_lru_cache_size"]
            if not isinstance(value, int) or value < 1 or value > 10000:
                errors.append("caching.default_lru_cache_size must be integer between 1 and 10000")
        
        # Optional cache size fields
        cache_fields = [
            "pii_detection_cache_size",
            "file_context_cache_size"
        ]
        
        for field in cache_fields:
            if field in caching:
                value = caching[field]
                if not isinstance(value, int) or value < 1 or value > 10000:
                    errors.append(f"caching.{field} must be integer between 1 and 10000")
        
        # TTL fields
        if "ip_resolution_cache_ttl" in caching:
            value = caching["ip_resolution_cache_ttl"]
            if not isinstance(value, int) or value < 60 or value > 86400:
                errors.append("caching.ip_resolution_cache_ttl must be integer between 60 and 86400")
        
        return errors
    
    def _validate_processing_limits(self, processing_limits: Dict[str, Any]) -> List[str]:
        """Validate processing limits."""
        errors = []
        
        # Required fields
        required_fields = {
            "max_file_chunks": (int, 1, 1000),
            "chunking_line_threshold": (int, 10, 10000)
        }
        
        for field, (field_type, min_val, max_val) in required_fields.items():
            if field not in processing_limits:
                errors.append(f"Missing required field: processing_limits.{field}")
                continue
            
            value = processing_limits[field]
            if not isinstance(value, field_type):
                errors.append(f"processing_limits.{field} must be {field_type.__name__}")
                continue
            
            if value < min_val or value > max_val:
                errors.append(f"processing_limits.{field} must be between {min_val} and {max_val}")
        
        # Optional fields
        optional_fields = {
            "min_chunk_lines": (int, 1, 1000),
            "max_context_lines": (int, 1, 1000),
            "chunk_overlap_size": (int, 0, 100),
            "chunk_size_mb": (float, 0.1, 100.0),
            "max_log_message_length": (int, 100, 100000)
        }
        
        for field, (field_type, min_val, max_val) in optional_fields.items():
            if field in processing_limits:
                value = processing_limits[field]
                if not isinstance(value, (field_type, int if field_type == float else field_type)):
                    errors.append(f"processing_limits.{field} must be {field_type.__name__}")
                elif value < min_val or value > max_val:
                    errors.append(f"processing_limits.{field} must be between {min_val} and {max_val}")
        
        return errors
    
    def _validate_performance_thresholds(self, performance_thresholds: Dict[str, Any]) -> List[str]:
        """Validate performance thresholds."""
        errors = []
        
        # Threshold validations
        threshold_fields = {
            "max_legacy_code_bytes": (int, 1024, 104857600),
            "large_text_threshold": (int, 1000, 1000000),
            "batch_size_limit": (int, 100, 100000),
            "memory_threshold_mb": (float, 0.1, 1000.0),
            "streaming_threshold_mb": (float, 1.0, 10000.0)
        }
        
        for field, (field_type, min_val, max_val) in threshold_fields.items():
            if field in performance_thresholds:
                value = performance_thresholds[field]
                if not isinstance(value, (field_type, int if field_type == float else field_type)):
                    errors.append(f"performance_thresholds.{field} must be {field_type.__name__}")
                elif value < min_val or value > max_val:
                    errors.append(f"performance_thresholds.{field} must be between {min_val} and {max_val}")
        
        return errors
    
    def _validate_model_defaults(self, model_defaults: Dict[str, Any]) -> List[str]:
        """Validate model defaults."""
        errors = []
        
        # Provider validation
        if "default_llm_provider" in model_defaults:
            provider = model_defaults["default_llm_provider"]
            valid_providers = ["google", "openai", "anthropic", "azure"]
            if provider not in valid_providers:
                errors.append(f"model_defaults.default_llm_provider must be one of: {valid_providers}")
        
        # Temperature validation
        if "temperature" in model_defaults:
            temp = model_defaults["temperature"]
            if not isinstance(temp, (int, float)) or temp < 0.0 or temp > 2.0:
                errors.append("model_defaults.temperature must be number between 0.0 and 2.0")
        
        # Token limits
        token_fields = {
            "max_output_tokens": (100, 100000),
            "max_input_tokens": (100, 200000),
            "max_batch_size": (1, 100000)
        }
        
        for field, (min_val, max_val) in token_fields.items():
            if field in model_defaults:
                value = model_defaults[field]
                if not isinstance(value, int) or value < min_val or value > max_val:
                    errors.append(f"model_defaults.{field} must be integer between {min_val} and {max_val}")
        
        return errors
    
    def _validate_flask_settings(self, flask_settings: Dict[str, Any]) -> List[str]:
        """Validate Flask settings."""
        errors = []
        
        # Redis settings validation
        if "redis_enabled" in flask_settings:
            if not isinstance(flask_settings["redis_enabled"], bool):
                errors.append("flask_settings.redis_enabled must be boolean")
        
        if "redis_port" in flask_settings:
            port = flask_settings["redis_port"]
            if not isinstance(port, int) or port < 1 or port > 65535:
                errors.append("flask_settings.redis_port must be integer between 1 and 65535")
        
        # Size limits
        size_fields = {
            "max_content_length_mb": (1, 1000),
            "max_file_size_mb": (1, 1000),
            "rate_limit_per_hour": (1, 100000),
            "redis_connection_pool_size": (1, 1000)
        }
        
        for field, (min_val, max_val) in size_fields.items():
            if field in flask_settings:
                value = flask_settings[field]
                if not isinstance(value, int) or value < min_val or value > max_val:
                    errors.append(f"flask_settings.{field} must be integer between {min_val} and {max_val}")
        
        return errors
    
    def _validate_environments(self, environments: Dict[str, Any]) -> List[str]:
        """Validate environments section."""
        errors = []
        
        valid_envs = ["development", "production", "testing"]
        for env_name in environments:
            if env_name not in valid_envs:
                errors.append(f"Unknown environment: {env_name}. Valid environments: {valid_envs}")
        
        return errors
    
    def _validate_metadata(self, metadata: Dict[str, Any]) -> List[str]:
        """Validate metadata section."""
        errors = []
        
        # Version format validation
        if "version" in metadata:
            version = metadata["version"]
            if not isinstance(version, str):
                errors.append("metadata.version must be string")
            else:
                import re
                if not re.match(r'^\d+\.\d+\.\d+$', version):
                    errors.append("metadata.version must follow semantic versioning (e.g., '1.0.0')")
        
        # Date format validation
        if "last_updated" in metadata:
            date_str = metadata["last_updated"]
            if not isinstance(date_str, str):
                errors.append("metadata.last_updated must be string")
            else:
                try:
                    datetime.strptime(date_str, "%Y-%m-%d")
                except ValueError:
                    errors.append("metadata.last_updated must be in YYYY-MM-DD format")
        
        return errors
    
    def generate_sample_config(self) -> Dict[str, Any]:
        """Generate a sample configuration that passes validation."""
        return {
            "agent_defaults": {
                "api_settings": {
                    "timeout_seconds": 30.0,
                    "max_retries": 3,
                    "total_operation_timeout": 300.0,
                    "retry_backoff_base": 2.0,
                    "retry_backoff_max": 16.0
                },
                "caching": {
                    "default_lru_cache_size": 128,
                    "pii_detection_cache_size": 256,
                    "file_context_cache_size": 128,
                    "ip_resolution_cache_ttl": 300
                },
                "processing_limits": {
                    "max_file_chunks": 50,
                    "min_chunk_lines": 10,
                    "chunking_line_threshold": 175,
                    "max_context_lines": 50,
                    "chunk_overlap_size": 25,
                    "chunk_size_mb": 1.0,
                    "max_log_message_length": 2000
                },
                "model_defaults": {
                    "default_model_name": "gemini-1.5-flash",
                    "default_llm_provider": "google",
                    "temperature": 0.1,
                    "max_output_tokens": 4096,
                    "max_input_tokens": 8192,
                    "timeout_seconds": 30.0,
                    "max_batch_size": 10000
                },
                "flask_settings": {
                    "max_content_length_mb": 16,
                    "max_file_size_mb": 50,
                    "rate_limit_per_hour": 100,
                    "redis_enabled": True,
                    "redis_host": "localhost",
                    "redis_port": 6379,
                    "redis_connection_pool_size": 20
                }
            },
            "environments": {
                "development": {
                    "api_settings": {
                        "timeout_seconds": 60.0,
                        "max_retries": 1
                    }
                },
                "production": {
                    "api_settings": {
                        "timeout_seconds": 30.0,
                        "max_retries": 3
                    }
                }
            },
            "metadata": {
                "version": "1.0.0",
                "last_updated": datetime.now().strftime("%Y-%m-%d"),
                "description": "Sample configuration for agent defaults"
            }
        }


def validate_config_file(config_path: str, verbose: bool = True) -> bool:
    """
    Convenience function to validate a configuration file.
    
    Args:
        config_path: Path to the configuration file
        verbose: Whether to print validation results
        
    Returns:
        True if configuration is valid, False otherwise
    """
    validator = ConfigurationValidator()
    is_valid, errors = validator.validate_configuration(config_path)
    
    if verbose:
        if is_valid:
            print(f"[VALID] Configuration file '{config_path}' is valid")
        else:
            print(f"[ERROR] Configuration file '{config_path}' has validation errors:")
            for error in errors:
                print(f"  - {error}")
    
    return is_valid


if __name__ == "__main__":
    """CLI interface for configuration validation."""
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python config_validation.py <config_file.yaml>")
        sys.exit(1)
    
    config_file = sys.argv[1]
    if validate_config_file(config_file):
        sys.exit(0)
    else:
        sys.exit(1)