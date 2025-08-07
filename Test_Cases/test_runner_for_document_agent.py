# main_extractor.py (Relevant section)

import json
from typing import Any, Dict, List
import os

# Import the classes from their respective files
from Agents.AuditingAgent import AgentAuditing, AuditLevel
from Agents.RuleDocumentationAgent import RuleDocumentationAgent
from Agents.LegacyRuleExtractionAndTranslatorAgent import LegacyRuleExtractionAgent

# Import the Google Generative AI library
import google.generativeai as genai
import os
from dotenv import load_dotenv

# --- No more Mock LLM Client needed ---
# The actual genai.Client will be used.

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
    audit_system = AgentAuditing(log_storage_path=audit_log_file_path)
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
    rule_extractor_agent = LegacyRuleExtractionAgent(
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
    doc_agent = RuleDocumentationAgent(real_llm_client, audit_system)

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
    main()
