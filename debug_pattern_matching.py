#!/usr/bin/env python3
"""
Debug Pattern Matching for Rule Completeness Analyzer

This script helps debug which patterns are matching and why we're getting
7 expected rules instead of 24.
"""

import re
from pathlib import Path
from Utils.rule_completeness_analyzer import RuleCompletenessAnalyzer, RuleCategory

def debug_pattern_matching():
    """Debug pattern matching against COBOL sample."""
    
    print("=" * 70)
    print("Debug Pattern Matching for Rule Completeness Analyzer")
    print("=" * 70)
    
    # Load COBOL sample
    cobol_file_path = Path("Sample_Data_Files/sample_legacy_insurance.cbl")
    
    try:
        with open(cobol_file_path, 'r', encoding='utf-8') as f:
            cobol_content = f.read()
        print(f"Loaded COBOL sample: {len(cobol_content.split(chr(10)))} lines")
    except Exception as e:
        print(f"Error loading COBOL file: {e}")
        return False
    
    # Initialize analyzer
    analyzer = RuleCompletenessAnalyzer()
    patterns = analyzer.rule_patterns.get("cobol", {})
    
    lines = cobol_content.split('\n')
    
    print(f"\n--- Pattern Matching Analysis ---")
    
    total_matches = 0
    
    for category, category_patterns in patterns.items():
        print(f"\n{category.value.upper()} Category:")
        category_matches = 0
        
        for pattern_idx, pattern in enumerate(category_patterns):
            print(f"  Pattern {pattern_idx + 1}: {pattern}")
            pattern_matches = []
            
            for line_num, line in enumerate(lines, 1):
                if re.search(pattern, line, re.IGNORECASE):
                    pattern_matches.append((line_num, line.strip()))
                    category_matches += 1
            
            if pattern_matches:
                print(f"    Matches ({len(pattern_matches)}):")
                for line_num, line_text in pattern_matches:
                    print(f"      Line {line_num}: {line_text}")
            else:
                print(f"    No matches")
        
        print(f"  Category total: {category_matches} matches")
        total_matches += category_matches
    
    print(f"\nOverall total: {total_matches} pattern matches")
    
    # Test section detection
    print(f"\n--- Section Detection Analysis ---")
    
    sections = analyzer._identify_cobol_sections(lines)
    print(f"Detected sections: {len(sections)}")
    
    for section_name, (start_line, end_line) in sections.items():
        print(f"  {section_name}: Lines {start_line + 1} - {end_line}")
        
        # Check expected rules for this section
        section_expectations = analyzer.section_expectations.get("cobol", {}).get(section_name, {})
        expected_total = sum(section_expectations.values())
        print(f"    Expected rules: {expected_total}")
        
        # Count actual patterns in this section
        section_lines = lines[start_line:end_line]
        section_matches = 0
        
        for category, category_patterns in patterns.items():
            for pattern in category_patterns:
                for line in section_lines:
                    if re.search(pattern, line, re.IGNORECASE):
                        section_matches += 1
        
        print(f"    Pattern matches: {section_matches}")
    
    # Manual verification of known business rules
    print(f"\n--- Manual Business Rule Verification ---")
    
    known_business_rules = [
        (91, "IF APPLICANT-AGE < MIN-AGE"),
        (98, "IF AUTO-POLICY AND APPLICANT-AGE > MAX-AGE-AUTO"),
        (104, "IF LIFE-POLICY AND APPLICANT-AGE > MAX-AGE-LIFE"),
        (111, "IF CREDIT-SCORE < MIN-CREDIT-SCORE"),
        (118, "IF EMPLOYMENT-STATUS = 'UNEMPLOYED'"),
        (135, "IF APPLICANT-STATE = 'FL' OR APPLICANT-STATE = 'LA'"),
        (143, "IF COVERAGE-AMOUNT > 500000"),
        (158, "IF DRIVING-YEARS < MIN-DRIVING-YEARS"),
        (165, "IF ACCIDENT-COUNT > MAX-CLAIMS-ALLOWED"),
        (172, "IF HAS-DUI"),
        (179, "IF VIOLATION-COUNT > 3"),
        (186, "IF VEHICLE-TYPE = 'SPORTS' OR VEHICLE-TYPE = 'LUXURY'"),
        (195, "IF VEHICLE-AGE > 15"),
        (205, "IF IS-SMOKER"),
        (213, "IF COVERAGE-AMOUNT > 1000000"),
        (219, "IF HEALTH-CONDITIONS NOT = SPACES"),
        (225, "IF BENEFICIARY-COUNT = 0"),
        (237, "IF AUTO-POLICY AND APPLICANT-AGE < YOUNG-DRIVER-AGE"),
        (242, "IF AUTO-POLICY AND APPLICANT-AGE > SENIOR-DRIVER-AGE"),
        (249, "IF LIFE-POLICY AND IS-SMOKER"),
        (255, "IF MULTI-POLICY"),
        (261, "IF AUTO-POLICY AND CALCULATED-PREMIUM > MAX-PREMIUM-AUTO"),
        (265, "IF LIFE-POLICY AND CALCULATED-PREMIUM > MAX-PREMIUM-LIFE"),
        (270, "IF APPLICANT-STATE = 'FL' OR APPLICANT-STATE = 'CA'")
    ]
    
    print(f"Testing {len(known_business_rules)} known business rules:")
    
    matched_rules = 0
    for line_num, rule_description in known_business_rules:
        actual_line = lines[line_num - 1].strip() if line_num <= len(lines) else ""
        
        # Test against all patterns
        matched = False
        matching_categories = []
        
        for category, category_patterns in patterns.items():
            for pattern in category_patterns:
                if re.search(pattern, actual_line, re.IGNORECASE):
                    matched = True
                    matching_categories.append(category.value)
        
        if matched:
            matched_rules += 1
            print(f"  + Line {line_num}: {rule_description} -> {', '.join(set(matching_categories))}")
        else:
            print(f"  - Line {line_num}: {rule_description}")
            print(f"      Actual: {actual_line}")
    
    print(f"\nMatched {matched_rules}/{len(known_business_rules)} known business rules")
    print(f"Pattern detection accuracy: {matched_rules/len(known_business_rules)*100:.1f}%")
    
    return True

if __name__ == "__main__":
    debug_pattern_matching()