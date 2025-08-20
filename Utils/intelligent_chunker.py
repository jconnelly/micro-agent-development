#!/usr/bin/env python3
"""
Intelligent Chunker System for Rule Extraction Optimization
Phase 15B - Section-Aware Chunking & Rule Boundary Detection

This module provides advanced chunking algorithms that understand programming language
structure and preserve business rule boundaries for optimal extraction accuracy.

Key Features:
- Section-aware chunking (COBOL PROCEDURE DIVISION, Java classes, etc.)
- Rule boundary detection to prevent mid-rule splits
- Language-specific chunking strategies
- Adaptive chunk sizing with ±50% flexibility
- Multi-layered fallback strategy for robustness
"""

import re
import math
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

from Utils.language_detection import LanguageDetector, DetectionResult, LanguageProfile


class ChunkingStrategy(Enum):
    """Available chunking strategies in order of preference."""
    SECTION_AWARE = "section_aware"        # Highest priority: preserve sections
    RULE_BOUNDARY = "rule_boundary"        # High priority: preserve rule boundaries  
    SMART_OVERLAP = "smart_overlap"        # Medium priority: intelligent overlaps
    FIXED_SIZE = "fixed_size"             # Fallback: traditional line-based chunking


@dataclass
class ChunkMetadata:
    """Metadata for a generated chunk."""
    chunk_id: str
    start_line: int
    end_line: int
    content_lines: int
    strategy_used: ChunkingStrategy
    section_name: Optional[str] = None
    rule_count_estimate: int = 0
    confidence_score: float = 0.0
    
    @property
    def size_efficiency(self) -> float:
        """Calculate chunk size efficiency (0.0-1.0)."""
        if self.content_lines == 0:
            return 0.0
        return min(self.content_lines / 200, 1.0)  # Optimal around 200 lines


@dataclass  
class ChunkingResult:
    """Result of intelligent chunking operation."""
    chunks: List[str]
    metadata: List[ChunkMetadata]
    language: str
    strategy_used: ChunkingStrategy
    total_lines: int
    chunk_count: int
    estimated_rule_coverage: float
    
    @property
    def average_chunk_size(self) -> float:
        """Calculate average chunk size in lines."""
        if not self.metadata:
            return 0.0
        return sum(meta.content_lines for meta in self.metadata) / len(self.metadata)
    
    @property
    def size_variance(self) -> float:
        """Calculate chunk size variance (0.0 = uniform, higher = more variable)."""
        if len(self.metadata) < 2:
            return 0.0
        avg_size = self.average_chunk_size
        variance = sum((meta.content_lines - avg_size) ** 2 for meta in self.metadata) / len(self.metadata)
        return math.sqrt(variance) / avg_size if avg_size > 0 else 0.0


