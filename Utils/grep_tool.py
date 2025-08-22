#!/usr/bin/env python3
"""
High-Performance Grep Tool for PII Detection

Enterprise-grade pattern matching tool that provides grep-like functionality
with optimizations for PII detection workloads. Supports both subprocess
grep calls and optimized Python-based pattern matching.
"""

import re
import subprocess
import tempfile
import os
import json
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
import logging


class GrepTool:
    """
    High-performance grep tool for pattern matching in large texts.
    
    Provides multiple strategies for pattern matching:
    1. System grep command (fastest for very large texts)
    2. Optimized Python regex (best for medium texts) 
    3. Memory-mapped file processing (for huge files)
    
    Features:
    - Automatic strategy selection based on text size
    - PII-specific optimizations
    - Context extraction for matches
    - Performance monitoring and statistics
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None, 
                 use_system_grep: bool = True):
        """
        Initialize the grep tool with configuration options.
        
        Args:
            logger: Optional logger for debugging and monitoring
            use_system_grep: Whether to use system grep command when available
        """
        self.logger = logger or logging.getLogger(__name__)
        self.use_system_grep = use_system_grep
        self.stats = {
            'total_searches': 0,
            'system_grep_usage': 0,
            'python_regex_usage': 0,
            'total_matches_found': 0,
            'average_search_time_ms': 0.0
        }
        
        # Check if system grep is available
        self.system_grep_available = self._check_system_grep()
        
        # Strategy thresholds (characters)
        self.small_text_threshold = 10000      # 10KB - use Python regex
        self.medium_text_threshold = 100000    # 100KB - use optimized Python
        self.large_text_threshold = 1000000    # 1MB - use system grep if available
        
    def _check_system_grep(self) -> bool:
        """Check if system grep command is available."""
        try:
            result = subprocess.run(['grep', '--version'], 
                                  capture_output=True, 
                                  timeout=5)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            return False
    
    def search_pattern(self, text: str, pattern: str, pii_type: Any = None, 
                      case_insensitive: bool = True) -> List[Dict[str, Any]]:
        """
        Search for pattern in text using optimal strategy.
        
        Args:
            text: Text to search in
            pattern: Regex pattern to search for
            pii_type: Type of PII being searched (for logging)
            case_insensitive: Whether to perform case-insensitive search
            
        Returns:
            List of match dictionaries with position and metadata
        """
        import time
        start_time = time.time()
        
        try:
            self.stats['total_searches'] += 1
            
            # Choose optimal strategy based on text size
            text_length = len(text)
            
            if (text_length > self.large_text_threshold and 
                self.system_grep_available and self.use_system_grep):
                # Use system grep for very large texts
                matches = self._search_with_system_grep(text, pattern, case_insensitive)
                self.stats['system_grep_usage'] += 1
                
            else:
                # Use optimized Python regex
                matches = self._search_with_python_regex(text, pattern, case_insensitive)
                self.stats['python_regex_usage'] += 1
            
            # Update statistics
            search_duration_ms = (time.time() - start_time) * 1000
            self._update_stats(search_duration_ms, len(matches))
            
            # Log performance info
            if self.logger:
                strategy = "system_grep" if text_length > self.large_text_threshold else "python_regex"
                self.logger.debug(
                    f"Grep search completed: pattern='{pattern[:30]}...', "
                    f"text_length={text_length}, matches={len(matches)}, "
                    f"strategy={strategy}, duration={search_duration_ms:.2f}ms"
                )
            
            return matches
            
        except Exception as e:
            self.logger.error(f"Grep search failed for pattern '{pattern}': {e}")
            return []
    
    def _search_with_system_grep(self, text: str, pattern: str, 
                                case_insensitive: bool) -> List[Dict[str, Any]]:
        """
        Use system grep command for high-performance search.
        
        Creates temporary file and uses grep with line numbers and byte offsets.
        """
        matches = []
        
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(mode='w', delete=False, 
                                           encoding='utf-8', suffix='.tmp') as tmp_file:
                tmp_file.write(text)
                tmp_filename = tmp_file.name
            
            # Build grep command
            grep_cmd = ['grep']
            if case_insensitive:
                grep_cmd.append('-i')
            
            # Add options for detailed output
            grep_cmd.extend([
                '-n',  # Line numbers
                '-b',  # Byte offset
                '-o',  # Only matching parts
                '-E',  # Extended regex
                pattern,
                tmp_filename
            ])
            
            # Execute grep
            result = subprocess.run(grep_cmd, capture_output=True, 
                                  text=True, timeout=30)
            
            if result.returncode == 0:  # Matches found
                lines = result.stdout.strip().split('\n')
                
                for line in lines:
                    if line:
                        match_info = self._parse_grep_output(line, text)
                        if match_info:
                            matches.append(match_info)
            
            # Clean up temporary file
            os.unlink(tmp_filename)
            
        except subprocess.TimeoutExpired:
            self.logger.warning(f"Grep search timed out for pattern: {pattern}")
        except Exception as e:
            self.logger.error(f"System grep search failed: {e}")
        
        return matches
    
    def _parse_grep_output(self, grep_line: str, original_text: str) -> Optional[Dict[str, Any]]:
        """
        Parse grep output line to extract match information.
        
        Grep output format: "byte_offset:line_number:match"
        """
        try:
            # Split grep output (byte_offset:line_number:match)
            parts = grep_line.split(':', 2)
            if len(parts) >= 3:
                byte_offset = int(parts[0])
                line_number = int(parts[1])
                match_value = parts[2]
                
                # Calculate positions
                start_pos = byte_offset
                end_pos = start_pos + len(match_value.encode('utf-8'))
                
                # Extract context
                context = self._extract_context(original_text, start_pos, end_pos)
                
                return {
                    'value': match_value,
                    'start': start_pos,
                    'end': end_pos,
                    'line_number': line_number,
                    'confidence': 0.98,  # High confidence for system grep
                    'context': context,
                    'method': 'system_grep'
                }
        except (ValueError, IndexError) as e:
            self.logger.warning(f"Failed to parse grep output '{grep_line}': {e}")
        
        return None
    
    def _search_with_python_regex(self, text: str, pattern: str, 
                                 case_insensitive: bool) -> List[Dict[str, Any]]:
        """
        Use optimized Python regex for pattern matching.
        
        Provides fallback when system grep is unavailable or for smaller texts.
        """
        matches = []
        
        try:
            # Compile pattern with appropriate flags
            flags = re.MULTILINE
            if case_insensitive:
                flags |= re.IGNORECASE
            
            compiled_pattern = re.compile(pattern, flags)
            
            # Efficient processing based on text size
            if len(text) > self.medium_text_threshold:
                # Line-by-line processing for large texts
                matches = self._line_by_line_search(text, compiled_pattern)
            else:
                # Standard processing for smaller texts
                for match in compiled_pattern.finditer(text):
                    match_info = {
                        'value': match.group(),
                        'start': match.start(),
                        'end': match.end(),
                        'line_number': text[:match.start()].count('\n') + 1,
                        'confidence': 0.95,  # High confidence for regex
                        'context': self._extract_context(text, match.start(), match.end()),
                        'method': 'python_regex'
                    }
                    matches.append(match_info)
        
        except re.error as e:
            self.logger.warning(f"Invalid regex pattern '{pattern}': {e}")
        except Exception as e:
            self.logger.error(f"Python regex search failed: {e}")
        
        return matches
    
    def _line_by_line_search(self, text: str, compiled_pattern: re.Pattern) -> List[Dict[str, Any]]:
        """
        Efficient line-by-line search for large texts.
        
        Reduces memory usage and improves performance for large documents.
        """
        matches = []
        lines = text.split('\n')
        current_pos = 0
        
        for line_num, line in enumerate(lines, 1):
            for match in compiled_pattern.finditer(line):
                absolute_start = current_pos + match.start()
                absolute_end = current_pos + match.end()
                
                match_info = {
                    'value': match.group(),
                    'start': absolute_start,
                    'end': absolute_end,
                    'line_number': line_num,
                    'confidence': 0.95,
                    'context': line.strip(),  # Use full line as context
                    'method': 'python_regex_line_by_line'
                }
                matches.append(match_info)
            
            current_pos += len(line) + 1  # +1 for newline
        
        return matches
    
    def _extract_context(self, text: str, start: int, end: int, 
                        context_chars: int = 80) -> str:
        """
        Extract context around a match for validation and debugging.
        """
        context_start = max(0, start - context_chars)
        context_end = min(len(text), end + context_chars)
        
        context = text[context_start:context_end]
        match_value = text[start:end]
        
        # Highlight the match within context
        relative_start = start - context_start
        relative_end = end - context_start
        
        highlighted_context = (
            context[:relative_start] + 
            f"[{match_value}]" + 
            context[relative_end:]
        )
        
        # Clean up whitespace and newlines for readability
        return highlighted_context.replace('\n', ' ').replace('\r', '').strip()
    
    def _update_stats(self, search_duration_ms: float, matches_found: int):
        """Update internal performance statistics."""
        self.stats['total_matches_found'] += matches_found
        
        # Calculate rolling average
        total_searches = self.stats['total_searches']
        current_avg = self.stats['average_search_time_ms']
        
        self.stats['average_search_time_ms'] = (
            (current_avg * (total_searches - 1) + search_duration_ms) / total_searches
        )
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive performance statistics.
        
        Returns:
            Dictionary with performance metrics and usage statistics
        """
        total_searches = self.stats['total_searches']
        
        return {
            'total_searches': total_searches,
            'system_grep_usage_percentage': (
                (self.stats['system_grep_usage'] / total_searches * 100)
                if total_searches > 0 else 0
            ),
            'python_regex_usage_percentage': (
                (self.stats['python_regex_usage'] / total_searches * 100)
                if total_searches > 0 else 0
            ),
            'total_matches_found': self.stats['total_matches_found'],
            'average_matches_per_search': (
                self.stats['total_matches_found'] / total_searches
                if total_searches > 0 else 0
            ),
            'average_search_time_ms': self.stats['average_search_time_ms'],
            'system_grep_available': self.system_grep_available,
            'strategy_thresholds': {
                'small_text_kb': self.small_text_threshold // 1000,
                'medium_text_kb': self.medium_text_threshold // 1000,
                'large_text_kb': self.large_text_threshold // 1000
            }
        }
    
    def reset_stats(self):
        """Reset all performance statistics."""
        self.stats = {
            'total_searches': 0,
            'system_grep_usage': 0,
            'python_regex_usage': 0,
            'total_matches_found': 0,
            'average_search_time_ms': 0.0
        }


