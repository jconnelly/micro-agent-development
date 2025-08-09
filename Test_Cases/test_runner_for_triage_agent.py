# test_runner_for_triage_agent.py

import json
from typing import Any, Dict, List
import os
import socket

# Import the classes from their respective files
from Agents.ComplianceMonitoringAgent import ComplianceMonitoringAgent, AuditLevel
from Agents.ApplicationTriageAgent import IntelligentSubmissionTriageAgent

# Import the Google Generative AI library
import google.generativeai as genai
from dotenv import load_dotenv

# --- No more Mock LLM Client needed ---
# The actual genai.Client will be used.


def load_submission_data(file_name: str) -> Dict[str, Any]:
    """Load submission data from JSON file in Sample_Data_Files directory"""
    folder_path = "./Sample_Data_Files/"
    file_path = folder_path + file_name
    
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: {file_path} not found. Please ensure the file exists.")
        return None
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return None

def main():
    # Define file paths
    folder_path = "./Sample_Data_Files/"
    
    # Available submission data files - comment/uncomment to test different sectors
    submission_file = "financial_submissions.json"
    #submission_file = "insurance_submissions.json"
    #submission_file = "government_submissions.json"
    #submission_file = "telecom_submissions.json"
    

    # --- Step 1: Load submission data from file ---
    print(f"Loading submission data from {submission_file}...")
    submission_data = load_submission_data(submission_file)
    
    if submission_data is None:
        return
    
    sector = submission_data.get("sector", "unknown")
    description = submission_data.get("description", "")
    sample_submissions = submission_data.get("submissions", [])
    
    print(f"Loaded {len(sample_submissions)} sample submissions for {sector} sector")
    print(f"Sector description: {description}")
    
    # Update output file paths to be sector-specific
    output_json_file_path = f"./Rule_Agent_Output_Files/triage_decisions_{sector}_output.json"
    audit_log_file_path = f"./Rule_Agent_Output_Files/triage_{sector}_audit_logs.jsonl"

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

    # --- Step 4: Initialize IntelligentSubmissionTriageAgent ---
    triage_agent = IntelligentSubmissionTriageAgent(
        llm_client=real_llm_client, # Pass the real client
        audit_system=audit_system,
        log_level=1,  # Enable logging for development/testing
        model_name="gemini-2.5-flash",
        llm_provider="google"
    )
    print("IntelligentSubmissionTriageAgent initialized.")

    # --- Step 5: Process each submission through the triage agent ---
    print(f"\\nProcessing submissions through IntelligentSubmissionTriageAgent using gemini-2.5-flash...")
    
    all_triage_results = []
    
    for idx, submission in enumerate(sample_submissions):
        print(f"\\n--- Processing Submission {idx + 1}/{len(sample_submissions)}: {submission['id']} ---")
        
        try:
            # Call the triage agent
            triage_result = triage_agent.triage_submission(
                submission_data=submission,
                audit_level=AuditLevel.LEVEL_1.value # Set to LEVEL_1 to see the audit trail
            )

            triage_decision = triage_result.get("triage_decision", {})
            audit_log_entry = triage_result.get("audit_log", {})
            
            # Add metadata for output
            result_with_metadata = {
                "submission_id": submission["id"],
                "submission_type": submission["type"], 
                "triage_decision": triage_decision,
                "processing_metadata": {
                    "model_used": "gemini-2.5-flash",
                    "audit_level": AuditLevel.LEVEL_1.value,
                    "agent_version": triage_agent.version
                }
            }
            
            all_triage_results.append(result_with_metadata)
            
            # Display results
            print(f"  Decision: {triage_decision.get('decision', 'Unknown')}")
            print(f"  Risk Score: {triage_decision.get('risk_score', 'N/A')}")
            print(f"  Category: {triage_decision.get('category', 'N/A')}")
            print(f"  Reasoning: {triage_decision.get('reasoning', 'No reasoning provided')[:100]}...")
            
        except Exception as e:
            print(f"  Error processing submission {submission['id']}: {e}")
            # Add error result
            error_result = {
                "submission_id": submission["id"],
                "submission_type": submission["type"],
                "triage_decision": {
                    "decision": "Error",
                    "reasoning": f"Processing error: {str(e)}",
                    "category": "System Error",
                    "risk_score": None
                },
                "processing_metadata": {
                    "model_used": "gemini-2.5-flash", 
                    "audit_level": AuditLevel.LEVEL_1.value,
                    "agent_version": triage_agent.version,
                    "error": str(e)
                }
            }
            all_triage_results.append(error_result)

    # --- Step 6: Output the triage decisions to a JSON file ---
    try:
        with open(output_json_file_path, 'w') as f:
            json.dump(all_triage_results, f, indent=2)
        print(f"\\nTriage decisions saved to {output_json_file_path}")
    except Exception as e:
        print(f"Error writing triage decisions to JSON file: {e}")

    # --- Step 7: Display summary ---
    print(f"\\n=== PROCESSING SUMMARY ===")
    print(f"Total submissions processed: {len(sample_submissions)}")
    successful_decisions = [r for r in all_triage_results if r["triage_decision"].get("decision") != "Error"]
    print(f"Successful triage decisions: {len(successful_decisions)}")
    
    if successful_decisions:
        decision_counts = {}
        for result in successful_decisions:
            decision = result["triage_decision"].get("decision", "Unknown")
            decision_counts[decision] = decision_counts.get(decision, 0) + 1
        
        print(f"Decision breakdown:")
        for decision, count in decision_counts.items():
            print(f"  {decision}: {count}")

    print(f"\\nDemonstration complete. Check '{output_json_file_path}' and '{audit_log_file_path}' files.")

if __name__ == "__main__":
    main()