class IntelligentChunker:
    """
    Advanced chunking system with language-aware section detection and rule preservation.
    
    Implements multi-layered chunking strategies:
    1. Section-aware: Respects language-specific section boundaries
    2. Rule boundary: Prevents splitting individual business rules
    3. Smart overlap: Optimizes overlaps to preserve context
    4. Fixed size: Traditional fallback for unknown patterns
    """
    
    def __init__(self, language_detector: Optional[LanguageDetector] = None):
        """
        Initialize the intelligent chunker.
        
        Args:
            language_detector: Optional LanguageDetector instance for language-aware chunking
        """
        self.language_detector = language_detector
        
        # Chunking parameters (will be overridden by language-specific settings)
        self.default_params = {
            "preferred_size": 175,
            "min_size": 87,
            "max_size": 262, 
            "overlap_size": 25,
            "max_chunks": 50
        }
        
        # Strategy weights for multi-strategy evaluation
        self.strategy_weights = {
            ChunkingStrategy.SECTION_AWARE: 1.0,
            ChunkingStrategy.RULE_BOUNDARY: 0.8,
            ChunkingStrategy.SMART_OVERLAP: 0.6,
            ChunkingStrategy.FIXED_SIZE: 0.4
        }
    
    def chunk_content(self, content: str, filename: str = "unknown.txt", 
                     target_strategy: Optional[ChunkingStrategy] = None) -> ChunkingResult:
        """
        Perform intelligent chunking on content with automatic strategy selection.
        
        Args:
            content: The source code content to chunk
            filename: Name of file being chunked (for language detection)
            target_strategy: Optional specific strategy to use (otherwise auto-selected)
            
        Returns:
            ChunkingResult with optimized chunks and metadata
        """
        lines = content.split('\n')
        total_lines = len(lines)
        
        if total_lines == 0:
            return self._create_empty_result()
        
        # Phase 15A: Language detection for chunking parameters
        detection_result = None
        chunking_params = self.default_params.copy()
        language = "unknown"
        
        if self.language_detector:
            try:
                detection_result = self.language_detector.detect_language(filename, content)
                if detection_result.profile and detection_result.is_confident:
                    language = detection_result.language
                    profile_params = detection_result.profile.chunking
                    chunking_params.update({
                        "preferred_size": profile_params.get('preferred_size', 175),
                        "min_size": profile_params.get('min_size', 87),
                        "max_size": profile_params.get('max_size', 262),
                        "overlap_size": profile_params.get('overlap_size', 25),
                        "section_priority": profile_params.get('section_priority', {})
                    })
            except Exception as e:
                # Fallback to default parameters
                pass
        
        # Single chunk optimization
        if total_lines <= chunking_params["preferred_size"]:
            return self._create_single_chunk_result(content, lines, language)
        
        # Strategy selection and execution
        if target_strategy:
            strategy = target_strategy
        else:
            strategy = self._select_optimal_strategy(lines, language, detection_result)
        
        # Execute chunking strategy
        if strategy == ChunkingStrategy.SECTION_AWARE:
            return self._chunk_by_sections(lines, language, detection_result, chunking_params)
        elif strategy == ChunkingStrategy.RULE_BOUNDARY:
            return self._chunk_by_rules(lines, language, detection_result, chunking_params)
        elif strategy == ChunkingStrategy.SMART_OVERLAP:
            return self._chunk_with_smart_overlap(lines, language, chunking_params)
        else:  # FIXED_SIZE fallback
            return self._chunk_fixed_size(lines, language, chunking_params)
    
    def _select_optimal_strategy(self, lines: List[str], language: str, 
                               detection_result: Optional[DetectionResult]) -> ChunkingStrategy:
        """
        Select the optimal chunking strategy based on content analysis.
        
        Args:
            lines: Content lines to analyze
            language: Detected programming language
            detection_result: Language detection result with evidence
            
        Returns:
            Optimal ChunkingStrategy for the content
        """
        total_lines = len(lines)
        
        # Analyze content characteristics
        section_markers = self._count_section_markers(lines, language, detection_result)
        rule_patterns = self._count_rule_patterns(lines, language, detection_result)
        
        # Strategy scoring
        scores = {}
        
        # Section-aware strategy: prefer if many clear section boundaries
        if section_markers >= 3 and language in ['cobol', 'pascal', 'pli']:
            scores[ChunkingStrategy.SECTION_AWARE] = section_markers * 0.3
        else:
            scores[ChunkingStrategy.SECTION_AWARE] = 0.1
        
        # Rule boundary strategy: prefer if many rule patterns but few sections  
        if rule_patterns >= 5 and section_markers < 3:
            scores[ChunkingStrategy.RULE_BOUNDARY] = rule_patterns * 0.2
        else:
            scores[ChunkingStrategy.RULE_BOUNDARY] = rule_patterns * 0.1
        
        # Smart overlap: good middle ground for most content
        scores[ChunkingStrategy.SMART_OVERLAP] = 0.6
        
        # Fixed size: always available as fallback
        scores[ChunkingStrategy.FIXED_SIZE] = 0.4
        
        # Select highest scoring strategy
        optimal_strategy = max(scores.items(), key=lambda x: x[1])[0]
        
        return optimal_strategy
    
    def _chunk_by_sections(self, lines: List[str], language: str, 
                          detection_result: Optional[DetectionResult],
                          chunking_params: Dict[str, Any]) -> ChunkingResult:
        """
        Chunk content by preserving language-specific section boundaries.
        
        This is the primary strategy for COBOL and other structured languages
        where business rules are organized in clear sections.
        """
        section_boundaries = self._identify_section_boundaries(lines, language, detection_result)
        
        if not section_boundaries:
            # Fallback to rule boundary chunking if no sections found
            return self._chunk_by_rules(lines, language, detection_result, chunking_params)
        
        chunks = []
        metadata = []
        
        preferred_size = chunking_params["preferred_size"]
        min_size = chunking_params["min_size"]
        max_size = chunking_params["max_size"]
        overlap_size = chunking_params["overlap_size"]
        
        current_chunk_start = 0
        chunk_id = 1
        
        for section_name, section_start, section_end in section_boundaries:
            section_size = section_end - section_start
            current_chunk_size = section_start - current_chunk_start
            
            # If adding this section would exceed preferred size, create chunk now
            if (current_chunk_size + section_size) > preferred_size and current_chunk_size >= min_size:
                # Create chunk from current_chunk_start to section_start
                chunk_end = min(section_start + overlap_size, len(lines))
                chunk_lines = lines[current_chunk_start:chunk_end]
                chunk_content = '\n'.join(chunk_lines)
                
                chunks.append(chunk_content)
                metadata.append(ChunkMetadata(
                    chunk_id=f"section_{chunk_id}",
                    start_line=current_chunk_start + 1,
                    end_line=chunk_end,
                    content_lines=len(chunk_lines),
                    strategy_used=ChunkingStrategy.SECTION_AWARE,
                    section_name=section_name,
                    rule_count_estimate=self._estimate_rule_count(chunk_lines, language),
                    confidence_score=0.9  # High confidence for section-based chunking
                ))
                chunk_id += 1
                current_chunk_start = max(0, section_start - overlap_size)
        
        # Handle remaining content
        if current_chunk_start < len(lines):
            chunk_lines = lines[current_chunk_start:]
            if len(chunk_lines) >= min_size:
                chunks.append('\n'.join(chunk_lines))
                metadata.append(ChunkMetadata(
                    chunk_id=f"section_{chunk_id}",
                    start_line=current_chunk_start + 1,
                    end_line=len(lines),
                    content_lines=len(chunk_lines),
                    strategy_used=ChunkingStrategy.SECTION_AWARE,
                    rule_count_estimate=self._estimate_rule_count(chunk_lines, language),
                    confidence_score=0.9
                ))
        
        return ChunkingResult(
            chunks=chunks,
            metadata=metadata,
            language=language,
            strategy_used=ChunkingStrategy.SECTION_AWARE,
            total_lines=len(lines),
            chunk_count=len(chunks),
            estimated_rule_coverage=self._estimate_rule_coverage(metadata)
        )
    
    def _chunk_by_rules(self, lines: List[str], language: str,
                       detection_result: Optional[DetectionResult],
                       chunking_params: Dict[str, Any]) -> ChunkingResult:
        """
        Chunk content by identifying and preserving individual business rules.
        
        This strategy prevents splitting business rules across chunk boundaries.
        """
        rule_boundaries = self._identify_rule_boundaries(lines, language, detection_result)
        
        if not rule_boundaries:
            # Fallback to smart overlap if no clear rules found
            return self._chunk_with_smart_overlap(lines, language, chunking_params)
        
        chunks = []
        metadata = []
        
        preferred_size = chunking_params["preferred_size"]
        min_size = chunking_params["min_size"]
        max_size = chunking_params["max_size"]
        overlap_size = chunking_params["overlap_size"]
        
        current_chunk_start = 0
        chunk_id = 1
        
        for rule_start, rule_end in rule_boundaries:
            # Check if adding this rule exceeds max size
            potential_size = rule_end - current_chunk_start
            
            if potential_size > max_size and (rule_start - current_chunk_start) >= min_size:
                # Create chunk up to this rule
                chunk_end = min(rule_start + overlap_size, len(lines))
                chunk_lines = lines[current_chunk_start:chunk_end]
                
                chunks.append('\n'.join(chunk_lines))
                metadata.append(ChunkMetadata(
                    chunk_id=f"rule_{chunk_id}",
                    start_line=current_chunk_start + 1,
                    end_line=chunk_end,
                    content_lines=len(chunk_lines),
                    strategy_used=ChunkingStrategy.RULE_BOUNDARY,
                    rule_count_estimate=self._estimate_rule_count(chunk_lines, language),
                    confidence_score=0.8  # Good confidence for rule-based chunking
                ))
                chunk_id += 1
                current_chunk_start = max(0, rule_start - overlap_size)
        
        # Handle remaining content
        if current_chunk_start < len(lines):
            chunk_lines = lines[current_chunk_start:]
            if len(chunk_lines) >= min_size:
                chunks.append('\n'.join(chunk_lines))
                metadata.append(ChunkMetadata(
                    chunk_id=f"rule_{chunk_id}",
                    start_line=current_chunk_start + 1,
                    end_line=len(lines),
                    content_lines=len(chunk_lines),
                    strategy_used=ChunkingStrategy.RULE_BOUNDARY,
                    rule_count_estimate=self._estimate_rule_count(chunk_lines, language),
                    confidence_score=0.8
                ))
        
        return ChunkingResult(
            chunks=chunks,
            metadata=metadata,
            language=language,
            strategy_used=ChunkingStrategy.RULE_BOUNDARY,
            total_lines=len(lines),
            chunk_count=len(chunks),
            estimated_rule_coverage=self._estimate_rule_coverage(metadata)
        )
    
    def _chunk_with_smart_overlap(self, lines: List[str], language: str,
                                 chunking_params: Dict[str, Any]) -> ChunkingResult:
        """
        Chunk with intelligent overlap calculation based on content density.
        """
        chunks = []
        metadata = []
        
        preferred_size = chunking_params["preferred_size"]
        min_size = chunking_params["min_size"]
        max_size = chunking_params["max_size"]
        base_overlap = chunking_params["overlap_size"]
        
        current_pos = 0
        chunk_id = 1
        
        while current_pos < len(lines):
            # Calculate adaptive chunk size based on content density
            chunk_end = min(current_pos + preferred_size, len(lines))
            
            # Find optimal boundary within max_size limit
            boundary_end = self._find_optimal_boundary(
                lines, current_pos, chunk_end, min(current_pos + max_size, len(lines))
            )
            
            chunk_lines = lines[current_pos:boundary_end]
            if len(chunk_lines) >= min_size or current_pos == 0:
                chunks.append('\n'.join(chunk_lines))
                
                # Calculate adaptive overlap based on rule density
                rule_density = self._estimate_rule_count(chunk_lines, language) / len(chunk_lines)
                adaptive_overlap = max(base_overlap, int(base_overlap * (1 + rule_density)))
                adaptive_overlap = min(adaptive_overlap, len(chunk_lines) // 3)  # Cap at 1/3 of chunk
                
                metadata.append(ChunkMetadata(
                    chunk_id=f"smart_{chunk_id}",
                    start_line=current_pos + 1,
                    end_line=boundary_end,
                    content_lines=len(chunk_lines),
                    strategy_used=ChunkingStrategy.SMART_OVERLAP,
                    rule_count_estimate=self._estimate_rule_count(chunk_lines, language),
                    confidence_score=0.7  # Medium confidence for smart overlap
                ))
                chunk_id += 1
                
                current_pos = max(current_pos + min_size, boundary_end - adaptive_overlap)
            else:
                break
        
        return ChunkingResult(
            chunks=chunks,
            metadata=metadata,
            language=language,
            strategy_used=ChunkingStrategy.SMART_OVERLAP,
            total_lines=len(lines),
            chunk_count=len(chunks),
            estimated_rule_coverage=self._estimate_rule_coverage(metadata)
        )
    
    def _chunk_fixed_size(self, lines: List[str], language: str,
                         chunking_params: Dict[str, Any]) -> ChunkingResult:
        """
        Traditional fixed-size chunking as fallback strategy.
        """
        chunks = []
        metadata = []
        
        preferred_size = chunking_params["preferred_size"]
        overlap_size = chunking_params["overlap_size"]
        
        current_pos = 0
        chunk_id = 1
        
        while current_pos < len(lines):
            chunk_end = min(current_pos + preferred_size, len(lines))
            chunk_lines = lines[current_pos:chunk_end]
            
            chunks.append('\n'.join(chunk_lines))
            metadata.append(ChunkMetadata(
                chunk_id=f"fixed_{chunk_id}",
                start_line=current_pos + 1,
                end_line=chunk_end,
                content_lines=len(chunk_lines),
                strategy_used=ChunkingStrategy.FIXED_SIZE,
                rule_count_estimate=self._estimate_rule_count(chunk_lines, language),
                confidence_score=0.5  # Lower confidence for fixed chunking
            ))
            chunk_id += 1
            
            current_pos = chunk_end - overlap_size
            if current_pos >= chunk_end:
                break
        
        return ChunkingResult(
            chunks=chunks,
            metadata=metadata,
            language=language,
            strategy_used=ChunkingStrategy.FIXED_SIZE,
            total_lines=len(lines),
            chunk_count=len(chunks),
            estimated_rule_coverage=self._estimate_rule_coverage(metadata)
        )
    
    def _identify_section_boundaries(self, lines: List[str], language: str,
                                   detection_result: Optional[DetectionResult]) -> List[Tuple[str, int, int]]:
        """
        Identify major section boundaries in the code.
        
        Returns:
            List of (section_name, start_line, end_line) tuples
        """
        boundaries = []
        
        if language == "cobol":
            # COBOL-specific section detection - Enhanced for insurance sample
            patterns = {
                "PROCEDURE DIVISION": r"^\s*PROCEDURE\s+DIVISION",
                "MAIN-PROGRAM": r"^\s*MAIN-PROGRAM\.",
                "VALIDATE-APPLICATION": r"^\s*VALIDATE-APPLICATION\.",
                "AUTO-VALIDATION": r"^\s*AUTO-VALIDATION\.", 
                "LIFE-VALIDATION": r"^\s*LIFE-VALIDATION\.",
                "CALCULATE-PREMIUM": r"^\s*CALCULATE-PREMIUM\.",
                "DISPLAY-RESULTS": r"^\s*DISPLAY-RESULTS\.",
                # Generic patterns for other COBOL programs
                "VALIDATION": r"^\s*\w*VALIDATION\w*\.",
                "CALCULATE": r"^\s*CALCULATE\w*\."
            }
            
            for i, line in enumerate(lines):
                for section_name, pattern in patterns.items():
                    if re.search(pattern, line, re.IGNORECASE):
                        # Find section end (next section or end of file)
                        section_end = len(lines)
                        for j in range(i + 1, len(lines)):
                            if any(re.search(p, lines[j], re.IGNORECASE) for p in patterns.values()):
                                section_end = j
                                break
                        
                        boundaries.append((section_name, i, section_end))
                        break
        
        elif language == "java":
            # Java class and method boundaries
            for i, line in enumerate(lines):
                if re.search(r'^\s*(public|private|protected)?\s*(class|interface)\s+\w+', line):
                    # Find class end
                    brace_count = 0
                    class_end = len(lines)
                    for j in range(i, len(lines)):
                        brace_count += lines[j].count('{') - lines[j].count('}')
                        if brace_count == 0 and j > i:
                            class_end = j + 1
                            break
                    boundaries.append(("CLASS", i, class_end))
        
        return boundaries
    
    def _identify_rule_boundaries(self, lines: List[str], language: str,
                                detection_result: Optional[DetectionResult]) -> List[Tuple[int, int]]:
        """
        Identify individual business rule boundaries.
        
        Returns:
            List of (rule_start_line, rule_end_line) tuples
        """
        boundaries = []
        
        if language == "cobol":
            # Enhanced COBOL rule boundary detection
            rule_start_patterns = [
                r'^\s*\*\s*Business Rule:',  # Comment-marked business rules
                r'^\s*IF\s+.*',              # IF statements
                r'^\s*PERFORM\s+.*',         # PERFORM statements
                r'^\s*EVALUATE\s+.*',        # EVALUATE statements
                r'^\s*MOVE\s+.*TO\s+.*',     # MOVE statements
                r'^\s*COMPUTE\s+.*',         # COMPUTE statements
            ]
            
            rule_end_patterns = [
                r'^\s*END-IF\s*\.',
                r'^\s*END-PERFORM\s*\.',
                r'^\s*END-EVALUATE\s*\.',
                r'^\s*GO TO\s+.*',
                r'^\s*EXIT\s*\.'
            ]
            
            i = 0
            while i < len(lines):
                line = lines[i].strip()
                
                # Check for rule start patterns
                rule_started = False
                for pattern in rule_start_patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        rule_started = True
                        rule_start = i
                        break
                
                if rule_started:
                    # Find rule end
                    rule_end = i + 1
                    
                    # Look for explicit end markers
                    if 'IF' in line.upper():
                        # Find END-IF or natural boundary
                        nested_if_count = 0
                        for j in range(i, min(i + 30, len(lines))):  # Extended lookahead
                            check_line = lines[j].upper()
                            
                            # Count nested IFs
                            if 'IF ' in check_line and j > i:
                                nested_if_count += 1
                            elif 'END-IF' in check_line:
                                if nested_if_count > 0:
                                    nested_if_count -= 1
                                else:
                                    rule_end = j + 1
                                    break
                            # Look for other rule terminators
                            elif any(re.search(p, lines[j], re.IGNORECASE) for p in rule_end_patterns):
                                rule_end = j + 1
                                break
                            # Stop at next rule or section
                            elif j > i and (any(re.search(p, lines[j], re.IGNORECASE) for p in rule_start_patterns) or
                                           re.search(r'^\s*\w+-?(VALIDATION|EXIT|PROGRAM)\w*\.', lines[j], re.IGNORECASE)):
                                rule_end = j
                                break
                    
                    elif 'COMPUTE' in line.upper():
                        # COMPUTE statements often span multiple lines
                        for j in range(i + 1, min(i + 10, len(lines))):
                            if ('END-IF' in lines[j].upper() or 
                                lines[j].strip().endswith('.') or
                                any(re.search(p, lines[j], re.IGNORECASE) for p in rule_start_patterns)):
                                rule_end = j + 1 if not any(re.search(p, lines[j], re.IGNORECASE) for p in rule_start_patterns) else j
                                break
                    
                    else:
                        # For other patterns, look for natural boundaries
                        for j in range(i + 1, min(i + 15, len(lines))):
                            if (lines[j].strip() == '' or  # Empty line
                                any(re.search(p, lines[j], re.IGNORECASE) for p in rule_start_patterns) or  # Next rule
                                re.search(r'^\s*\w+-?(VALIDATION|EXIT|PROGRAM)\w*\.', lines[j], re.IGNORECASE)):  # Section end
                                rule_end = j
                                break
                    
                    # Add rule boundary if it's substantial
                    if rule_end > rule_start + 1:  # At least 2 lines
                        boundaries.append((rule_start, rule_end))
                    
                    i = rule_end - 1  # Skip to end of current rule
                
                i += 1
        
        return boundaries
    
    def _count_section_markers(self, lines: List[str], language: str,
                             detection_result: Optional[DetectionResult]) -> int:
        """Count the number of clear section markers in the content."""
        if not detection_result or not detection_result.profile:
            return 0
        
        count = 0
        for line in lines:
            for regex in detection_result.profile._section_regex:
                if regex.search(line):
                    count += 1
                    break
        
        return count
    
    def _count_rule_patterns(self, lines: List[str], language: str,
                           detection_result: Optional[DetectionResult]) -> int:
        """Count the number of business rule patterns in the content."""
        if not detection_result or not detection_result.profile:
            return 0
        
        count = 0
        for line in lines:
            for regex in detection_result.profile._rule_regex:
                matches = regex.findall(line)
                count += len(matches)
        
        return count
    
    def _estimate_rule_count(self, lines: List[str], language: str) -> int:
        """Estimate the number of business rules in a chunk with improved accuracy."""
        if language == 'cobol':
            # Enhanced COBOL business rule detection
            rule_count = 0
            
            # Look for explicit business rule comments
            for line in lines:
                if re.search(r'^\s*\*\s*Business Rule:', line, re.IGNORECASE):
                    rule_count += 1
            
            # If we found explicit markers, use those (most accurate)
            if rule_count > 0:
                return rule_count
            
            # Otherwise, use pattern-based estimation with better filtering
            decision_patterns = [
                r'^\s*IF\s+.*(?:REJECTED|APPROVED|PENDING)',  # Decision-making IF statements
                r'^\s*EVALUATE\s+.*',                          # EVALUATE statements
                r'^\s*COMPUTE\s+.*\*\s*[0-9.]',               # Premium calculations with multipliers
                r'^\s*MOVE\s+.*(?:REJECTED|APPROVED|PENDING)\s+TO',  # Status assignments
            ]
            
            rule_count = 0
            for line in lines:
                for pattern in decision_patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        rule_count += 1
                        break  # Count each line only once
            
            # Reasonable scaling for COBOL - typically 1 rule per 10-15 lines in business logic sections
            estimated_from_size = max(1, len(lines) // 12)
            
            # Use the higher of pattern-based or size-based estimation
            return max(rule_count, min(estimated_from_size, len(lines) // 8))
        
        else:
            # Generic estimation for other languages
            rule_indicators = {
                'java': [r'if\s*\([^)]*(?:reject|approve|valid)', r'switch\s*\(', r'while\s*\('],
                'pascal': [r'if\s+.*then', r'case\s+.*of', r'while\s+.*do']
            }
            
            patterns = rule_indicators.get(language, [])
            count = 0
            
            for line in lines:
                for pattern in patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        count += 1
                        break
            
            return max(count, len(lines) // 15)  # Conservative estimation
    
    def _estimate_rule_coverage(self, metadata: List[ChunkMetadata]) -> float:
        """Estimate the percentage of business rules that will be successfully extracted."""
        if not metadata:
            return 0.0
        
        # Higher confidence strategies and more rules per chunk = better coverage
        total_confidence = sum(meta.confidence_score * meta.rule_count_estimate for meta in metadata)
        total_rules = sum(meta.rule_count_estimate for meta in metadata)
        
        if total_rules == 0:
            return 0.0
        
        return min(total_confidence / total_rules, 1.0)
    
    def _find_optimal_boundary(self, lines: List[str], start: int, preferred_end: int, max_end: int) -> int:
        """Find the optimal chunk boundary to avoid splitting rules."""
        # Look for natural breakpoints (empty lines, comments, etc.)
        for end in range(preferred_end, max_end):
            if end >= len(lines):
                return len(lines)
            
            line = lines[end].strip()
            if not line or line.startswith(('*', '//', '#', ';')):
                return end + 1
        
        return preferred_end
    
    def _create_empty_result(self) -> ChunkingResult:
        """Create empty result for edge cases."""
        return ChunkingResult(
            chunks=[],
            metadata=[],
            language="unknown",
            strategy_used=ChunkingStrategy.FIXED_SIZE,
            total_lines=0,
            chunk_count=0,
            estimated_rule_coverage=0.0
        )
    
    def _create_single_chunk_result(self, content: str, lines: List[str], language: str) -> ChunkingResult:
        """Create result for content that doesn't need chunking."""
        metadata = [ChunkMetadata(
            chunk_id="single_chunk",
            start_line=1,
            end_line=len(lines),
            content_lines=len(lines),
            strategy_used=ChunkingStrategy.SECTION_AWARE,  # Best strategy for single chunk
            rule_count_estimate=self._estimate_rule_count(lines, language),
            confidence_score=1.0  # Perfect confidence for single chunk
        )]
        
        return ChunkingResult(
            chunks=[content],
            metadata=metadata,
            language=language,
            strategy_used=ChunkingStrategy.SECTION_AWARE,
            total_lines=len(lines),
            chunk_count=1,
            estimated_rule_coverage=1.0  # Single chunk = perfect coverage
        )