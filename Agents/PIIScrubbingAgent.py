#!/usr/bin/env python3

"""
PIIScrubbingAgent.py

A reusable production-ready agent for detecting and scrubbing Personally Identifiable Information (PII)
from data before it's sent to LLMs or stored in logs. This agent can be used by any other agent
that needs PII protection.

Key Features:
- Multiple PII detection patterns (SSN, credit cards, phone numbers, emails, addresses)
- Configurable masking strategies (full mask, partial mask, tokenization, hashing)
- Context-aware scrubbing for different domains (financial, healthcare, general)
- Comprehensive audit trail for compliance
- Reversible tokenization for authorized access
- Production logging with silent/verbose modes

Author: AI Development Team
Version: 1.0.0
"""

import re
import hashlib
import json
import uuid
from typing import Dict, List, Any, Optional, Tuple, Union, Pattern
from enum import Enum
from datetime import datetime, timezone
import secrets
import string
from functools import lru_cache

# Import other Agents from current location, change package location if moved
from .BaseAgent import BaseAgent
from .AuditingAgent import AgentAuditing
from .Exceptions import PIIProcessingError, ConfigurationError, ValidationError

# Import Utils - handle both relative and absolute imports
try:
    from ..Utils import JsonUtils, TextProcessingUtils, config_loader
except ImportError:
    import sys
    import os
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    from Utils import JsonUtils, TextProcessingUtils, config_loader


class PIIType(Enum):
    """Enumeration of supported PII types"""
    SSN = "ssn"
    CREDIT_CARD = "credit_card"
    PHONE_NUMBER = "phone_number"
    EMAIL = "email"
    ADDRESS = "address"
    ACCOUNT_NUMBER = "account_number"
    DATE_OF_BIRTH = "date_of_birth"
    DRIVER_LICENSE = "driver_license"
    PASSPORT = "passport"
    BANK_ROUTING = "bank_routing"


class MaskingStrategy(Enum):
    """Enumeration of masking strategies"""
    FULL_MASK = "full_mask"          # Replace entire value with ***
    PARTIAL_MASK = "partial_mask"    # Show first/last chars, mask middle
    TOKENIZE = "tokenize"            # Replace with reversible token
    HASH = "hash"                    # One-way hash (irreversible)
    REMOVE = "remove"                # Remove entirely from text


class PIIContext(Enum):
    """Different contexts requiring different PII handling"""
    FINANCIAL = "financial"
    HEALTHCARE = "healthcare" 
    GENERAL = "general"
    LEGAL = "legal"
    GOVERNMENT = "government"


