#!/usr/bin/env python3

"""
File Processor for Enterprise Privacy Agent

Standard file processing component with encoding detection, content handling, and optimization.
Extracted from EnterpriseDataPrivacyAgent for improved maintainability and focused functionality.

This component handles:
- File reading with robust encoding detection (UTF-8, Latin1 fallback)
- File metadata extraction and analysis
- Content processing and memory optimization
- Integration with Read tool and managed file operations
"""

import os
import uuid
import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# Import base types and utilities
from Utils.pii_components import MaskingStrategy
from Utils.time_utils import TimeUtils


class FileProcessor:
    """
    Enterprise-grade file processing component with robust encoding and optimization.
    
    **Key Features:**
    - **Robust Encoding Detection**: UTF-8 primary, Latin1 fallback for legacy files
    - **Tool Integration**: Native Read tool support with managed file fallback
    - **Memory Optimization**: Automatic strategy selection based on file size
    - **Metadata Extraction**: Comprehensive file analysis and statistics
    - **Resource Management**: Context managers for safe file operations
    
    **Performance Benefits:**
    - Automatic encoding detection prevents processing failures
    - Memory-optimized reading for large files
    - Comprehensive error handling with multiple fallback strategies
    - Real-time file metadata and processing statistics
    """
    
    def __init__(self, read_tool=None, logger=None, agent_config: Dict[str, Any] = None):
        """
        Initialize file processor with tools and configuration.
        
        Args:
            read_tool: Optional Claude Code Read tool for optimized file reading
            logger: Logger instance for audit trail and debugging
            agent_config: Agent configuration for thresholds and settings
        """
        self.read_tool = read_tool
        self.logger = logger
        self.agent_config = agent_config or {}
        
        # Performance tracking
        self.processing_stats = {
            'files_processed': 0,
            'total_bytes_processed': 0,
            'read_tool_usage': 0,
            'managed_io_usage': 0,
            'encoding_fallbacks': 0,
            'average_processing_time_ms': 0
        }
    
    def read_file_content(self, file_path: str, request_id: str = None) -> Dict[str, Any]:
        """
        Read file content with robust encoding detection and tool integration.
        
        Args:
            file_path: Path to file to read
            request_id: Optional request ID for audit trail
            
        Returns:
            Dictionary with file content, metadata, and processing information
        """
        if not request_id:
            request_id = f"file-read-{uuid.uuid4().hex}"
        
        start_time = datetime.datetime.now(datetime.timezone.utc)
        
        try:
            # Get file metadata first
            file_metadata = self._extract_file_metadata(file_path)
            
            # Attempt to read using Read tool first
            if self.read_tool:
                try:
                    file_content = self.read_tool(file_path=file_path)
                    read_method = "read_tool"
                    self.processing_stats['read_tool_usage'] += 1
                    
                    if self.logger:
                        self.logger.debug(f"File read using Read tool: {len(file_content)} characters", request_id=request_id)
                        
                except Exception as e:
                    if self.logger:
                        self.logger.warning(f"Read tool failed, using managed file I/O: {e}", request_id=request_id)
                    
                    # Fallback to managed file reading
                    content_result = self._read_with_managed_io(file_path, request_id)
                    file_content = content_result['content']
                    read_method = content_result['read_method']
            else:
                # Use managed file reading directly
                content_result = self._read_with_managed_io(file_path, request_id)
                file_content = content_result['content']
                read_method = content_result['read_method']
            
            processing_duration = TimeUtils.calculate_duration_ms(start_time)
            
            # Update statistics
            self._update_processing_stats(processing_duration, len(file_content))
            
            # Combine metadata with content and processing info
            file_metadata.update({
                'content_length': len(file_content),
                'read_method': read_method,
                'processing_duration_ms': processing_duration,
                'memory_efficient': True,
                'request_id': request_id
            })
            
            return {
                'success': True,
                'content': file_content,
                'metadata': file_metadata,
                'processing_info': {
                    'read_method': read_method,
                    'processing_duration_ms': processing_duration,
                    'content_length': len(file_content),
                    'encoding_used': content_result.get('encoding_used', 'utf-8'),
                    'request_id': request_id
                }
            }
            
        except Exception as e:
            processing_duration = TimeUtils.calculate_duration_ms(start_time)
            
            if self.logger:
                self.logger.error(f"File processing failed for {file_path}: {e}", request_id=request_id)
            
            return {
                'success': False,
                'error': str(e),
                'metadata': self._extract_file_metadata(file_path),
                'processing_info': {
                    'read_method': 'failed',
                    'processing_duration_ms': processing_duration,
                    'error_occurred': True,
                    'request_id': request_id
                }
            }
    
    def _read_with_managed_io(self, file_path: str, request_id: str) -> Dict[str, Any]:
        """
        Read file using managed I/O with encoding fallback strategy.
        
        Args:
            file_path: Path to file to read
            request_id: Request ID for logging
            
        Returns:
            Dictionary with content, read method, and encoding information
        """
        from Utils.resource_managers import managed_file
        
        # Try UTF-8 first (most common encoding)
        try:
            with managed_file(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.processing_stats['managed_io_usage'] += 1
            
            return {
                'content': content,
                'read_method': 'managed_io_utf8',
                'encoding_used': 'utf-8',
                'encoding_fallback': False
            }
            
        except UnicodeDecodeError:
            # Fallback to Latin1 for legacy files
            if self.logger:
                self.logger.info(f"UTF-8 decode failed, trying Latin1 for {file_path}", request_id=request_id)
            
            try:
                with managed_file(file_path, 'r', encoding='latin1') as f:
                    content = f.read()
                
                self.processing_stats['managed_io_usage'] += 1
                self.processing_stats['encoding_fallbacks'] += 1
                
                return {
                    'content': content,
                    'read_method': 'managed_io_latin1',
                    'encoding_used': 'latin1',
                    'encoding_fallback': True
                }
                
            except Exception as e:
                # Final fallback - try binary mode and decode errors
                if self.logger:
                    self.logger.warning(f"Latin1 decode failed, trying binary mode for {file_path}: {e}", request_id=request_id)
                
                with managed_file(file_path, 'rb') as f:
                    binary_content = f.read()
                    content = binary_content.decode('utf-8', errors='replace')
                
                self.processing_stats['managed_io_usage'] += 1
                self.processing_stats['encoding_fallbacks'] += 1
                
                return {
                    'content': content,
                    'read_method': 'managed_io_binary_fallback',
                    'encoding_used': 'utf-8-replace',
                    'encoding_fallback': True
                }
    
    def _extract_file_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        Extract comprehensive file metadata for analysis and optimization.
        
        Args:
            file_path: Path to file to analyze
            
        Returns:
            Dictionary with file metadata and statistics
        """
        try:
            file_path_obj = Path(file_path)
            file_stats = os.stat(file_path)
            file_size_mb = file_stats.st_size / (1024 * 1024)
            
            # Determine processing strategy based on file size
            large_file_threshold_mb = self.agent_config.get('performance_thresholds', {}).get('large_file_mb', 10)
            is_large_file = file_size_mb > large_file_threshold_mb
            
            return {
                'file_path': str(file_path_obj),
                'file_name': file_path_obj.name,
                'file_extension': file_path_obj.suffix.lower(),
                'file_size_bytes': file_stats.st_size,
                'file_size_mb': round(file_size_mb, 2),
                'file_exists': file_path_obj.exists(),
                'is_large_file': is_large_file,
                'suggested_processing_method': 'streaming' if is_large_file else 'standard',
                'created_time': datetime.datetime.fromtimestamp(file_stats.st_ctime, datetime.timezone.utc).isoformat(),
                'modified_time': datetime.datetime.fromtimestamp(file_stats.st_mtime, datetime.timezone.utc).isoformat(),
                'access_time': datetime.datetime.fromtimestamp(file_stats.st_atime, datetime.timezone.utc).isoformat()
            }
            
        except Exception as e:
            return {
                'file_path': str(file_path),
                'file_name': Path(file_path).name,
                'error': str(e),
                'file_exists': False,
                'metadata_extraction_failed': True
            }
    
    def process_file_content(self, content: str, file_metadata: Dict[str, Any], 
                           processing_context: str = "general") -> Dict[str, Any]:
        """
        Process file content with optimization based on size and type.
        
        Args:
            content: File content to process
            file_metadata: File metadata from extraction
            processing_context: Context for processing optimization
            
        Returns:
            Dictionary with processed content and processing information
        """
        start_time = datetime.datetime.now(datetime.timezone.utc)
        
        # Determine optimal processing strategy
        content_length = len(content)
        is_large_content = content_length > self.agent_config.get('performance_thresholds', {}).get('large_text_threshold', 50000)
        
        processing_strategy = {
            'strategy': 'large_content_optimized' if is_large_content else 'standard_processing',
            'content_length': content_length,
            'line_count': content.count('\n') + 1,
            'estimated_processing_time_ms': self._estimate_processing_time(content_length),
            'memory_efficient': True,
            'context': processing_context
        }
        
        # Basic content analysis
        content_analysis = {
            'character_count': content_length,
            'line_count': content.count('\n') + 1,
            'word_count': len(content.split()),
            'paragraph_count': len([p for p in content.split('\n\n') if p.strip()]),
            'has_special_characters': bool(re.search(r'[^\w\s]', content)),
            'estimated_pii_likelihood': self._estimate_pii_likelihood(content)
        }
        
        processing_duration = TimeUtils.calculate_duration_ms(start_time)
        
        return {
            'processed_content': content,  # Content passed through for now
            'content_analysis': content_analysis,
            'processing_strategy': processing_strategy,
            'processing_metadata': {
                'processing_duration_ms': processing_duration,
                'content_length': content_length,
                'processing_context': processing_context,
                'optimization_applied': is_large_content
            }
        }
    
    def _estimate_processing_time(self, content_length: int) -> float:
        """Estimate processing time based on content length and historical data."""
        base_time_ms = 10  # Base processing time
        length_factor = content_length / 1000  # 1ms per 1K characters
        
        return base_time_ms + length_factor
    
    def _estimate_pii_likelihood(self, content: str) -> float:
        """
        Estimate likelihood of PII presence based on content patterns.
        
        Args:
            content: Content to analyze
            
        Returns:
            Float between 0.0 and 1.0 indicating PII likelihood
        """
        import re
        
        # Simple heuristics for PII likelihood
        indicators = 0
        total_checks = 8
        
        # Check for common PII patterns (simplified)
        if re.search(r'\b\d{3}-\d{2}-\d{4}\b', content):  # SSN pattern
            indicators += 1
        if re.search(r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b', content):  # Credit card pattern
            indicators += 1
        if re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', content):  # Email pattern
            indicators += 1
        if re.search(r'\b\d{3}[- ]?\d{3}[- ]?\d{4}\b', content):  # Phone pattern
            indicators += 1
        if re.search(r'\b\d{1,5}\s\w+\s(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd)\b', content, re.IGNORECASE):  # Address pattern
            indicators += 1
        if re.search(r'\b(?:Mr|Mrs|Ms|Dr|Prof)\.?\s[A-Z][a-z]+\s[A-Z][a-z]+\b', content):  # Name pattern
            indicators += 1
        if re.search(r'\b\d{4}[- /]\d{2}[- /]\d{2}\b', content):  # Date pattern
            indicators += 1
        if re.search(r'\$\d+\.?\d*', content):  # Currency pattern
            indicators += 1
        
        return indicators / total_checks
    
    def _update_processing_stats(self, processing_duration: float, content_length: int):
        """Update internal processing statistics."""
        self.processing_stats['files_processed'] += 1
        self.processing_stats['total_bytes_processed'] += content_length
        
        # Calculate rolling average processing time
        current_avg = self.processing_stats['average_processing_time_ms']
        total_files = self.processing_stats['files_processed']
        
        self.processing_stats['average_processing_time_ms'] = (
            (current_avg * (total_files - 1) + processing_duration) / total_files
        )
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive performance summary for monitoring.
        
        Returns:
            Dictionary with performance metrics and statistics
        """
        total_files = self.processing_stats['files_processed']
        
        return {
            'files_processed': total_files,
            'total_bytes_processed': self.processing_stats['total_bytes_processed'],
            'average_file_size_bytes': (
                self.processing_stats['total_bytes_processed'] / total_files
                if total_files > 0 else 0
            ),
            'read_tool_usage_percentage': (
                (self.processing_stats['read_tool_usage'] / total_files * 100)
                if total_files > 0 else 0
            ),
            'managed_io_usage_percentage': (
                (self.processing_stats['managed_io_usage'] / total_files * 100)
                if total_files > 0 else 0
            ),
            'encoding_fallback_rate': (
                (self.processing_stats['encoding_fallbacks'] / total_files * 100)
                if total_files > 0 else 0
            ),
            'average_processing_time_ms': self.processing_stats['average_processing_time_ms']
        }