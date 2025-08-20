#!/usr/bin/env python3

"""
PII Type Definitions

Enumeration classes for PII types, masking strategies, and context handling.
Provides standardized type definitions for consistent PII processing across
all components.

This module was extracted from PersonalDataProtectionAgent.py as part of Phase 14
code quality improvements to break down large class files.
"""

from enum import Enum


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