#!/usr/bin/env python3
"""
Phase 15A Language Detection Test Script - Simple Version

Tests the LanguageDetector system with various programming languages
to validate detection accuracy and chunking parameter selection.
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from Utils.language_detection import LanguageDetector, LanguageDetectionError

def test_language_detection():
    """Test language detection with sample code snippets."""
    
    print("=" * 60)
    print("Phase 15A Language Detection Test")  
    print("=" * 60)
    
    # Initialize language detector
    try:
        detector = LanguageDetector()
        print("SUCCESS: Language detector initialized successfully")
        print(f"Available languages: {', '.join(detector.get_available_languages())}")
    except LanguageDetectionError as e:
        print(f"ERROR: Language detector initialization failed: {e}")
        return False
    
    # Test cases with different programming languages
    test_cases = [
        {
            "filename": "sample_legacy_insurance.cbl",
            "content": """
      IDENTIFICATION DIVISION.
      PROGRAM-ID. INSURANCE-VALIDATION.
      
      ENVIRONMENT DIVISION.
      
      DATA DIVISION.
      WORKING-STORAGE SECTION.
      01 APPLICANT-INFO.
         05 APPLICANT-AGE           PIC 99 VALUE ZERO.
         05 CREDIT-SCORE            PIC 999 VALUE ZERO.
         05 EMPLOYMENT-STATUS       PIC X(10) VALUE SPACES.
      
      PROCEDURE DIVISION.
      VALIDATE-APPLICATION.
          IF APPLICANT-AGE < 18
             MOVE 'REJECTED' TO APPLICATION-STATUS
          END-IF.
      """,
            "expected": "cobol"
        },
        {
            "filename": "BusinessLogic.java",
            "content": """
package com.example.insurance;

import java.util.List;

public class PolicyValidator {
    private static final int MIN_AGE = 18;
    
    public boolean validatePolicy(Applicant applicant) {
        if (applicant.getAge() < MIN_AGE) {
            throw new ValidationException("Applicant too young");
        }
        return true;
    }
}
      """,
            "expected": "java"
        },
        {
            "filename": "legacy_system.pas",
            "content": """
program InsuranceValidator;

type
  Applicant = record
    age: integer;
    creditScore: integer;
  end;

var
  applicant: Applicant;
  isValid: boolean;

function ValidateAge(age: integer): boolean;
begin
  if age < 18 then
    ValidateAge := false
  else
    ValidateAge := true;
end;

begin
  writeln('Insurance Validation System');
  isValid := ValidateAge(applicant.age);
end.
      """,
            "expected": "pascal"
        }
    ]
    
    print(f"\nTesting {len(test_cases)} language detection scenarios...")
    
    results = []
    for i, test_case in enumerate(test_cases, 1):
        filename = test_case["filename"]
        content = test_case["content"].strip()
        expected = test_case["expected"]
        
        print(f"\n--- Test {i}: {filename} ---")
        
        try:
            # Perform language detection
            detection_result = detector.detect_language(filename, content)
            
            # Check accuracy
            is_correct = detection_result.language == expected
            confidence = detection_result.confidence
            
            print(f"Expected: {expected}")
            print(f"Detected: {detection_result.language}")
            print(f"Confidence: {confidence:.1%}")
            print(f"Correct: {'Yes' if is_correct else 'No'}")
            
            # Show evidence
            if detection_result.evidence:
                strong_patterns = len(detection_result.evidence.get('pattern_matches', {}).get('strong', []))
                rule_patterns = sum(match['matches'] for match in 
                                  detection_result.evidence.get('pattern_matches', {}).get('rules', []))
                print(f"Evidence: {strong_patterns} strong patterns, {rule_patterns} rule patterns")
            
            # Show chunking parameters
            if detection_result.profile and detection_result.is_confident:
                chunking = detection_result.profile.chunking
                print(f"Chunking: size={chunking['preferred_size']} "
                      f"(range: {chunking['min_size']}-{chunking['max_size']})")
            
            # Show recommendations
            for rec in detection_result.recommendations[:2]:  # Show first 2 recommendations
                print(f"Recommendation: {rec}")
            
            results.append({
                "filename": filename,
                "expected": expected,
                "detected": detection_result.language,
                "confidence": confidence,
                "correct": is_correct,
                "confident": detection_result.is_confident
            })
            
        except Exception as e:
            print(f"ERROR: {e}")
            results.append({
                "filename": filename,
                "expected": expected,
                "detected": "error",
                "confidence": 0.0,
                "correct": False,
                "confident": False
            })
    
    # Summary
    print("\n" + "=" * 60)
    print("DETECTION ACCURACY SUMMARY")
    print("=" * 60)
    
    correct_count = sum(1 for r in results if r["correct"])
    total_count = len(results)
    accuracy = (correct_count / total_count) * 100 if total_count > 0 else 0
    
    confident_count = sum(1 for r in results if r["confident"])
    avg_confidence = sum(r["confidence"] for r in results) / total_count if total_count > 0 else 0
    
    print(f"Overall Accuracy: {accuracy:.1f}% ({correct_count}/{total_count})")
    print(f"Average Confidence: {avg_confidence:.1%}")
    print(f"High Confidence Detections: {confident_count}/{total_count}")
    
    # Individual results
    print(f"\nIndividual Results:")
    for result in results:
        status = "PASS" if result["correct"] else "FAIL"
        conf_indicator = "HIGH-CONF" if result["confident"] else "LOW-CONF"
        print(f"  {status} {conf_indicator} {result['filename']}: "
              f"{result['detected']} ({result['confidence']:.0%})")
    
    print("\n" + "=" * 60)
    success = accuracy >= 80 and confident_count >= (total_count * 0.8)
    if success:
        print("SUCCESS: Language detection system meets accuracy requirements!")
        print("   - Detection accuracy >= 80% PASS")
        print("   - High confidence rate >= 80% PASS") 
        print("   - Ready for production use with BusinessRuleExtractionAgent")
    else:
        print("NEEDS IMPROVEMENT: Language detection system needs tuning")
        print(f"   - Detection accuracy: {accuracy:.1f}% (target: >=80%)")
        print(f"   - High confidence rate: {confident_count/total_count*100:.1f}% (target: >=80%)")
    print("=" * 60)
    
    return success


if __name__ == "__main__":
    test_language_detection()