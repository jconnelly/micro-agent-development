#!/usr/bin/env python3

"""
PII Security Components

Secure token storage and encryption utilities for PII tokenization with
encryption and expiry management. Replaces insecure in-memory dictionary storage.

This module was extracted from PersonalDataProtectionAgent.py as part of Phase 14
code quality improvements to break down large class files.
"""

import base64
import datetime
import hashlib
import secrets
from datetime import timezone
from typing import Any, Dict, Optional


class SecureTokenStorage:
    """
    Secure token storage for PII tokenization with encryption and expiry.
    Replaces insecure in-memory dictionary storage.
    """
    
    def __init__(self, storage_key: Optional[str] = None):
        """
        Initialize secure token storage with encryption.
        
        Args:
            storage_key: Base64-encoded encryption key. If None, generates a new key.
        """
        if storage_key:
            self.key = storage_key.encode('utf-8')
        else:
            # In production, this key should come from secure key management (e.g., AWS KMS, HashiCorp Vault)
            self.key = base64.urlsafe_b64encode(secrets.token_bytes(32))
        
        # Initialize encryption with the key
        try:
            # Use a simple XOR-based encryption for now (production should use proper crypto library)
            self._encryption_key = hashlib.sha256(self.key).digest()
        except Exception:
            # Fallback to basic key derivation
            self._encryption_key = hashlib.md5(self.key).digest()
        
        # In-memory storage with expiry (production should use Redis/database)
        self._token_store: Dict[str, Dict[str, Any]] = {}
        self._reverse_mapping: Dict[str, str] = {}
    
    def _encrypt_value(self, value: str) -> str:
        """Encrypt a value using simple XOR encryption."""
        # Convert value to bytes
        value_bytes = value.encode('utf-8')
        
        # Simple XOR encryption (production should use AES/Fernet)
        encrypted = bytearray()
        key_len = len(self._encryption_key)
        
        for i, byte in enumerate(value_bytes):
            encrypted.append(byte ^ self._encryption_key[i % key_len])
        
        # Return base64 encoded result
        return base64.b64encode(bytes(encrypted)).decode('utf-8')
    
    def _decrypt_value(self, encrypted_value: str) -> str:
        """Decrypt a value using simple XOR decryption."""
        try:
            # Decode from base64
            encrypted_bytes = base64.b64decode(encrypted_value.encode('utf-8'))
            
            # Simple XOR decryption
            decrypted = bytearray()
            key_len = len(self._encryption_key)
            
            for i, byte in enumerate(encrypted_bytes):
                decrypted.append(byte ^ self._encryption_key[i % key_len])
            
            return bytes(decrypted).decode('utf-8')
        except Exception:
            # If decryption fails, return empty string for security
            return ""
    
    def store_token(self, token: str, original_value: str, ttl_hours: int = 24) -> bool:
        """
        Store a token mapping securely with expiry.
        
        Args:
            token: The token to store
            original_value: The original PII value to encrypt
            ttl_hours: Time to live in hours
            
        Returns:
            True if stored successfully
        """
        try:
            # Encrypt the original value
            encrypted_value = self._encrypt_value(original_value)
            
            # Calculate expiry time
            expiry_time = datetime.datetime.now(timezone.utc) + datetime.timedelta(hours=ttl_hours)
            
            # Store encrypted mapping
            self._token_store[token] = {
                'encrypted_value': encrypted_value,
                'expires_at': expiry_time,
                'created_at': datetime.datetime.now(timezone.utc)
            }
            
            # Store reverse mapping for quick lookup using hashed key (security fix)
            value_hash = hashlib.sha256(original_value.encode('utf-8')).hexdigest()
            self._reverse_mapping[value_hash] = token
            
            return True
        except Exception:
            return False
    
    def retrieve_original(self, token: str) -> Optional[str]:
        """
        Retrieve and decrypt the original value for a token.
        
        Args:
            token: The token to look up
            
        Returns:
            Decrypted original value or None if not found/expired
        """
        if token not in self._token_store:
            return None
        
        token_data = self._token_store[token]
        
        # Check if token has expired
        if datetime.datetime.now(timezone.utc) > token_data['expires_at']:
            # Remove expired token
            self._cleanup_token(token)
            return None
        
        # Decrypt and return the value
        return self._decrypt_value(token_data['encrypted_value'])
    
    def get_token_for_value(self, original_value: str) -> Optional[str]:
        """Get existing token for a value if it exists and hasn't expired."""
        # Use hashed key for secure lookup (security fix)
        value_hash = hashlib.sha256(original_value.encode('utf-8')).hexdigest()
        token = self._reverse_mapping.get(value_hash)
        if token and token in self._token_store:
            # Check if still valid
            if datetime.datetime.now(timezone.utc) <= self._token_store[token]['expires_at']:
                return token
            else:
                # Clean up expired token
                self._cleanup_token(token)
        return None
    
    def _cleanup_token(self, token: str) -> None:
        """Remove token and its reverse mapping."""
        if token in self._token_store:
            # Find and remove reverse mapping
            token_data = self._token_store[token]
            original_value = self._decrypt_value(token_data['encrypted_value'])
            # Use hashed key for secure cleanup (security fix) 
            value_hash = hashlib.sha256(original_value.encode('utf-8')).hexdigest()
            if value_hash in self._reverse_mapping:
                del self._reverse_mapping[value_hash]
            
            # Remove token
            del self._token_store[token]
    
    def cleanup_expired_tokens(self) -> int:
        """Clean up all expired tokens. Returns count of removed tokens."""
        current_time = datetime.datetime.now(timezone.utc)
        expired_tokens = [
            token for token, data in self._token_store.items()
            if current_time > data['expires_at']
        ]
        
        for token in expired_tokens:
            self._cleanup_token(token)
        
        return len(expired_tokens)
    
    def get_storage_stats(self) -> Dict[str, int]:
        """Get storage statistics for monitoring."""
        return {
            'total_tokens': len(self._token_store),
            'expired_tokens_cleaned': self.cleanup_expired_tokens()
        }