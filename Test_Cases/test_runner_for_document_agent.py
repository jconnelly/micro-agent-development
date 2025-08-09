# main_extractor.py (Relevant section)

import json
from typing import Any, Dict, List
import os
import sys

# Add the parent directory to Python path for imports (since we're in Test_Cases subdirectory)
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

# Import the classes from their respective files
from Agents.ComplianceMonitoringAgent import ComplianceMonitoringAgent, AuditLevel
from Agents.RuleDocumentationGeneratorAgent import RuleDocumentationGeneratorAgent
from Agents.BusinessRuleExtractionAgent import BusinessRuleExtractorAgent

# Import the Google Generative AI library
import google.generativeai as genai
import os
from dotenv import load_dotenv

# --- No more Mock LLM Client needed ---
# The actual genai.Client will be used.

def test_documentation_formats(rules_json_file: str, output_format: str = "markdown"):
    """
    Test RuleDocumentationAgent with pre-extracted rules from JSON file.
    This allows testing different output formats without running rule extraction.
    
    Args:
        rules_json_file: Path to JSON file containing extracted rules
        output_format: Output format ('markdown', 'json', 'html')
    """
    print(f"\n=== Testing RuleDocumentationAgent with {output_format.upper()} format ===")
    
    # Load rules from JSON file
    try:
        with open(rules_json_file, 'r') as f:
            extracted_rules = json.load(f)
        print(f"Loaded {len(extracted_rules)} rules from {rules_json_file}")
    except FileNotFoundError:
        print(f"Error: {rules_json_file} not found.")
        return
    except Exception as e:
        print(f"Error reading {rules_json_file}: {e}")
        return

    # Initialize AgentAuditing
    audit_log_file_path = f"./Rule_Agent_Output_Files/doc_test_{output_format}_audit.jsonl"
    audit_system = ComplianceMonitoringAgent(log_storage_path=audit_log_file_path)
    print(f"AgentAuditing initialized for {output_format} format test.")

    # Configure Gemini API (though we won't use LLM for this test)
    try:
        load_dotenv()
        api_key = os.getenv('GEMINI_API_KEY')        
        genai.configure(api_key=api_key)
        real_llm_client = genai.GenerativeModel('gemini-1.5-flash')
        print("Gemini API configured (not used for this test).")
    except Exception as e:
        print(f"Warning: Gemini API configuration failed: {e}")
        real_llm_client = None

    # Initialize RuleDocumentationAgent
    doc_agent = RuleDocumentationGeneratorAgent(real_llm_client, audit_system)

    # Generate documentation in specified format
    print(f"\nGenerating {output_format} documentation...")
    result = doc_agent.document_and_visualize_rules(
        extracted_rules=extracted_rules,
        output_format=output_format,
        audit_level=AuditLevel.LEVEL_1.value
    )

    # Access the documentation result
    generated_docs = result.get("generated_documentation", "")
    doc_audit_log = result.get("audit_log", {})

    print(f"\nGenerated documentation for {len(extracted_rules)} business rules in {output_format} format.")
    
    # Display the generated documentation
    print("\n" + "="*80)
    print(f"GENERATED BUSINESS RULES DOCUMENTATION ({output_format.upper()})")
    print("="*80)
    print(generated_docs)
    print("="*80)

    # Save documentation to format-specific file
    file_extensions = {
        "markdown": "md",
        "json": "json", 
        "html": "html"
    }
    
    extension = file_extensions.get(output_format, "txt")
    doc_output_file_path = f"./Rule_Agent_Output_Files/business_rules_documentation_{output_format}.{extension}"
    
    try:
        with open(doc_output_file_path, 'w') as f:
            f.write(generated_docs)
        print(f"\nDocumentation saved to {doc_output_file_path}")
    except Exception as e:
        print(f"Error writing documentation to file: {e}")

    print(f"\n{output_format.capitalize()} format test complete!")
    return result

def test_all_documentation_formats(rules_json_file: str):
    """
    Test all documentation formats (markdown, json, html) with the same rule set.
    
    Args:
        rules_json_file: Path to JSON file containing extracted rules
    """
    print("\n" + "="*80)
    print("TESTING ALL DOCUMENTATION FORMATS")
    print("="*80)
    
    formats = ["markdown", "json", "html"]
    
    for format_name in formats:
        try:
            result = test_documentation_formats(rules_json_file, format_name)
            print(f"[PASS] {format_name.capitalize()} format test passed")
        except Exception as e:
            print(f"[FAIL] {format_name.capitalize()} format test failed: {e}")
    
    print(f"\n[SUCCESS] All format tests complete! Check ./Rule_Agent_Output_Files/ for output files:")
    for format_name in formats:
        extension = {"markdown": "md", "json": "json", "html": "html"}[format_name]
        print(f"   - business_rules_documentation_{format_name}.{extension}")

