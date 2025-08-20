#!/usr/bin/env python3
"""
Simple test for IntelligentChunker
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from Utils.intelligent_chunker import IntelligentChunker, ChunkingStrategy
from Utils.language_detection import LanguageDetector


def test_simple():
    """Simple test of intelligent chunker."""
    
    print("Testing IntelligentChunker...")
    
    # Simple COBOL content
    cobol_content = """
    IDENTIFICATION DIVISION.
    PROGRAM-ID. INSURANCE-VALIDATION.
    
    DATA DIVISION.
    WORKING-STORAGE SECTION.
    01 APPLICANT-AGE PIC 99 VALUE ZERO.
    
    PROCEDURE DIVISION.
    VALIDATE-APPLICATION.
        IF APPLICANT-AGE < 18
           MOVE 'REJECTED' TO APPLICATION-STATUS
        END-IF.
        
    AUTO-VALIDATION.
        IF DRIVING-YEARS < 2
           MOVE 'REJECTED' TO APPLICATION-STATUS
        END-IF.
    
    LIFE-VALIDATION.
        IF IS-SMOKER
           MOVE 'PENDING' TO APPLICATION-STATUS
        END-IF.
    """
    
    try:
        # Initialize components
        language_detector = LanguageDetector()
        chunker = IntelligentChunker(language_detector)
        
        print("Components initialized successfully")
        
        # Test chunking
        result = chunker.chunk_content(
            content=cobol_content,
            filename="test.cbl",
            target_strategy=ChunkingStrategy.SECTION_AWARE
        )
        
        print(f"Chunking successful:")
        print(f"  Language: {result.language}")
        print(f"  Strategy: {result.strategy_used.value}")
        print(f"  Chunks: {result.chunk_count}")
        print(f"  Coverage: {result.estimated_rule_coverage:.1%}")
        
        for i, metadata in enumerate(result.metadata):
            print(f"  Chunk {i+1}: {metadata.content_lines} lines, {metadata.rule_count_estimate} rules")
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    test_simple()