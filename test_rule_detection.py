#!/usr/bin/env python3
"""
Test rule boundary detection with COBOL sample
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from Utils.intelligent_chunker import IntelligentChunker
from Utils.language_detection import LanguageDetector


def test_rule_detection():
    """Test rule boundary detection."""
    
    print("Testing Rule Boundary Detection...")
    
    # Load COBOL sample
    cobol_file_path = project_root / "Sample_Data_Files" / "sample_legacy_insurance.cbl"
    
    try:
        with open(cobol_file_path, 'r', encoding='utf-8') as f:
            cobol_content = f.read()
        print(f"Loaded COBOL sample: {len(cobol_content.split(chr(10)))} lines")
    except Exception as e:
        print(f"Error loading file: {e}")
        return False
    
    # Initialize components
    try:
        language_detector = LanguageDetector()
        chunker = IntelligentChunker(language_detector)
        print("Components initialized")
    except Exception as e:
        print(f"Error initializing: {e}")
        return False
    
    # Test section-aware chunking
    try:
        result = chunker.chunk_content(
            content=cobol_content,
            filename="sample_legacy_insurance.cbl"
        )
        
        print(f"\nChunking Results:")
        print(f"  Language: {result.language}")
        print(f"  Strategy: {result.strategy_used.value}")
        print(f"  Total lines: {result.total_lines}")
        print(f"  Chunks created: {result.chunk_count}")
        print(f"  Average size: {result.average_chunk_size:.1f} lines")
        print(f"  Estimated coverage: {result.estimated_rule_coverage:.1%}")
        
        # Show chunk details
        total_estimated_rules = 0
        print(f"\nChunk Details:")
        for i, metadata in enumerate(result.metadata):
            section_info = f" [{metadata.section_name}]" if metadata.section_name else ""
            print(f"  Chunk {i+1}: Lines {metadata.start_line}-{metadata.end_line} "
                  f"({metadata.content_lines} lines) - "
                  f"{metadata.rule_count_estimate} rules{section_info}")
            total_estimated_rules += metadata.rule_count_estimate
        
        print(f"\nRule Extraction Prediction:")
        print(f"  Total estimated rules: {total_estimated_rules}")
        print(f"  Expected extraction: {total_estimated_rules * result.estimated_rule_coverage:.0f} rules")
        print(f"  Current system: 14 rules (58.3%)")
        print(f"  Target: 24 rules (100%)")
        
        predicted_accuracy = (total_estimated_rules * result.estimated_rule_coverage) / 24 * 100
        print(f"  Predicted accuracy: {predicted_accuracy:.1f}%")
        
        success = predicted_accuracy >= 90
        print(f"  90% Target: {'ACHIEVED' if success else 'NOT ACHIEVED'}")
        
        return success
        
    except Exception as e:
        print(f"Error during chunking: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    test_rule_detection()