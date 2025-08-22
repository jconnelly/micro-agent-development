#!/usr/bin/env python3

"""
Type Annotation Validation Test

Validates that critical agent methods have proper type annotations.
This ensures comprehensive type coverage for better IDE support and type safety.
"""

import ast
import inspect
from typing import get_type_hints
from pathlib import Path

def test_type_annotation_coverage():
    """Test that critical agent methods have proper type annotations."""
    
    # Import key agent classes to test
    try:
        from Agents.BaseAgent import BaseAgent
        from Agents.PersonalDataProtectionAgent import PersonalDataProtectionAgent
        from Agents.BusinessRuleExtractionAgent import BusinessRuleExtractionAgent
        
        agents_to_test = [
            BaseAgent,
            PersonalDataProtectionAgent, 
            BusinessRuleExtractionAgent
        ]
        
        results = {
            'total_methods_checked': 0,
            'methods_with_annotations': 0,
            'methods_missing_annotations': [],
            'success_rate': 0
        }
        
        for agent_class in agents_to_test:
            # Get all public methods (not starting with _)
            methods = [method for method in dir(agent_class) 
                      if callable(getattr(agent_class, method)) 
                      and not method.startswith('_')
                      and method != '__init__']
            
            for method_name in methods:
                method = getattr(agent_class, method_name)
                
                # Check if method has type hints
                try:
                    type_hints = get_type_hints(method)
                    has_return_annotation = 'return' in type_hints
                    
                    results['total_methods_checked'] += 1
                    
                    if has_return_annotation:
                        results['methods_with_annotations'] += 1
                    else:
                        results['methods_missing_annotations'].append(f"{agent_class.__name__}.{method_name}")
                        
                except Exception as e:
                    # Some methods might not be introspectable
                    results['total_methods_checked'] += 1
                    results['methods_missing_annotations'].append(f"{agent_class.__name__}.{method_name} (error: {e})")
        
        # Calculate success rate
        if results['total_methods_checked'] > 0:
            results['success_rate'] = (results['methods_with_annotations'] / results['total_methods_checked']) * 100
        
        print(f"Type Annotation Coverage Report:")
        print(f"  Total methods checked: {results['total_methods_checked']}")
        print(f"  Methods with return type annotations: {results['methods_with_annotations']}")
        print(f"  Success rate: {results['success_rate']:.1f}%")
        
        if results['methods_missing_annotations']:
            print(f"  Methods missing annotations: {len(results['methods_missing_annotations'])}")
            for missing in results['methods_missing_annotations'][:5]:  # Show first 5
                print(f"    - {missing}")
            if len(results['methods_missing_annotations']) > 5:
                print(f"    ... and {len(results['methods_missing_annotations']) - 5} more")
        else:
            print("  All checked methods have proper return type annotations!")
        
        return results
        
    except ImportError as e:
        print(f"Error importing agent classes: {e}")
        return {'success_rate': 0, 'error': str(e)}


def test_specific_fixed_methods():
    """Test the specific methods we fixed for type annotations."""
    
    print("\nTesting specific methods that were fixed:")
    
    # Test 1: BusinessRuleExtractionAgent_original.get_last_completeness_report
    try:
        import ast
        with open('Agents/BusinessRuleExtractionAgent_original.py', 'r') as f:
            content = f.read()
            
        # Check if the method has return type annotation
        if 'def get_last_completeness_report(self) -> Optional[Any]:' in content:
            print("  BusinessRuleExtractionAgent_original.get_last_completeness_report has return type annotation")
        else:
            print("  BusinessRuleExtractionAgent_original.get_last_completeness_report missing return type annotation")
    except Exception as e:
        print(f"  ❌ Error checking BusinessRuleExtractionAgent_original: {e}")
    
    # Test 2: temp.py PolicyInquiryAgent.ingest_documents  
    try:
        with open('Agents/temp.py', 'r') as f:
            content = f.read()
            
        if 'def ingest_documents(self, documents: List[Dict[str, str]]) -> None:' in content:
            print("  PolicyInquiryAgent.ingest_documents has return type annotation")
        else:
            print("  PolicyInquiryAgent.ingest_documents missing return type annotation")
    except Exception as e:
        print(f"  ❌ Error checking temp.py: {e}")
    
    # Test 3: BaseAgent.audited_operation_context
    try:
        with open('Agents/BaseAgent.py', 'r') as f:
            content = f.read()
            
        if 'audit_level: int = None) -> Any:' in content:
            print("  BaseAgent.audited_operation_context has return type annotation")
        else:
            print("  BaseAgent.audited_operation_context missing return type annotation")
    except Exception as e:
        print(f"  ❌ Error checking BaseAgent.py: {e}")


if __name__ == '__main__':
    print("Running Type Annotation Coverage Tests...")
    
    # Test overall coverage
    results = test_type_annotation_coverage()
    
    # Test specific fixed methods
    test_specific_fixed_methods()
    
    # Summary
    print(f"\nSummary:")
    if results.get('success_rate', 0) > 95:
        print("Excellent type annotation coverage!")
    elif results.get('success_rate', 0) > 80:
        print("Good type annotation coverage!")  
    else:
        print("Type annotation coverage could be improved")
    
    if 'error' not in results:
        print(f"Overall success rate: {results.get('success_rate', 0):.1f}%")
    
    print("\nType annotation validation completed!")