class PIIScrubbingAgent(BaseAgent):
    """
    Production-ready agent for PII detection and scrubbing with comprehensive audit trail.
    
    This agent can be used by any other agent that processes potentially sensitive data.
    """
    
    def __init__(
        self, 
        audit_system: AgentAuditing,
        context: PIIContext = PIIContext.GENERAL,
        agent_id: str = None,
        log_level: int = 0,
        enable_tokenization: bool = False
    ):
        """
        Initialize the PII Scrubbing Agent.
        
        Args:
            audit_system: AgentAuditing instance for compliance logging
            context: PIIContext enum for domain-specific handling
            agent_id: Unique identifier for this agent instance
            log_level: 0 for production (silent), 1 for development (verbose)
            enable_tokenization: Whether to support reversible tokenization
        """
        # Initialize base agent
        super().__init__(
            audit_system=audit_system,
            agent_id=agent_id,
            log_level=log_level,
            model_name="pii-scrubber",
            llm_provider="internal",
            agent_name="PII Scrubbing Agent"
        )
        
        # PII-specific configuration
        self.context = context
        self.enable_tokenization = enable_tokenization
        
        # Token storage for reversible operations (in production, this would be encrypted/external storage)
        self.token_mapping: Dict[str, str] = {}
        
        # Initialize PII detection patterns
        self._initialize_patterns()
        
        # Initialize context-specific configurations
        self._initialize_context_config()
    
    def _initialize_patterns(self) -> None:
        """Initialize and pre-compile regex patterns for different PII types for optimal performance"""
        # Fallback pattern definitions (preserved from original hardcoded values)
        fallback_patterns = {
            'pii_types': {
                'ssn': {
                    'patterns': [
                        r'\b\d{3}-\d{2}-\d{4}\b',  # 123-45-6789
                        r'\b\d{3}\s\d{2}\s\d{4}\b',  # 123 45 6789
                        r'\b\d{9}\b'  # 123456789 (9 consecutive digits)
                    ]
                },
                'credit_card': {
                    'patterns': [
                        r'\b4\d{3}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b',  # Visa
                        r'\b5[1-5]\d{2}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b',  # MasterCard
                        r'\b3[47]\d{2}[\s-]?\d{6}[\s-]?\d{5}\b',  # American Express
                        r'\b6011[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b'  # Discover
                    ]
                },
                'phone_number': {
                    'patterns': [
                        r'(?<!\d)\(\d{3}\)\s?\d{3}-\d{4}(?!\d)',  # (555) 123-4567
                        r'\b\d{3}-\d{3}-\d{4}\b',  # 555-123-4567
                        r'\b\d{3}\.\d{3}\.\d{4}\b',  # 555.123.4567
                        r'\b\d{10}\b'  # 5551234567
                    ]
                },
                'email': {
                    'patterns': [
                        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                    ]
                },
                'account_number': {
                    'patterns': [
                        r'\b\d{8,17}\b'  # 8-17 digit account numbers
                    ]
                },
                'date_of_birth': {
                    'patterns': [
                        r'\b\d{1,2}/\d{1,2}/\d{4}\b',  # MM/DD/YYYY
                        r'\b\d{1,2}-\d{1,2}-\d{4}\b',  # MM-DD-YYYY
                        r'\b\d{4}-\d{1,2}-\d{1,2}\b'   # YYYY-MM-DD
                    ]
                },
                'bank_routing': {
                    'patterns': [
                        r'\b\d{9}\b'  # 9-digit routing numbers
                    ]
                }
            }
        }
        
        # Load configuration with graceful fallback
        try:
            pii_config = config_loader.load_config("pii_patterns", fallback_patterns)
            pii_types_config = pii_config.get('pii_types', fallback_patterns['pii_types'])
            self.logger.debug("Loaded PII patterns configuration from external file")
        except Exception as e:
            self.logger.warning(f"Failed to load PII patterns configuration: {e}. Using fallback.")
            pii_types_config = fallback_patterns['pii_types']
        
        # Convert configuration to enum-based structure for backward compatibility
        raw_patterns = {}
        
        # Map configuration keys to PIIType enums
        pii_type_mapping = {
            'ssn': PIIType.SSN,
            'credit_card': PIIType.CREDIT_CARD,
            'phone_number': PIIType.PHONE_NUMBER,
            'email': PIIType.EMAIL,
            'account_number': PIIType.ACCOUNT_NUMBER,
            'date_of_birth': PIIType.DATE_OF_BIRTH,
            'bank_routing': PIIType.BANK_ROUTING,
            'driver_license': PIIType.DRIVER_LICENSE,
            'passport': PIIType.PASSPORT
        }
        
        # Convert external configuration to internal format
        for config_key, pii_type in pii_type_mapping.items():
            if config_key in pii_types_config:
                patterns = pii_types_config[config_key]['patterns']
                # Clean up patterns - remove r' prefix and ' suffix if present
                cleaned_patterns = []
                for pattern in patterns:
                    if isinstance(pattern, str):
                        # Remove r' prefix and ' suffix if present (YAML artifact)
                        if pattern.startswith("r'") and pattern.endswith("'"):
                            cleaned_pattern = pattern[2:-1]  # Remove r' and '
                        elif pattern.startswith('r"') and pattern.endswith('"'):
                            cleaned_pattern = pattern[2:-1]  # Remove r" and "
                        else:
                            cleaned_pattern = pattern
                        cleaned_patterns.append(cleaned_pattern)
                raw_patterns[pii_type] = cleaned_patterns
        
        # Pre-compile all patterns for significant performance improvement
        self.compiled_patterns: Dict[PIIType, List[Tuple[Pattern[str], str]]] = {}
        self.patterns = {}  # Keep raw patterns for backward compatibility
        
        for pii_type, pattern_list in raw_patterns.items():
            compiled_list = []
            raw_list = []
            
            for pattern_str in pattern_list:
                try:
                    # Pre-compile with IGNORECASE flag for performance
                    compiled_pattern = re.compile(pattern_str, re.IGNORECASE)
                    compiled_list.append((compiled_pattern, pattern_str))
                    raw_list.append(pattern_str)
                except re.error as e:
                    # Log invalid patterns but continue
                    self.logger.warning(f"Invalid regex pattern for {pii_type.value}: {pattern_str} - {e}")
                    continue
            
            self.compiled_patterns[pii_type] = compiled_list
            self.patterns[pii_type] = raw_list
        
        # Log compilation statistics
        total_patterns = sum(len(patterns) for patterns in self.compiled_patterns.values())
        self.logger.info(f"Pre-compiled {total_patterns} PII regex patterns for optimal performance")
    
    def _initialize_context_config(self) -> None:
        """Initialize context-specific PII handling configurations using external config with fallback"""
        # Fallback context configurations (preserved from original hardcoded values)
        fallback_context_configs = {
            'context_configs': {
                'financial': {
                    'priority_types': ['ssn', 'credit_card', 'account_number', 'bank_routing'],
                    'default_strategy': 'tokenize',
                    'require_full_audit': True
                },
                'healthcare': {
                    'priority_types': ['ssn', 'date_of_birth', 'phone_number'],
                    'default_strategy': 'hash',
                    'require_full_audit': True
                },
                'general': {
                    'priority_types': ['email', 'phone_number', 'ssn'],
                    'default_strategy': 'partial_mask',
                    'require_full_audit': False
                }
            }
        }
        
        # Load configuration with graceful fallback
        try:
            pii_config = config_loader.load_config("pii_patterns", fallback_context_configs)
            context_configs_raw = pii_config.get('context_configs', fallback_context_configs['context_configs'])
        except Exception as e:
            self.logger.warning(f"Failed to load context configurations: {e}. Using fallback.")
            context_configs_raw = fallback_context_configs['context_configs']
        
        # Convert external configuration to internal format
        self.context_configs = {}
        
        # Map configuration keys to enum types
        context_mapping = {
            'financial': PIIContext.FINANCIAL,
            'healthcare': PIIContext.HEALTHCARE,
            'general': PIIContext.GENERAL,
            'legal': PIIContext.LEGAL,
            'government': PIIContext.GOVERNMENT
        }
        
        pii_type_mapping = {
            'ssn': PIIType.SSN,
            'credit_card': PIIType.CREDIT_CARD,
            'phone_number': PIIType.PHONE_NUMBER,
            'email': PIIType.EMAIL,
            'account_number': PIIType.ACCOUNT_NUMBER,
            'date_of_birth': PIIType.DATE_OF_BIRTH,
            'bank_routing': PIIType.BANK_ROUTING,
            'driver_license': PIIType.DRIVER_LICENSE,
            'passport': PIIType.PASSPORT
        }
        
        strategy_mapping = {
            'full_mask': MaskingStrategy.FULL_MASK,
            'partial_mask': MaskingStrategy.PARTIAL_MASK,
            'tokenize': MaskingStrategy.TOKENIZE,
            'hash': MaskingStrategy.HASH,
            'remove': MaskingStrategy.REMOVE
        }
        
        # Convert configurations
        for config_key, context_enum in context_mapping.items():
            if config_key in context_configs_raw:
                config = context_configs_raw[config_key]
                
                # Convert priority types from strings to enums
                priority_types = []
                for pii_type_str in config.get('priority_types', []):
                    if pii_type_str in pii_type_mapping:
                        priority_types.append(pii_type_mapping[pii_type_str])
                
                # Convert strategy from string to enum
                strategy_str = config.get('default_strategy', 'partial_mask')
                strategy = strategy_mapping.get(strategy_str, MaskingStrategy.PARTIAL_MASK)
                
                self.context_configs[context_enum] = {
                    'priority_types': priority_types,
                    'default_strategy': strategy,
                    'require_full_audit': config.get('require_full_audit', False)
                }
    
    def _prepare_input_data(self, data: Union[str, Dict[str, Any]]) -> tuple[str, bool]:
        """
        Prepare input data for PII processing.
        
        Args:
            data: Input data to prepare
            
        Returns:
            Tuple of (text_data, is_dict_input)
        """
        return TextProcessingUtils.prepare_input_data(data)
    
    def _perform_pii_detection(self, text_data: str, request_id: str) -> tuple[List[PIIType], Dict[PIIType, List]]:
        """
        Detect PII in text data and log results.
        
        Args:
            text_data: Text to scan for PII
            request_id: Request identifier for logging
            
        Returns:
            Tuple of (pii_detected, pii_matches)
        """
        detection_results = self._detect_pii(text_data)
        pii_detected = detection_results['detected_types']
        pii_matches = detection_results['matches']
        
        self.logger.info(f"Detected {len(pii_detected)} PII types: {[t.value for t in pii_detected]}")
        
        return pii_detected, pii_matches
    
    def _apply_scrubbing_strategy(self, text_data: str, pii_matches: Dict[PIIType, List], custom_strategy: MaskingStrategy = None) -> tuple[str, MaskingStrategy]:
        """
        Apply the appropriate scrubbing strategy to the text data.
        
        Args:
            text_data: Original text data
            pii_matches: Detected PII matches
            custom_strategy: Override default strategy
            
        Returns:
            Tuple of (scrubbed_text, strategy_used)
        """
        strategy = custom_strategy or self.context_configs[self.context]['default_strategy']
        scrubbed_text = self._apply_scrubbing(text_data, pii_matches, strategy)
        
        return scrubbed_text, strategy
    
    def _prepare_result_data(self, scrubbed_text: str, is_dict_input: bool) -> Union[str, Dict[str, Any]]:
        """
        Convert scrubbed text back to original format.
        
        Args:
            scrubbed_text: The scrubbed text
            is_dict_input: Whether original input was a dictionary
            
        Returns:
            Scrubbed data in appropriate format
        """
        try:
            return TextProcessingUtils.restore_data_format(scrubbed_text, is_dict_input, fallback_to_string=True)
        except ValueError:
            # If restoration fails, log and return as string
            self.logger.error("Failed to parse scrubbed data back to JSON format")
            return scrubbed_text
    
    def _create_scrubbing_summary(self, request_id: str, pii_detected: List[PIIType], pii_matches: Dict[PIIType, List], 
                                  strategy: MaskingStrategy, operation_start: datetime) -> Dict[str, Any]:
        """
        Create a comprehensive summary of the scrubbing operation.
        
        Returns:
            Dictionary containing scrubbing operation summary
        """
        return {
            'request_id': request_id,
            'pii_types_detected': [t.value for t in pii_detected],
            'total_pii_instances': sum(len(matches) for matches in pii_matches.values()),
            'masking_strategy': strategy.value,
            'context': self.context.value,
            'processing_duration_ms': (datetime.now(timezone.utc) - operation_start).total_seconds() * 1000,
            'tokenization_enabled': self.enable_tokenization,
            'tokens_generated': len([m for matches in pii_matches.values() for m in matches if strategy == MaskingStrategy.TOKENIZE])
        }
    
    def _create_pii_audit_entry(self, request_id: str, text_data: str, pii_detected: List[PIIType], 
                                pii_matches: Dict[PIIType, List], scrubbed_text: str, strategy: MaskingStrategy, 
                                scrubbing_summary: Dict[str, Any], result: Dict[str, Any], audit_level: int) -> None:
        """
        Create and log audit entry for PII scrubbing operation.
        """
        audit_entry = self._create_audit_entry(
            request_id=request_id,
            operation="PII_SCRUBBING",
            pii_detected=pii_detected,
            strategy=strategy,
            summary=scrubbing_summary,
            audit_level=audit_level
        )
        
        self.audit_system.log_agent_activity(
            request_id=request_id,
            user_id="system",
            session_id="pii_scrubbing",
            ip_address="internal",
            agent_id=self.agent_id,
            agent_name="PII Scrubbing Agent",
            agent_version=self.version,
            step_type="PII_SCRUBBING",
            llm_model_name="n/a",
            llm_provider="n/a",
            llm_input=JsonUtils.safe_dumps({
                "original_data_length": len(text_data),
                "pii_types_detected": [t.value for t in pii_detected],
                "masking_strategy": strategy.value,
                "context": self.context.value
            }),
            llm_output=JsonUtils.safe_dumps({
                "scrubbed_data_preview": scrubbed_text[:200] + "..." if len(scrubbed_text) > 200 else scrubbed_text,
                "pii_instances_processed": sum(len(matches) for matches in pii_matches.values()),
                "tokens_generated": scrubbing_summary.get('tokens_generated', 0)
            }),
            tokens_input=0,
            tokens_output=0,
            tool_calls=[],
            retrieved_chunks=[],
            final_decision=JsonUtils.safe_dumps({
                "scrubbed_data_length": len(str(result['scrubbed_data'])),
                "pii_types_detected": [t.value for t in result['pii_detected']],
                "scrubbing_summary": result['scrubbing_summary']
            }),
            duration_ms=scrubbing_summary['processing_duration_ms'],
            audit_level=audit_level
        )
        
        result['audit_log'] = audit_entry

    def scrub_data(
        self, 
        data: Union[str, Dict[str, Any]], 
        request_id: str = None,
        custom_strategy: MaskingStrategy = None,
        audit_level: int = 1
    ) -> Dict[str, Any]:
        """
        Main method to scrub PII from input data.
        
        Args:
            data: String or dictionary containing potentially sensitive data
            request_id: Unique request identifier for audit trail
            custom_strategy: Override default masking strategy
            audit_level: Audit detail level (0=none, 1=basic, 2=detailed, 3=full)
            
        Returns:
            Dictionary containing:
            - scrubbed_data: The cleaned data
            - pii_detected: List of detected PII types
            - scrubbing_summary: Summary of operations performed
            - audit_log: Audit trail entry
        """
        operation_start = datetime.now(timezone.utc)
        request_id = request_id or f"pii-{uuid.uuid4().hex[:12]}"
        
        # Set request ID for logger
        self.logger.request_id = request_id
        self.logger.info(f"Starting PII scrubbing operation for request: {request_id}")
        
        try:
            # 1. Prepare input data
            text_data, is_dict_input = self._prepare_input_data(data)
            
            # 2. Perform PII detection
            pii_detected, pii_matches = self._perform_pii_detection(text_data, request_id)
            
            # 3. Apply scrubbing strategy
            scrubbed_text, strategy = self._apply_scrubbing_strategy(text_data, pii_matches, custom_strategy)
            
            # 4. Prepare result data
            scrubbed_data = self._prepare_result_data(scrubbed_text, is_dict_input)
            
            # 5. Create scrubbing summary
            scrubbing_summary = self._create_scrubbing_summary(request_id, pii_detected, pii_matches, strategy, operation_start)
            
            self.logger.info(f"PII scrubbing completed successfully")
            
            # 6. Create comprehensive result
            result = {
                'scrubbed_data': scrubbed_data,
                'pii_detected': pii_detected,
                'scrubbing_summary': scrubbing_summary,
                'logger_session_summary': self.logger.create_audit_summary(
                    operation_name="pii_scrubbing",
                    request_id=request_id,
                    status="SUCCESS",
                    metadata=scrubbing_summary
                )
            }
            
            # 7. Add to audit trail if required
            if audit_level > 0:
                self._create_pii_audit_entry(request_id, text_data, pii_detected, pii_matches, 
                                           scrubbed_text, strategy, scrubbing_summary, result, audit_level)
            
            return result
            
        except Exception as e:
            error_msg = f"PII scrubbing failed: {str(e)}"
            self.logger.error(error_msg)
            
            # Log exception to audit trail
            if audit_level > 0:
                self._log_exception_to_audit(request_id, e, "PII_SCRUBBING", {
                    "context": self.context.value,
                    "audit_level": audit_level,
                    "enable_tokenization": self.enable_tokenization
                }, "pii_scrubbing")
            
            raise PIIProcessingError(
                error_msg.replace("PII scrubbing failed: ", ""),
                context={"audit_level": audit_level},
                request_id=request_id
            )
    
    def _detect_pii(self, text: str) -> Dict[str, Any]:
        """
        Detect PII in the given text using regex patterns with caching for performance.
        
        Args:
            text: Text to scan for PII
            
        Returns:
            Dictionary with detected types and matches
        """
        # Use cached detection for improved performance on repeated text
        cache_key = (text, self.context.value)  # Include context in cache key
        return self._cached_detect_pii(cache_key, text)
    
    @lru_cache(maxsize=256)  # Cache up to 256 unique text/context combinations
    def _cached_detect_pii(self, cache_key: Tuple[str, str], text: str) -> Dict[str, Any]:
        """
        Cached PII detection implementation for performance optimization.
        
        Args:
            cache_key: Tuple of (text, context) for cache discrimination
            text: Text to scan for PII
            
        Returns:
            Dictionary with detected types and matches
        """
        detected_types = []
        matches = {}
        
        priority_types = self.context_configs[self.context]['priority_types']
        
        # Check priority types first, then others - use set for O(1) lookup instead of O(n) list search
        priority_set = set(priority_types)
        remaining_types = [t for t in PIIType if t not in priority_set]
        all_types = priority_types + remaining_types
        
        for pii_type in all_types:
            type_matches = []
            
            # Use pre-compiled patterns for significant performance improvement
            for compiled_pattern, original_pattern in self.compiled_patterns.get(pii_type, []):
                found_matches = compiled_pattern.finditer(text)
                for match in found_matches:
                    type_matches.append({
                        'value': match.group(),
                        'start': match.start(),
                        'end': match.end(),
                        'pattern': original_pattern  # Keep original pattern string for compatibility
                    })
            
            if type_matches:
                detected_types.append(pii_type)
                matches[pii_type] = type_matches
        
        return {
            'detected_types': detected_types,
            'matches': matches
        }
    
    def _apply_scrubbing(
        self, 
        text: str, 
        pii_matches: Dict[PIIType, List[Dict]], 
        strategy: MaskingStrategy
    ) -> str:
        """
        Apply the specified masking strategy to detected PII.
        
        Args:
            text: Original text
            pii_matches: Detected PII matches by type
            strategy: Masking strategy to apply
            
        Returns:
            Scrubbed text
        """
        scrubbed_text = text
        offset = 0  # Track offset changes due to replacements
        
        # Sort all matches by position for proper replacement
        all_matches = []
        for pii_type, matches in pii_matches.items():
            for match in matches:
                all_matches.append({
                    'type': pii_type,
                    'value': match['value'],
                    'start': match['start'],
                    'end': match['end']
                })
        
        # Sort by start position
        all_matches.sort(key=lambda x: x['start'])
        
        # Apply masking strategy
        for match in all_matches:
            original_value = match['value']
            masked_value = self._mask_value(original_value, match['type'], strategy)
            
            # Calculate positions accounting for offset
            start_pos = match['start'] + offset
            end_pos = match['end'] + offset
            
            # Replace in text
            scrubbed_text = scrubbed_text[:start_pos] + masked_value + scrubbed_text[end_pos:]
            
            # Update offset
            offset += len(masked_value) - len(original_value)
        
        return scrubbed_text
    
    def _mask_value(self, value: str, pii_type: PIIType, strategy: MaskingStrategy) -> str:
        """
        Apply masking strategy to a specific PII value.
        
        Args:
            value: The PII value to mask
            pii_type: Type of PII
            strategy: Masking strategy
            
        Returns:
            Masked value
        """
        if strategy == MaskingStrategy.FULL_MASK:
            return "*" * len(value)
        
        elif strategy == MaskingStrategy.PARTIAL_MASK:
            if len(value) <= 4:
                return "*" * len(value)
            elif pii_type == PIIType.CREDIT_CARD:
                # Show last 4 digits for credit cards
                return "*" * (len(value) - 4) + value[-4:]
            elif pii_type == PIIType.SSN:
                # Show last 4 digits for SSN
                return "*" * (len(value) - 4) + value[-4:]
            else:
                # Show first and last 2 characters
                return value[:2] + "*" * (len(value) - 4) + value[-2:]
        
        elif strategy == MaskingStrategy.TOKENIZE:
            if self.enable_tokenization:
                token = f"PII_TOKEN_{uuid.uuid4().hex[:8].upper()}"
                self.token_mapping[token] = value
                return token
            else:
                return self._mask_value(value, pii_type, MaskingStrategy.FULL_MASK)
        
        elif strategy == MaskingStrategy.HASH:
            hash_value = hashlib.sha256(value.encode()).hexdigest()[:16]
            return f"HASH_{hash_value}"
        
        elif strategy == MaskingStrategy.REMOVE:
            return ""
        
        else:
            return "*" * len(value)
    
    def detokenize_data(self, data: Union[str, Dict[str, Any]], request_id: str = None) -> Dict[str, Any]:
        """
        Reverse tokenization to restore original PII values (for authorized access).
        
        Args:
            data: Tokenized data
            request_id: Request identifier for audit
            
        Returns:
            Dictionary with restored data and audit information
        """
        if not self.enable_tokenization:
            raise ValidationError(
                "Tokenization not enabled for this PII scrubbing agent",
                context={"operation": "detokenization", "tokenization_enabled": False},
                request_id=request_id
            )
        
        request_id = request_id or f"detok-{uuid.uuid4().hex[:12]}"
        self.logger.request_id = request_id
        
        self.logger.info(f"Starting detokenization for request: {request_id}")
        
        # Convert to string for processing
        text_data, is_dict_input = TextProcessingUtils.prepare_input_data(data)
        
        # Find and replace tokens
        restored_text = text_data
        tokens_found = []
        
        for token, original_value in self.token_mapping.items():
            if token in restored_text:
                restored_text = restored_text.replace(token, original_value)
                tokens_found.append(token)
        
        # Convert back to original format
        restored_data = TextProcessingUtils.restore_data_format(restored_text, is_dict_input)
        
        self.logger.info(f"Detokenization completed. Restored {len(tokens_found)} tokens")
        
        return {
            'restored_data': restored_data,
            'tokens_restored': len(tokens_found),
            'logger_session_summary': self.logger.create_audit_summary(
                operation_name="pii_detokenization",
                request_id=request_id,
                status="SUCCESS",
                metadata={'tokens_restored': len(tokens_found)}
            )
        }
    
    def _create_audit_entry(
        self,
        request_id: str,
        operation: str,
        pii_detected: List[PIIType],
        strategy: MaskingStrategy,
        summary: Dict[str, Any],
        audit_level: int
    ) -> Dict[str, Any]:
        """Create detailed audit entry for PII operations"""
        
        audit_entry = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'request_id': request_id,
            'agent_id': self.agent_id,
            'agent_version': self.version,
            'operation': operation,
            'context': self.context.value,
            'pii_types_detected': [t.value for t in pii_detected],
            'masking_strategy': strategy.value,
            'audit_level': audit_level
        }
        
        if audit_level >= 2:
            audit_entry.update({
                'processing_summary': summary,
                'tokenization_enabled': self.enable_tokenization
            })
        
        if audit_level >= 3:
            audit_entry.update({
                'session_logs': self.logger.session_logs,
                'detailed_metrics': {
                    'total_characters_processed': summary.get('total_pii_instances', 0),
                    'processing_duration_ms': summary.get('processing_duration_ms', 0)
                }
            })
        
        return audit_entry
    
    # _log_exception_to_audit() method now inherited from BaseAgent
    
    def get_agent_info(self) -> Dict[str, Any]:
        """
        Get agent information including capabilities and configuration.
        
        Returns:
            Dictionary containing agent information
        """
        return {
            "agent_name": self.agent_name,
            "agent_id": self.agent_id,
            "version": self.version,
            "model_name": self.model_name,
            "llm_provider": self.llm_provider,
            "capabilities": [
                "pii_detection",
                "data_masking",
                "tokenization",
                "audit_compliance",
                "reversible_scrubbing"
            ],
            "supported_pii_types": [pii_type.value for pii_type in PIIType],
            "supported_contexts": [context.value for context in PIIContext],
            "masking_strategies": [strategy.value for strategy in MaskingStrategy],
            "configuration": {
                "context": self.context.value,
                "tokenization_enabled": self.enable_tokenization,
                "patterns_count": len(self.patterns) if hasattr(self, 'patterns') else 0,
                "compiled_patterns_count": sum(len(patterns) for patterns in self.compiled_patterns.values()) if hasattr(self, 'compiled_patterns') else 0,
                "performance_optimized": True
            }
        }