def main():
    # Define file paths
    folder_path = "./Sample_Data_Files/"
    #example_file = folder_path + "sample_legacy_code.java"
    #example_file = folder_path + "sample_legacy_insurance.cbl"
    #example_file = folder_path + "sample_legacy_trading.cpp"
    #example_file = folder_path + "sample_legacy_healthcare.mumps"
    #example_file = folder_path + "sample_legacy_manufacturing.pas"
    #example_file = folder_path + "sample_legacy_retail.pl"
    #example_file = folder_path + "sample_legacy_insurance.drl"
    example_file = folder_path + "sample_legacy_banking.clp"
    #example_file = folder_path + "sample_legacy_ecommerce.xml"
    #example_file = folder_path + "sample_legacy_workflow.bpmn"

    output_json_file_path = "./Rule_Agent_Output_Files/extracted_rules_output.json"
    audit_log_file_path = "./Rule_Agent_Output_Files/audit_logs.jsonl" # This is the default for AgentAuditing

    # --- Step 1: Read the sample Java file ---
    try:
        new_file_path_name = example_file

        # File Testing
        with open(new_file_path_name, 'r') as f:
            code_content = f.read()
        print(f"Successfully read {new_file_path_name}")
    except FileNotFoundError:
        print(f"Error: {new_file_path_name} not found. Please ensure it's in the same directory.")
        return
    except Exception as e:
        print(f"Error reading {new_file_path_name}: {e}")
        return

    # --- Step 2: Initialize AgentAuditing ---
    audit_system = ComplianceMonitoringAgent(log_storage_path=audit_log_file_path)
    print(f"AgentAuditing initialized. Logs will be written to {audit_log_file_path} (if audit_level > 0).")

    # --- Step 3: Load environment variables and configure Gemini API ---
    try:
        # Load environment variables from .env file
        load_dotenv()
        
        # Get API key from environment
        api_key = os.getenv('GEMINI_API_KEY')        
        genai.configure(api_key=api_key)
        real_llm_client = genai.GenerativeModel('gemini-1.5-flash')
        print("Gemini API configured successfully from environment variables.")
    except Exception as e:
        print(f"Error configuring Gemini API: {e}")
        return

    # --- Step 4: Initialize LegacyRuleExtractionAgent ---
    rule_extractor_agent = BusinessRuleExtractorAgent(
        llm_client=real_llm_client, # Pass the real client
        audit_system=audit_system
    )
    print("LegacyRuleExtractionAgent initialized.")

    # --- Step 5: Call the LegacyRuleExtractionAgent to extract rules ---
    print("\nCalling LegacyRuleExtractionAgent to extract rules using Gemini 1.5 Flash...")
    extraction_result = rule_extractor_agent.extract_and_translate_rules(
        legacy_code_snippet=code_content,
        context="This Java code processes loan applications for a financial institution.",
        audit_level=AuditLevel.LEVEL_1.value # Set to LEVEL_1 to see the audit trail
    )

    extracted_rules = extraction_result.get("extracted_rules", [])
    audit_log_entry = extraction_result.get("audit_log", {})

    # Initialize with LLM client and audit system
    doc_agent = RuleDocumentationGeneratorAgent(real_llm_client, audit_system)

    # Generate documentation from extracted rules
    result = doc_agent.document_and_visualize_rules(
        extracted_rules=extracted_rules,
        output_format="markdown",  # or "json", "html"
        audit_level=AuditLevel.LEVEL_1.value
    )

    # Access the documentation result
    generated_docs = result.get("generated_documentation", "")
    doc_audit_log = result.get("audit_log", {})

    print(f"\nExtracted {len(extracted_rules)} business rules.")
    
    # Display the generated documentation
    print("\n" + "="*60)
    print("GENERATED BUSINESS RULES DOCUMENTATION")
    print("="*60)
    print(generated_docs)
    print("="*60)

    # --- Step 6: Output the extracted rules to a JSON file ---
    try:
        with open(output_json_file_path, 'w') as f:
            json.dump(extracted_rules, f, indent=2)
        print(f"Extracted rules saved to {output_json_file_path}")
    except Exception as e:
        print(f"Error writing extracted rules to JSON file: {e}")

    # --- Print the audit log entry (if any) ---
    if audit_log_entry:
        print("\n--- Audit Log Entry (from return value) ---")
        # print(json.dumps(audit_log_entry, indent=2))
    else:
        print("\nNo audit log entry returned (due to audit_level=0).")

    # Save documentation to file
    doc_output_file_path = "./Rule_Agent_Output_Files/business_rules_documentation.md"
    try:
        with open(doc_output_file_path, 'w') as f:
            f.write(generated_docs)
        print(f"Documentation saved to {doc_output_file_path}")
    except Exception as e:
        print(f"Error writing documentation to file: {e}")

    print("\nDemonstration complete. Check 'extracted_rules_output.json', 'business_rules_documentation.md', and 'audit_logs.jsonl' files.")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test RuleDocumentationAgent with different modes")
    parser.add_argument("--mode", choices=["full", "formats", "single-format"], default="full", 
                       help="Test mode: 'full' runs complete extraction+documentation, 'formats' tests all formats with existing JSON, 'single-format' tests one format")
    parser.add_argument("--format", choices=["markdown", "json", "html"], default="markdown",
                       help="Output format for single-format mode")
    parser.add_argument("--rules-file", default="./Rule_Agent_Output_Files/extracted_rules_output.json",
                       help="Path to extracted rules JSON file")
    
    args = parser.parse_args()
    
    if args.mode == "full":
        # Run the original full extraction + documentation workflow
        print("Running full extraction and documentation workflow...")
        main()
    elif args.mode == "formats":
        # Test all formats with existing extracted rules
        print(f"Testing all documentation formats with rules from: {args.rules_file}")
        test_all_documentation_formats(args.rules_file)
    elif args.mode == "single-format":
        # Test single format with existing extracted rules
        print(f"Testing {args.format} format with rules from: {args.rules_file}")
        test_documentation_formats(args.rules_file, args.format)
