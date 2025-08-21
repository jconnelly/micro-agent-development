"""
Chunk Processing Component for Business Rule Extraction

This module handles file chunking, processing strategy determination, and chunk boundary
optimization for the BusinessRuleExtractionAgent.

Extracted from BusinessRuleExtractionAgent.py as part of Phase 16 Task 2 modularization.
"""

import re
from typing import Dict, Any, List, Optional, Tuple

# Import Intelligent Chunking System (Phase 15B)  
from Utils.intelligent_chunker import IntelligentChunker, ChunkingResult


class ChunkProcessor:
    """
    Handles file chunking and processing strategy for business rule extraction.
    
    Responsibilities:
    - Determine optimal processing strategy (single file vs chunked)
    - Intelligent file chunking with boundary detection
    - Chunk overlap management for rule continuity
    """
    
    def __init__(self, agent_config: Dict[str, Any]):
        """Initialize the chunk processor with configuration."""
        self.agent_config = agent_config
        self.intelligent_chunker = IntelligentChunker()
        
        # Load configuration
        processing_config = self.agent_config.get('processing_limits', {})
        self._chunking_threshold = processing_config.get('chunking_line_threshold', 175)
        self._min_chunk_size = processing_config.get('min_chunk_lines', 10)
        self._max_chunks = processing_config.get('max_file_chunks', 50)
        self._chunk_overlap = processing_config.get('chunk_overlap_size', 25)
        
    def determine_processing_strategy(self, legacy_code_snippet: str) -> Tuple[bool, int]:
        """
        Determine if the file should be processed as chunks or single file.
        
        Args:
            legacy_code_snippet: The code content to analyze
            
        Returns:
            Tuple of (should_chunk, line_count)
        """
        lines = legacy_code_snippet.split('\n')
        line_count = len(lines)
        
        # Determine if chunking is needed based on size
        should_chunk = line_count > self._chunking_threshold
        
        return should_chunk, line_count
    
    def chunk_large_file(self, content: str, chunk_size: int = None, 
                        overlap_size: int = None, chunking_params: Dict[str, Any] = None, 
                        filename: str = "unknown.txt") -> List[str]:
        """
        Break large files into intelligently chunked segments.
        
        Args:
            content: File content to chunk
            chunk_size: Size of each chunk (lines)
            overlap_size: Overlap between chunks (lines)
            chunking_params: Language-specific chunking parameters
            filename: Name of file being processed
            
        Returns:
            List of content chunks
        """
        processing_config = self.agent_config.get('processing_limits', {})
        chunk_size = chunk_size or chunking_params.get('preferred_size', processing_config.get('chunking_line_threshold', 175))
        overlap_size = overlap_size or chunking_params.get('overlap_size', processing_config.get('chunk_overlap_size', 25))
        
        lines = content.split('\n')
        MIN_CHUNK_SIZE = chunking_params.get('min_size', processing_config.get('min_chunk_lines', 10))
        
        MAX_CHUNKS = processing_config.get('max_file_chunks', 50)
        
        # Use intelligent chunker first
        try:
            chunking_result = self.intelligent_chunker.chunk_content(
                content=content,
                filename=filename,
                chunk_size=chunk_size,
                overlap_size=overlap_size
            )
            
            if chunking_result.chunks and len(chunking_result.chunks) <= MAX_CHUNKS:
                # Log successful intelligent chunking
                self._log_chunking_result("intelligent", len(chunking_result.chunks), chunk_size)
                return chunking_result.chunks
                
        except Exception as e:
            # Fall back to boundary-aware chunking
            pass
        
        # Fallback to boundary-aware chunking
        chunks = []
        i = 0
        
        while i < len(lines) and len(chunks) < MAX_CHUNKS:
            # Find smart chunk boundary
            chunk_end = min(i + chunk_size, len(lines))
            
            if chunk_end < len(lines):
                # Look for smart boundary near the target position
                smart_boundary = self._find_smart_boundary(lines, chunk_end)
                chunk_end = smart_boundary
            
            # Extract chunk content
            chunk_lines = lines[i:chunk_end]
            
            # Add overlap from previous chunk if not the first chunk
            if i > 0 and overlap_size > 0:
                overlap_start = max(0, i - overlap_size)
                overlap_lines = lines[overlap_start:i]
                chunk_lines = overlap_lines + chunk_lines
            
            # Only add chunk if it meets minimum size requirement
            if len(chunk_lines) >= MIN_CHUNK_SIZE:
                chunk_content = '\n'.join(chunk_lines)
                chunks.append(chunk_content)
            
            # Move to next chunk position
            i = chunk_end
        
        self._log_chunking_result("boundary-aware", len(chunks), chunk_size)
        return chunks
    
    def find_smart_boundary(self, lines: List[str], target_pos: int, search_window: int = 10) -> int:
        """
        Find an intelligent boundary for chunking near the target position.
        
        Args:
            lines: List of all lines in the file
            target_pos: Target position for the boundary
            search_window: Number of lines to search around target
            
        Returns:
            Optimized boundary position
        """
        return self._find_smart_boundary(lines, target_pos, search_window)
    
    def _find_smart_boundary(self, lines: List[str], target_pos: int, search_window: int = 10) -> int:
        """
        Internal method to find smart chunk boundaries.
        
        Looks for natural break points like:
        - End of functions/procedures
        - Empty lines
        - Comments
        - Section breaks
        """
        if target_pos >= len(lines):
            return len(lines)
        
        start_search = max(0, target_pos - search_window)
        end_search = min(len(lines), target_pos + search_window)
        
        # Look for ideal boundary patterns
        for i in range(target_pos, end_search):
            if i >= len(lines):
                return len(lines)
                
            line = lines[i].strip()
            
            # Ideal boundaries (end of blocks)
            if (line == '' or  # Empty line
                line.startswith(('END-', 'end ', '}', '*)')) or  # End of blocks
                lines[i].strip().endswith(('.', ';')) and len(line) < 50):  # End statements
                return i + 1
        
        # Look backwards for acceptable boundaries
        for i in range(target_pos - 1, start_search - 1, -1):
            if i < 0:
                break
                
            line = lines[i].strip()
            
            # Acceptable boundaries
            if (line == '' or  # Empty line
                line.startswith(('*', '//', '#')) or  # Comments
                line.endswith(('.', ';', ':')) and len(line) < 80):  # Statement ends
                return i + 1
        
        # If no smart boundary found, use target position
        return target_pos
    
    def _log_chunking_result(self, strategy: str, chunk_count: int, chunk_size: int) -> None:
        """Log the chunking strategy and results."""
        # This would typically use the agent's logging system
        # For now, we'll keep it simple
        pass
    
    def estimate_processing_time(self, chunk_count: int, has_context: bool = False) -> Tuple[int, int]:
        """
        Estimate processing time for chunks.
        
        Args:
            chunk_count: Number of chunks to process
            has_context: Whether context processing is included
            
        Returns:
            Tuple of (min_seconds, max_seconds)
        """
        # Base time per chunk (includes API call overhead)
        base_time_per_chunk = 2  # seconds
        
        # Additional time for context processing
        context_overhead = 1 if has_context else 0
        
        # API delay factor (can vary significantly)
        api_delay_factor = 1.5
        
        min_time = chunk_count * base_time_per_chunk + context_overhead
        max_time = int(chunk_count * base_time_per_chunk * api_delay_factor) + context_overhead
        
        return min_time, max_time
    
    def validate_chunk_quality(self, chunk: str, min_lines: int = None) -> bool:
        """
        Validate that a chunk meets quality requirements.
        
        Args:
            chunk: Chunk content to validate
            min_lines: Minimum required lines
            
        Returns:
            True if chunk meets quality requirements
        """
        if min_lines is None:
            min_lines = self._min_chunk_size
            
        lines = chunk.split('\n')
        
        # Check minimum size
        if len(lines) < min_lines:
            return False
        
        # Check that chunk has some non-empty content
        non_empty_lines = [line for line in lines if line.strip()]
        if len(non_empty_lines) < min_lines // 2:
            return False
        
        # Check for potential business logic indicators
        business_indicators = [
            'if ', 'when ', 'case ', 'switch ',
            'validate', 'check', 'verify', 'process',
            'calculate', 'compute', 'determine',
            'approve', 'reject', 'accept', 'deny'
        ]
        
        content_lower = chunk.lower()
        has_business_logic = any(indicator in content_lower for indicator in business_indicators)
        
        return has_business_logic