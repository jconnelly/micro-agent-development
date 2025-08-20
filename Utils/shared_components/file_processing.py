#!/usr/bin/env python3

"""
Streaming File Processing Utilities

High-performance streaming file processor for large files (>100MB).
Implements memory-efficient chunked processing to handle enterprise-scale
files without loading entire contents into memory.

This module was extracted from StandardImports.py as part of Phase 14
code quality improvements to break down large class files.
"""

from pathlib import Path
from datetime import datetime as dt, timezone
from typing import Any, Callable, Dict, Union

# Type alias
PathType = Union[str, Path]


class StreamingFileProcessor:
    """
    High-performance streaming file processor for large files (>100MB).
    
    Implements memory-efficient chunked processing to handle enterprise-scale
    files without loading entire contents into memory.
    
    Part of Phase 11 Performance & Architecture optimizations.
    """
    
    # Configuration constants for optimal performance
    DEFAULT_CHUNK_SIZE = 1024 * 1024  # 1MB chunks for good memory/performance balance
    MAX_CHUNK_SIZE = 10 * 1024 * 1024  # 10MB maximum chunk size
    MIN_CHUNK_SIZE = 64 * 1024  # 64KB minimum chunk size
    OVERLAP_SIZE = 1024  # 1KB overlap between chunks to avoid splitting entities
    
    @staticmethod
    def process_large_file_streaming(file_path: PathType, 
                                   chunk_processor: Callable[[str, Dict[str, Any]], Any],
                                   chunk_size: int = None,
                                   encoding: str = 'utf-8',
                                   metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process a large file in streaming chunks to minimize memory usage.
        
        Args:
            file_path: Path to the file to process
            chunk_processor: Function to process each chunk (chunk_text, chunk_metadata) -> result
            chunk_size: Size of each chunk in bytes (defaults to 1MB)
            encoding: File encoding (default: utf-8)
            metadata: Additional metadata to pass to chunk processor
            
        Returns:
            Dictionary with processing results and performance metrics
        """
        file_path = Path(file_path)
        chunk_size = chunk_size or StreamingFileProcessor.DEFAULT_CHUNK_SIZE
        metadata = metadata or {}
        
        # Validate parameters
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if chunk_size < StreamingFileProcessor.MIN_CHUNK_SIZE:
            chunk_size = StreamingFileProcessor.MIN_CHUNK_SIZE
        elif chunk_size > StreamingFileProcessor.MAX_CHUNK_SIZE:
            chunk_size = StreamingFileProcessor.MAX_CHUNK_SIZE
        
        # Get file info
        file_size = file_path.stat().st_size
        estimated_chunks = max(1, file_size // chunk_size)
        
        start_time = dt.now(timezone.utc)
        results = []
        total_bytes_processed = 0
        chunk_number = 0
        overlap_buffer = ""
        
        try:
            with open(file_path, 'r', encoding=encoding, buffering=8192) as file:
                while True:
                    # Read chunk with overlap consideration
                    chunk_data = file.read(chunk_size)
                    if not chunk_data:
                        break
                    
                    chunk_number += 1
                    
                    # Apply overlap from previous chunk
                    if overlap_buffer:
                        chunk_data = overlap_buffer + chunk_data
                        overlap_buffer = ""
                    
                    # Prepare overlap for next chunk (last 1KB of current chunk)
                    if len(chunk_data) > StreamingFileProcessor.OVERLAP_SIZE:
                        overlap_buffer = chunk_data[-StreamingFileProcessor.OVERLAP_SIZE:]
                    
                    total_bytes_processed += len(chunk_data.encode(encoding))
                    
                    # Prepare chunk metadata
                    chunk_metadata = {
                        'chunk_number': chunk_number,
                        'chunk_size': len(chunk_data),
                        'total_chunks_estimated': estimated_chunks,
                        'total_bytes_processed': total_bytes_processed,
                        'file_size': file_size,
                        'progress_percentage': min(100.0, (total_bytes_processed / file_size) * 100),
                        'file_path': str(file_path),
                        **metadata
                    }
                    
                    # Process chunk
                    chunk_result = chunk_processor(chunk_data, chunk_metadata)
                    results.append({
                        'chunk_number': chunk_number,
                        'chunk_metadata': chunk_metadata,
                        'result': chunk_result
                    })
        
        except Exception as e:
            return {
                'success': False,
                'error': f"Streaming processing failed: {e}",
                'chunks_processed': chunk_number,
                'bytes_processed': total_bytes_processed,
                'duration_ms': (dt.now(timezone.utc) - start_time).total_seconds() * 1000
            }
        
        # Calculate final statistics
        end_time = dt.now(timezone.utc)
        duration_ms = (end_time - start_time).total_seconds() * 1000
        
        return {
            'success': True,
            'total_chunks': chunk_number,
            'total_bytes_processed': total_bytes_processed,
            'file_size': file_size,
            'duration_ms': duration_ms,
            'throughput_mb_per_sec': (total_bytes_processed / (1024 * 1024)) / (duration_ms / 1000) if duration_ms > 0 else 0,
            'chunks_per_second': chunk_number / (duration_ms / 1000) if duration_ms > 0 else 0,
            'results': results,
            'performance_metrics': {
                'memory_efficient': True,
                'streaming_method': 'chunk_based',
                'chunk_size_bytes': chunk_size,
                'overlap_size_bytes': StreamingFileProcessor.OVERLAP_SIZE,
                'estimated_vs_actual_chunks': f"{estimated_chunks} estimated, {chunk_number} actual"
            }
        }
    
    @staticmethod
    def get_file_size_category(file_path: PathType) -> str:
        """
        Categorize file size for processing strategy selection.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Size category string: 'small', 'medium', 'large', 'huge'
        """
        try:
            size_bytes = Path(file_path).stat().st_size
            size_mb = size_bytes / (1024 * 1024)
            
            if size_mb < 1:
                return 'small'
            elif size_mb < 10:
                return 'medium'
            elif size_mb < 100:
                return 'large'
            else:
                return 'huge'
        except (OSError, FileNotFoundError):
            return 'unknown'
    
    @staticmethod
    def should_use_streaming(file_path: PathType, threshold_mb: int = 10) -> bool:
        """
        Determine if a file should use streaming processing based on size.
        
        Args:
            file_path: Path to the file
            threshold_mb: Size threshold in MB (default: 10MB)
            
        Returns:
            True if file should use streaming processing
        """
        try:
            size_bytes = Path(file_path).stat().st_size
            size_mb = size_bytes / (1024 * 1024)
            return size_mb >= threshold_mb
        except (OSError, FileNotFoundError):
            return False