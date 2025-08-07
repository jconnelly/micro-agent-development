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
from typing import Dict, List, Any, Optional, Tuple, Union
from enum import Enum
from datetime import datetime, timezone
import secrets
import string

# Import other Agents from current location, change package location if moved
from .LoggerAgent import AgentLogger
from .AuditingAgent import AgentAuditing


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


class PIIScrubbingAgent:
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
        self.agent_id = agent_id or f"PIIScrubber-{uuid.uuid4().hex[:8]}"
        self.audit_system = audit_system
        self.context = context
        self.version = "1.0.0"
        self.enable_tokenization = enable_tokenization
        
        # Initialize logger
        self.logger = AgentLogger(
            log_level=log_level,
            agent_name="PII Scrubbing Agent"
        )
        
        # Token storage for reversible operations (in production, this would be encrypted/external storage)
        self.token_mapping: Dict[str, str] = {}
        
        # Initialize PII detection patterns
        self._initialize_patterns()
        
        # Initialize context-specific configurations
        self._initialize_context_config()
    
    def _initialize_patterns(self):
        """Initialize regex patterns for different PII types"""
        self.patterns = {
            PIIType.SSN: [
                r'\b\d{3}-\d{2}-\d{4}\b',  # 123-45-6789
                r'\b\d{3}\s\d{2}\s\d{4}\b',  # 123 45 6789
                r'\b\d{9}\b'  # 123456789 (9 consecutive digits)
            ],
            PIIType.CREDIT_CARD: [
                r'\b4\d{3}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b',  # Visa
                r'\b5[1-5]\d{2}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b',  # MasterCard
                r'\b3[47]\d{2}[\s-]?\d{6}[\s-]?\d{5}\b',  # American Express
                r'\b6011[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b'  # Discover
            ],
            PIIType.PHONE_NUMBER: [
                r'\b\(\d{3}\)\s?\d{3}-\d{4}\b',  # (555) 123-4567
                r'\b\d{3}-\d{3}-\d{4}\b',  # 555-123-4567
                r'\b\d{3}\.\d{3}\.\d{4}\b',  # 555.123.4567
                r'\b\d{10}\b'  # 5551234567
            ],
            PIIType.EMAIL: [
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            ],
            PIIType.ACCOUNT_NUMBER: [
                r'\b\d{8,17}\b'  # 8-17 digit account numbers
            ],
            PIIType.DATE_OF_BIRTH: [
                r'\b\d{1,2}/\d{1,2}/\d{4}\b',  # MM/DD/YYYY
                r'\b\d{1,2}-\d{1,2}-\d{4}\b',  # MM-DD-YYYY
                r'\b\d{4}-\d{1,2}-\d{1,2}\b'   # YYYY-MM-DD
            ],
            PIIType.BANK_ROUTING: [
                r'\b\d{9}\b'  # 9-digit routing numbers
            ]
        }
    
    def _initialize_context_config(self):
        """Initialize context-specific PII handling configurations"""
        self.context_configs = {
            PIIContext.FINANCIAL: {
                'priority_types': [PIIType.SSN, PIIType.CREDIT_CARD, PIIType.ACCOUNT_NUMBER, PIIType.BANK_ROUTING],
                'default_strategy': MaskingStrategy.TOKENIZE,
                'require_full_audit': True
            },
            PIIContext.HEALTHCARE: {
                'priority_types': [PIIType.SSN, PIIType.DATE_OF_BIRTH, PIIType.PHONE_NUMBER],
                'default_strategy': MaskingStrategy.HASH,
                'require_full_audit': True
            },
            PIIContext.GENERAL: {
                'priority_types': [PIIType.EMAIL, PIIType.PHONE_NUMBER, PIIType.SSN],
                'default_strategy': MaskingStrategy.PARTIAL_MASK,
                'require_full_audit': False
            }
        }
    
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
            # Convert input to string for processing
            if isinstance(data, dict):
                text_data = json.dumps(data, indent=2)
                is_dict_input = True
            else:
                text_data = str(data)
                is_dict_input = False
            
            # Detect PII
            detection_results = self._detect_pii(text_data)
            pii_detected = detection_results['detected_types']
            pii_matches = detection_results['matches']
            
            self.logger.info(f"Detected {len(pii_detected)} PII types: {[t.value for t in pii_detected]}")
            
            # Apply scrubbing strategy
            strategy = custom_strategy or self.context_configs[self.context]['default_strategy']
            scrubbed_text = self._apply_scrubbing(text_data, pii_matches, strategy)
            
            # Convert back to original format
            if is_dict_input:
                try:
                    scrubbed_data = json.loads(scrubbed_text)
                except json.JSONDecodeError:
                    # If JSON parsing fails, return as string with warning
                    scrubbed_data = scrubbed_text
                    self.logger.error("Failed to parse scrubbed data back to JSON format")
            else:
                scrubbed_data = scrubbed_text
            
            # Create scrubbing summary
            scrubbing_summary = {
                'request_id': request_id,
                'pii_types_detected': [t.value for t in pii_detected],
                'total_pii_instances': sum(len(matches) for matches in pii_matches.values()),
                'masking_strategy': strategy.value,
                'context': self.context.value,
                'processing_duration_ms': (datetime.now(timezone.utc) - operation_start).total_seconds() * 1000,
                'tokenization_enabled': self.enable_tokenization,
                'tokens_generated': len([m for matches in pii_matches.values() for m in matches if strategy == MaskingStrategy.TOKENIZE])
            }
            
            self.logger.info(f"PII scrubbing completed successfully")
            
            # Create comprehensive result
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
            
            # Add to audit trail if required
            if audit_level > 0:
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
                    llm_input=json.dumps({
                        "original_data_length": len(text_data),
                        "pii_types_detected": [t.value for t in pii_detected],
                        "masking_strategy": strategy.value,
                        "context": self.context.value
                    }),
                    llm_output=json.dumps({
                        "scrubbed_data_preview": scrubbed_text[:200] + "..." if len(scrubbed_text) > 200 else scrubbed_text,
                        "pii_instances_processed": sum(len(matches) for matches in pii_matches.values()),
                        "tokens_generated": scrubbing_summary.get('tokens_generated', 0)
                    }),
                    tokens_input=0,
                    tokens_output=0,
                    tool_calls=[],
                    retrieved_chunks=[],
                    final_decision=json.dumps({
                        "scrubbed_data_length": len(str(result['scrubbed_data'])),
                        "pii_types_detected": [t.value for t in result['pii_detected']],
                        "scrubbing_summary": result['scrubbing_summary']
                    }),
                    duration_ms=scrubbing_summary['processing_duration_ms'],
                    audit_level=audit_level
                )
                
                result['audit_log'] = audit_entry
            
            return result
            
        except Exception as e:
            error_msg = f"PII scrubbing failed: {str(e)}"
            self.logger.error(error_msg)
            
            # Log exception to audit trail
            if audit_level > 0:
                self._log_exception_to_audit(request_id, "PII_SCRUBBING", e, audit_level)
            
            raise Exception(error_msg)
    
    def _detect_pii(self, text: str) -> Dict[str, Any]:
        """
        Detect PII in the given text using regex patterns.
        
        Args:
            text: Text to scan for PII
            
        Returns:
            Dictionary with detected types and matches
        """
        detected_types = []
        matches = {}
        
        priority_types = self.context_configs[self.context]['priority_types']
        
        # Check priority types first, then others
        all_types = priority_types + [t for t in PIIType if t not in priority_types]
        
        for pii_type in all_types:
            type_matches = []
            
            for pattern in self.patterns.get(pii_type, []):
                found_matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in found_matches:
                    type_matches.append({
                        'value': match.group(),
                        'start': match.start(),
                        'end': match.end(),
                        'pattern': pattern
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
            raise ValueError("Tokenization not enabled for this PII scrubbing agent")
        
        request_id = request_id or f"detok-{uuid.uuid4().hex[:12]}"
        self.logger.request_id = request_id
        
        self.logger.info(f"Starting detokenization for request: {request_id}")
        
        # Convert to string for processing
        if isinstance(data, dict):
            text_data = json.dumps(data, indent=2)
            is_dict_input = True
        else:
            text_data = str(data)
            is_dict_input = False
        
        # Find and replace tokens
        restored_text = text_data
        tokens_found = []
        
        for token, original_value in self.token_mapping.items():
            if token in restored_text:
                restored_text = restored_text.replace(token, original_value)
                tokens_found.append(token)
        
        # Convert back to original format
        if is_dict_input:
            try:
                restored_data = json.loads(restored_text)
            except json.JSONDecodeError:
                restored_data = restored_text
        else:
            restored_data = restored_text
        
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
    
    def _log_exception_to_audit(self, request_id: str, operation: str, exception: Exception, audit_level: int):
        """Log exceptions to audit trail with context"""
        
        error_entry = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'request_id': request_id,
            'agent_id': self.agent_id,
            'operation': operation,
            'error_type': type(exception).__name__,
            'error_message': str(exception),
            'context': self.context.value,
            'audit_level': audit_level
        }
        
        self.audit_system.log_agent_activity(
            request_id=request_id,
            user_id="system",
            session_id="pii_error",
            ip_address="internal",
            agent_id=self.agent_id,
            agent_name="PII Scrubbing Agent",
            agent_version=self.version,
            step_type="PII_ERROR",
            llm_model_name="n/a",
            llm_provider="n/a",
            llm_input="PII operation failed",
            llm_output=json.dumps(error_entry),
            tokens_input=0,
            tokens_output=0,
            tool_calls=[],
            retrieved_chunks=[],
            final_decision=json.dumps({'error': str(exception)}),
            duration_ms=0,
            error_details=error_entry,
            audit_level=audit_level
        )