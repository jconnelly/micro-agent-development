#!/usr/bin/env python3
"""
Debug section boundary detection
"""

import os
import sys
import re
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from Utils.intelligent_chunker import IntelligentChunker
from Utils.language_detection import LanguageDetector


def debug_sections():
    """Debug section detection."""
    
    print("Debugging Section Detection...")
    
    # Load COBOL sample
    cobol_file_path = project_root / "Sample_Data_Files" / "sample_legacy_insurance.cbl"
    
    with open(cobol_file_path, 'r', encoding='utf-8') as f:
        cobol_content = f.read()
    
    lines = cobol_content.split('\n')
    
    # Test section patterns
    patterns = {
        "PROCEDURE DIVISION": r"^\s*PROCEDURE\s+DIVISION",
        "MAIN-PROGRAM": r"^\s*MAIN-PROGRAM\.",
        "VALIDATE-APPLICATION": r"^\s*VALIDATE-APPLICATION\.",
        "AUTO-VALIDATION": r"^\s*AUTO-VALIDATION\.", 
        "LIFE-VALIDATION": r"^\s*LIFE-VALIDATION\.",
        "CALCULATE-PREMIUM": r"^\s*CALCULATE-PREMIUM\.",
        "DISPLAY-RESULTS": r"^\s*DISPLAY-RESULTS\."
    }
    
    print("Section matches found:")
    for i, line in enumerate(lines):
        for section_name, pattern in patterns.items():
            if re.search(pattern, line, re.IGNORECASE):
                print(f"  Line {i+1}: {section_name} - '{line.strip()}'")
                break
    
    # Test chunker section detection
    language_detector = LanguageDetector()
    chunker = IntelligentChunker(language_detector)
    
    # Access the private method for testing
    boundaries = chunker._identify_section_boundaries(lines, "cobol", None)
    
    print(f"\nDetected {len(boundaries)} section boundaries:")
    for section_name, start, end in boundaries:
        print(f"  {section_name}: Lines {start+1}-{end} ({end-start} lines)")


if __name__ == "__main__":
    debug_sections()