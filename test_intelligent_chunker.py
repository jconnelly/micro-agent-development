#!/usr/bin/env python3
"""
Phase 15B Intelligent Chunker Test Script

Tests the new IntelligentChunker system against the COBOL sample to validate
section-aware chunking and improved business rule extraction coverage.
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from Utils.intelligent_chunker import IntelligentChunker, ChunkingStrategy
from Utils.language_detection import LanguageDetector


def test_intelligent_chunking():
    """Test intelligent chunking with COBOL sample data."""
    
    print("=" * 70)
    print("Phase 15B Intelligent Chunker Test")
    print("=" * 70)
    
    # Load the COBOL sample file
    cobol_file_path = project_root / "Sample_Data_Files" / "sample_legacy_insurance.cbl"
    
    try:
        with open(cobol_file_path, 'r', encoding='utf-8') as f:
            cobol_content = f.read()
        print(f"SUCCESS: Loaded COBOL sample: {cobol_file_path}")
        print(f"File size: {len(cobol_content)} characters, {len(cobol_content.split(chr(10)))} lines")
    except FileNotFoundError:
        print(f"ERROR: COBOL sample file not found: {cobol_file_path}")
        return False
    except Exception as e:
        print(f"ERROR: Reading COBOL file: {e}")
        return False
    
    # Initialize language detector and intelligent chunker
    try:
        language_detector = LanguageDetector()
        intelligent_chunker = IntelligentChunker(language_detector)
        print("SUCCESS: Intelligent chunker initialized")
    except Exception as e:
        print(f"ERROR: Initializing intelligent chunker: {e}")
        return False
    
    print(f"\nTesting Multiple Chunking Strategies...")
    
    # Test different chunking strategies
    strategies = [
        ChunkingStrategy.SECTION_AWARE,
        ChunkingStrategy.RULE_BOUNDARY, 
        ChunkingStrategy.SMART_OVERLAP,
        ChunkingStrategy.FIXED_SIZE
    ]
    
    results = {}
    
    for strategy in strategies:
        print(f"\n--- Testing {strategy.value.upper()} Strategy ---")
        
        try:
            # Perform chunking
            chunking_result = intelligent_chunker.chunk_content(
                content=cobol_content,
                filename="sample_legacy_insurance.cbl",
                target_strategy=strategy
            )
            
            results[strategy] = chunking_result
            
            # Display results
            print(f"Language Detection: {chunking_result.language}")
            print(f"Strategy Used: {chunking_result.strategy_used.value}")
            print(f"Total Lines: {chunking_result.total_lines}")
            print(f"Chunk Count: {chunking_result.chunk_count}")
            print(f"Average Chunk Size: {chunking_result.average_chunk_size:.1f} lines")
            print(f"Size Variance: {chunking_result.size_variance:.2f}")
            print(f"Estimated Rule Coverage: {chunking_result.estimated_rule_coverage:.1%}")
            
            # Show chunk details
            print("Chunk Details:")
            for i, metadata in enumerate(chunking_result.metadata):
                section_info = f" ({metadata.section_name})" if metadata.section_name else ""
                print(f"  Chunk {i+1}: Lines {metadata.start_line}-{metadata.end_line} "
                      f"({metadata.content_lines} lines) - "
                      f"{metadata.rule_count_estimate} rules{section_info}")
            
        except Exception as e:
            print(f"ERROR: Chunking with {strategy.value} failed: {e}")
            results[strategy] = None
    
    # Compare strategies
    print(f"\n" + "=" * 70)
    print("STRATEGY COMPARISON SUMMARY")
    print("=" * 70)
    
    comparison_data = []
    for strategy, result in results.items():
        if result:
            total_rules = sum(meta.rule_count_estimate for meta in result.metadata)
            comparison_data.append({
                "strategy": strategy.value,
                "chunks": result.chunk_count,
                "avg_size": result.average_chunk_size,
                "variance": result.size_variance,
                "total_rules": total_rules,
                "coverage": result.estimated_rule_coverage,
                "result": result
            })
    
    # Sort by estimated rule coverage (descending)
    comparison_data.sort(key=lambda x: x["coverage"], reverse=True)
    
    print(f"{'Strategy':<15} {'Chunks':<7} {'Avg Size':<9} {'Variance':<9} {'Rules':<6} {'Coverage':<10}")
    print(f"{'-'*15} {'-'*7} {'-'*9} {'-'*9} {'-'*6} {'-'*10}")
    
    best_strategy = None
    best_coverage = 0.0
    
    for data in comparison_data:
        coverage_str = f"{data['coverage']:.1%}"
        print(f"{data['strategy']:<15} {data['chunks']:<7} {data['avg_size']:<9.1f} "
              f"{data['variance']:<9.2f} {data['total_rules']:<6} {coverage_str:<10}")
        
        if data['coverage'] > best_coverage:
            best_coverage = data['coverage'] 
            best_strategy = data['strategy']
    
    print(f"\nBEST STRATEGY: {best_strategy} (Coverage: {best_coverage:.1%})")
    
    # Detailed analysis of best strategy
    if best_strategy:
        best_result = next(data['result'] for data in comparison_data if data['strategy'] == best_strategy)
        
        print(f"\nDETAILED ANALYSIS: {best_strategy.upper()}")
        print(f"Language: {best_result.language}")
        print(f"Total lines processed: {best_result.total_lines}")
        print(f"Chunks created: {best_result.chunk_count}")
        
        # Show predicted vs current extraction
        total_estimated_rules = sum(meta.rule_count_estimate for meta in best_result.metadata)
        predicted_extraction = total_estimated_rules * best_coverage
        
        print(f"\nRule Extraction Prediction:")
        print(f"  Estimated rules in file: {total_estimated_rules}")
        print(f"  Expected extraction coverage: {best_coverage:.1%}")
        print(f"  Predicted extracted rules: {predicted_extraction:.0f}")
        print(f"  Current system extracts: 14 rules (58.3%)")
        print(f"  Expected improvement: {predicted_extraction-14:.0f} additional rules")
        
        # Target achievement  
        target_rules = 24  # From our analysis
        target_percentage = predicted_extraction / target_rules * 100 if target_rules > 0 else 0
        
        print(f"\nTarget Achievement:")
        print(f"  Target rules (from analysis): {target_rules}")
        print(f"  Predicted achievement: {target_percentage:.1f}%")
        
        success = target_percentage >= 90
        status = "SUCCESS" if success else "NEEDS IMPROVEMENT"
        print(f"  90% Target Status: {status}")
    
    # Recommendations
    print(f"\n" + "=" * 70)
    print("RECOMMENDATIONS")
    print("=" * 70)
    
    if best_coverage >= 0.9:
        print("EXCELLENT: Intelligent chunking ready for production deployment")
        print("   - Strategy selection algorithm working optimally")
        print("   - Expected to achieve 90%+ rule extraction accuracy")
        print("   - Significant improvement over current 58.3% extraction rate")
    elif best_coverage >= 0.7:
        print("GOOD: Intelligent chunking shows improvement, minor tuning needed")
        print("   - Consider refining section boundary detection patterns")
        print("   - Evaluate rule boundary identification accuracy")
        print("   - May achieve 70-89% rule extraction accuracy")
    else:
        print("NEEDS WORK: Intelligent chunking requires significant improvements")
        print("   - Review section and rule detection algorithms")
        print("   - Consider additional COBOL-specific patterns")
        print("   - Current approach may not significantly improve extraction")
    
    print("=" * 70)
    return best_coverage >= 0.7


if __name__ == "__main__":
    test_intelligent_chunking()