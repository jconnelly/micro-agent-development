"""
Request Utilities - Common request ID generation and management functions.

Provides standardized request ID generation patterns used across all agents.
"""

import uuid
from typing import Optional


class RequestIdGenerator:
    """Utility class for generating consistent request IDs across agents."""
    
    @staticmethod
    def create_request_id(prefix: str = "req", length: int = 12) -> str:
        """
        Generate a unique request ID with specified prefix and length.
        
        Args:
            prefix: String prefix for the request ID (e.g., "req", "pii", "rule-doc")
            length: Length of the UUID portion (default 12)
            
        Returns:
            Formatted request ID string: "{prefix}-{uuid_hex[:length]}"
            
        Examples:
            >>> RequestIdGenerator.create_request_id()
            'req-a1b2c3d4e5f6'
            >>> RequestIdGenerator.create_request_id("pii", 8)
            'pii-a1b2c3d4'
        """
        return f"{prefix}-{uuid.uuid4().hex[:length]}"
    
    @staticmethod
    def create_pii_token(length: int = 8) -> str:
        """
        Generate a PII tokenization token.
        
        Args:
            length: Length of the UUID portion (default 8)
            
        Returns:
            Formatted PII token: "PII_TOKEN_{UUID_HEX[:length].upper()}"
            
        Example:
            >>> RequestIdGenerator.create_pii_token()
            'PII_TOKEN_A1B2C3D4'
        """
        return f"PII_TOKEN_{uuid.uuid4().hex[:length].upper()}"
    
    @staticmethod
    def create_agent_specific_id(agent_type: str, operation: str = None, length: int = 12) -> str:
        """
        Generate agent-specific request IDs following established patterns.
        
        Args:
            agent_type: Type of agent ("triage", "extraction", "pii", "documentation")
            operation: Optional operation type
            length: Length of UUID portion
            
        Returns:
            Agent-specific request ID
            
        Examples:
            >>> RequestIdGenerator.create_agent_specific_id("triage")
            'triage-a1b2c3d4e5f6'
            >>> RequestIdGenerator.create_agent_specific_id("pii", "detokenize")
            'detok-a1b2c3d4e5f6'
        """
        # Handle specific patterns from existing agents
        if agent_type == "pii" and operation == "detokenize":
            return f"detok-{uuid.uuid4().hex[:length]}"
        elif agent_type == "rule_extraction":
            return f"rule-ext-{uuid.uuid4().hex[:length]}"
        elif agent_type == "rule_documentation":
            return f"rule-doc-{uuid.uuid4().hex[:length]}"
        else:
            return f"{agent_type}-{uuid.uuid4().hex[:length]}"
    
    @staticmethod
    def validate_request_id(request_id: str) -> bool:
        """
        Validate that a string follows the expected request ID format.
        
        Args:
            request_id: String to validate
            
        Returns:
            True if valid format, False otherwise
        """
        if not request_id or not isinstance(request_id, str):
            return False
        
        parts = request_id.split('-', 1)
        if len(parts) != 2:
            return False
        
        prefix, uuid_part = parts
        
        # Basic validation - prefix should be alphanumeric, uuid_part should be hex
        if not prefix.replace('_', '').isalnum():
            return False
            
        try:
            int(uuid_part, 16)  # Try to parse as hex
            return True
        except ValueError:
            return False
    
    @staticmethod 
    def extract_prefix(request_id: str) -> Optional[str]:
        """
        Extract the prefix from a request ID.
        
        Args:
            request_id: Request ID to extract prefix from
            
        Returns:
            Prefix string or None if invalid format
        """
        if not RequestIdGenerator.validate_request_id(request_id):
            return None
        
        return request_id.split('-', 1)[0]