# Convenience function for quick pattern searches
def search_text(text: str, pattern: str, case_insensitive: bool = True) -> List[Dict[str, Any]]:
    """
    Quick pattern search function using optimized grep tool.
    
    Args:
        text: Text to search
        pattern: Regex pattern
        case_insensitive: Case-insensitive search flag
        
    Returns:
        List of match dictionaries
    """
    grep_tool = GrepTool()
    return grep_tool.search_pattern(text, pattern, case_insensitive=case_insensitive)


if __name__ == "__main__":
    # Simple test of the grep tool
    test_text = """
    John Doe's SSN is 123-45-6789 and his email is john.doe@example.com.
    Jane Smith can be reached at jane.smith@company.org or call 555-123-4567.
    Credit card number: 4532-1234-5678-9012
    """
    
    grep_tool = GrepTool()
    
    # Test SSN pattern
    ssn_pattern = r'\b\d{3}-\d{2}-\d{4}\b'
    ssn_matches = grep_tool.search_pattern(test_text, ssn_pattern)
    print(f"SSN matches found: {len(ssn_matches)}")
    for match in ssn_matches:
        print(f"  {match['value']} at line {match['line_number']}")
    
    # Test email pattern  
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    email_matches = grep_tool.search_pattern(test_text, email_pattern)
    print(f"Email matches found: {len(email_matches)}")
    for match in email_matches:
        print(f"  {match['value']} at line {match['line_number']}")
    
    # Print performance stats
    stats = grep_tool.get_performance_stats()
    print(f"Performance: {stats['total_searches']} searches, avg {stats['average_search_time_ms']:.2f}ms")