#!/usr/bin/env python3

"""
Configuration Loader Utility

Provides centralized configuration loading with graceful degradation and validation.
Supports YAML configuration files with fallback to hardcoded defaults.

Author: AI Development Team
Version: 1.0.0
"""

import os
import logging
from typing import Dict, Any, Optional, Union
from pathlib import Path

# Try to import PyYAML with graceful fallback
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False
    logging.warning("PyYAML not available. Configuration will use fallback mechanisms.")


class ConfigurationLoader:
    """
    Centralized configuration loader with fallback mechanisms and validation.
    """
    
    def __init__(self, config_dir: str = "config"):
        """
        Initialize the configuration loader.
        
        Args:
            config_dir: Directory containing configuration files
        """
        self.config_dir = Path(config_dir)
        self.logger = logging.getLogger(__name__)
        
        # Cache for loaded configurations
        self._config_cache: Dict[str, Any] = {}
        
    def load_config(self, config_name: str, fallback_data: Optional[Dict[str, Any]] = None, 
                   validate_schema: bool = True) -> Dict[str, Any]:
        """
        Load configuration from YAML file with fallback mechanisms.
        
        Args:
            config_name: Name of configuration file (without extension)
            fallback_data: Fallback data if file loading fails
            validate_schema: Whether to validate the loaded configuration
            
        Returns:
            Configuration dictionary
            
        Raises:
            ValueError: If configuration is invalid and no fallback available
        """
        # Check cache first
        cache_key = f"{config_name}"
        if cache_key in self._config_cache:
            return self._config_cache[cache_key]
            
        config_file = self.config_dir / f"{config_name}.yaml"
        
        # Try to load from YAML file
        if YAML_AVAILABLE and config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config_data = yaml.safe_load(f)
                
                if validate_schema:
                    self._validate_config(config_name, config_data)
                
                self._config_cache[cache_key] = config_data
                self.logger.info(f"Loaded configuration from {config_file}")
                return config_data
                
            except (yaml.YAMLError, IOError, ValueError) as e:
                self.logger.warning(f"Failed to load {config_file}: {e}")
                if fallback_data is None:
                    raise ValueError(f"Configuration loading failed and no fallback provided: {e}")
                    
        # Use fallback data
        if fallback_data is not None:
            self.logger.info(f"Using fallback configuration for {config_name}")
            if validate_schema:
                self._validate_config(config_name, fallback_data)
            self._config_cache[cache_key] = fallback_data
            return fallback_data
            
        raise ValueError(f"No configuration available for {config_name} (file not found, YAML not available, no fallback)")
    
    def _validate_config(self, config_name: str, config_data: Dict[str, Any]) -> None:
        """
        Validate configuration data based on config type.
        
        Args:
            config_name: Name of the configuration
            config_data: Configuration data to validate
            
        Raises:
            ValueError: If configuration is invalid
        """
        if not isinstance(config_data, dict):
            raise ValueError(f"Configuration {config_name} must be a dictionary")
            
        # Domain-specific validation
        if config_name == "domains":
            self._validate_domains_config(config_data)
        elif config_name == "pii_patterns":
            self._validate_pii_patterns_config(config_data)
        elif config_name == "agent_defaults":
            self._validate_agent_defaults_config(config_data)
            
    def _validate_domains_config(self, config_data: Dict[str, Any]) -> None:
        """Validate domains configuration structure."""
        if "domains" not in config_data:
            raise ValueError("Domains configuration must contain 'domains' key")
            
        domains = config_data["domains"]
        if not isinstance(domains, dict):
            raise ValueError("'domains' must be a dictionary")
            
        for domain_name, domain_config in domains.items():
            if not isinstance(domain_config, dict):
                raise ValueError(f"Domain '{domain_name}' must be a dictionary")
            if "keywords" not in domain_config:
                raise ValueError(f"Domain '{domain_name}' must contain 'keywords'")
            if not isinstance(domain_config["keywords"], list):
                raise ValueError(f"Domain '{domain_name}' keywords must be a list")
            if "weight" not in domain_config:
                raise ValueError(f"Domain '{domain_name}' must contain 'weight'")
                
    def _validate_pii_patterns_config(self, config_data: Dict[str, Any]) -> None:
        """Validate PII patterns configuration structure."""
        if "pii_types" not in config_data:
            raise ValueError("PII patterns configuration must contain 'pii_types' key")
            
        pii_types = config_data["pii_types"]
        if not isinstance(pii_types, dict):
            raise ValueError("'pii_types' must be a dictionary")
            
        for pii_type, pii_config in pii_types.items():
            if not isinstance(pii_config, dict):
                raise ValueError(f"PII type '{pii_type}' must be a dictionary")
            if "patterns" not in pii_config:
                raise ValueError(f"PII type '{pii_type}' must contain 'patterns'")
            if not isinstance(pii_config["patterns"], list):
                raise ValueError(f"PII type '{pii_type}' patterns must be a list")
            
            # Validate that patterns are valid regex strings
            for i, pattern in enumerate(pii_config["patterns"]):
                if not isinstance(pattern, str):
                    raise ValueError(f"PII type '{pii_type}' pattern {i} must be a string")
                try:
                    import re
                    re.compile(pattern)  # Test if regex is valid
                except re.error as e:
                    raise ValueError(f"PII type '{pii_type}' pattern {i} is invalid regex: {e}")
        
        # Validate context configurations if present
        if "context_configs" in config_data:
            context_configs = config_data["context_configs"]
            if not isinstance(context_configs, dict):
                raise ValueError("'context_configs' must be a dictionary")
            
            valid_strategies = ["full_mask", "partial_mask", "tokenize", "hash", "remove"]
            
            for context_name, context_config in context_configs.items():
                if not isinstance(context_config, dict):
                    raise ValueError(f"Context '{context_name}' must be a dictionary")
                
                if "priority_types" in context_config:
                    if not isinstance(context_config["priority_types"], list):
                        raise ValueError(f"Context '{context_name}' priority_types must be a list")
                
                if "default_strategy" in context_config:
                    strategy = context_config["default_strategy"]
                    if strategy not in valid_strategies:
                        raise ValueError(f"Context '{context_name}' default_strategy must be one of: {valid_strategies}")
                
                if "require_full_audit" in context_config:
                    if not isinstance(context_config["require_full_audit"], bool):
                        raise ValueError(f"Context '{context_name}' require_full_audit must be boolean")
                
    def _validate_agent_defaults_config(self, config_data: Dict[str, Any]) -> None:
        """Validate agent defaults configuration structure."""
        if "agent_defaults" not in config_data:
            raise ValueError("Agent defaults configuration must contain 'agent_defaults' key")
            
        agent_defaults = config_data["agent_defaults"]
        if not isinstance(agent_defaults, dict):
            raise ValueError("'agent_defaults' must be a dictionary")
            
        # Validate API settings if present
        if "api_settings" in agent_defaults:
            api_settings = agent_defaults["api_settings"]
            if not isinstance(api_settings, dict):
                raise ValueError("'api_settings' must be a dictionary")
                
            # Validate numeric settings
            numeric_settings = ["timeout_seconds", "max_retries", "total_operation_timeout", 
                              "retry_backoff_base", "retry_backoff_max"]
            for setting in numeric_settings:
                if setting in api_settings:
                    value = api_settings[setting]
                    if not isinstance(value, (int, float)) or value <= 0:
                        raise ValueError(f"API setting '{setting}' must be a positive number")
        
        # Validate caching settings if present        
        if "caching" in agent_defaults:
            caching = agent_defaults["caching"] 
            if not isinstance(caching, dict):
                raise ValueError("'caching' must be a dictionary")
                
            cache_size_settings = ["default_lru_cache_size", "pii_detection_cache_size", 
                                 "file_context_cache_size"]
            for setting in cache_size_settings:
                if setting in caching:
                    value = caching[setting]
                    if not isinstance(value, int) or value <= 0:
                        raise ValueError(f"Cache setting '{setting}' must be a positive integer")
        
        # Validate processing limits if present
        if "processing_limits" in agent_defaults:
            limits = agent_defaults["processing_limits"]
            if not isinstance(limits, dict):
                raise ValueError("'processing_limits' must be a dictionary")
                
            limit_settings = ["max_file_chunks", "min_chunk_lines", "chunking_line_threshold", 
                            "max_context_lines"]
            for setting in limit_settings:
                if setting in limits:
                    value = limits[setting]
                    if not isinstance(value, int) or value <= 0:
                        raise ValueError(f"Processing limit '{setting}' must be a positive integer")
        
    def clear_cache(self) -> None:
        """Clear the configuration cache."""
        self._config_cache.clear()
        self.logger.info("Configuration cache cleared")
        
    def get_config_path(self, config_name: str) -> Path:
        """Get the full path to a configuration file."""
        return self.config_dir / f"{config_name}.yaml"
        
    def config_exists(self, config_name: str) -> bool:
        """Check if a configuration file exists."""
        return self.get_config_path(config_name).exists()


# Global configuration loader instance
_config_loader = None

def get_config_loader() -> ConfigurationLoader:
    """Get the global configuration loader instance."""
    global _config_loader
    if _config_loader is None:
        _config_loader = ConfigurationLoader()
    return _config_loader

def load_config(config_name: str, fallback_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Convenience function to load configuration using the global loader.
    
    Args:
        config_name: Name of configuration file (without extension)
        fallback_data: Fallback data if file loading fails
        
    Returns:
        Configuration dictionary
    """
    return get_config_loader().load_config(config_name, fallback_data)