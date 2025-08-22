#!/usr/bin/env python3

"""
Error Handling Module

Standardized error handling utilities for consistent exception management
across all agents with unified patterns, logging, and recovery mechanisms.
"""

from .standardized_handler import (
    StandardizedErrorHandler,
    handle_config_error,
    handle_validation_error, 
    handle_processing_error
)

__all__ = [
    'StandardizedErrorHandler',
    'handle_config_error',
    'handle_validation_error',
    'handle_processing_error'
]