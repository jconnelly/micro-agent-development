# main_extractor.py (Relevant section)

import json
from typing import Any, Dict, List
import os
import sys
import socket

# Add project root to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import the classes from their respective files
from Agents.ComplianceMonitoringAgent import ComplianceMonitoringAgent, AuditLevel
from Agents.BusinessRuleExtractionAgent import BusinessRuleExtractorAgent

# Import the Google Generative AI library
import google.generativeai as genai
from dotenv import load_dotenv

def main():
    # Define file paths
    folder_path = "./Sample_Data_Files/"
    new_file_path_name = folder_path + "sample_legacy_code.java"
    #new_file_path_name = folder_path + "sample_legacy_insurance.cbl"
    #new_file_path_name = folder_path + "sample_legacy_trading.cpp"
    #new_file_path_name = folder_path + "sample_legacy_healthcare.mumps"
    #new_file_path_name = folder_path + "sample_legacy_manufacturing.pas"
    #new_file_path_name = folder_path + "sample_legacy_retail.pl"
    #new_file_path_name = folder_path + "sample_legacy_insurance.drl"
    #new_file_path_name = folder_path + "sample_legacy_banking.clp"
    #new_file_path_name = folder_path + "sample_legacy_ecommerce.xml"
    #new_file_path_name = folder_path + "sample_legacy_workflow.bpmn"

    output_json_file_path = "./Rule_Agent_Output_Files/extracted_rules_output.json"
    audit_log_file_path = "./Rule_Agent_Output_Files/audit_logs.jsonl" # This is the default for AgentAuditing

    # --- Step 1: Read the sample file ---
    try:
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

    # --- Step 3: Configure Gemini API ---
    try:
        # Load environment variables from .env file
        load_dotenv()
        
        # Get API key from environment
        api_key = os.getenv('GEMINI_API_KEY')        
        genai.configure(api_key=api_key)
        real_llm_client = genai.GenerativeModel('gemini-2.5-flash')
        print("Gemini API configured successfully.")
    except Exception as e:
        print(f"Error configuring Gemini API: {e}")
        return

    # --- Step 4: Initialize LegacyRuleExtractionAgent ---
    rule_extractor_agent = BusinessRuleExtractorAgent(
        llm_client=real_llm_client, # Pass the real client
        audit_system=audit_system,
        log_level=1,  # Enable logging for development/testing
        model_name="gemini-2.5-flash",
        llm_provider="google"
    )
    print("LegacyRuleExtractionAgent initialized.")

    # --- Step 5: Call the LegacyRuleExtractionAgent to extract rules ---
    print(f"\nCalling LegacyRuleExtractionAgent to extract rules using gemini-2.5-flash...")
    extraction_result = rule_extractor_agent.extract_and_translate_rules(
        legacy_code_snippet=code_content,
        context="This Java code processes loan applications for a financial institution.",
        audit_level=AuditLevel.LEVEL_1.value # Set to LEVEL_1 to see the audit trail
    )

    extracted_rules = extraction_result.get("extracted_rules", [])
    audit_log_entry = extraction_result.get("audit_log", {})

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

    print("\nDemonstration complete. Check 'extracted_rules_output.json', 'business_rules_documentation.md', and 'audit_logs.jsonl' files.")

if __name__ == "__main__":
    main()
