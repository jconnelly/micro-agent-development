#!/usr/bin/env python3

"""
Configuration Management System

Centralized configuration management for all agents with consistent fallback
handling and caching. Eliminates configuration loading pattern duplication.

This module was extracted from StandardImports.py as part of Phase 14
code quality improvements to break down large class files.
"""

import re
from typing import Any, Dict

from .import_utils import ImportUtils


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