# agent_auditing.py

import json
import datetime
import socket
from enum import Enum
from typing import Dict, Any, List, Optional
import hashlib # For simple PII anonymization example

class AuditLevel(Enum):
    """Defines different levels of audit granularity for the AgentAuditing system."""
    LEVEL_0 = 0 # No auditing (primarily for development/testing, not recommended for production)
    LEVEL_1 = 1 # Full auditing: Captures all available details for maximum traceability.
    LEVEL_2 = 2 # Detailed auditing: Focuses on key LLM, Agent, and essential User details.
    LEVEL_3 = 3 # Summary auditing: Provides core decision, Agent, and basic User details.
    LEVEL_4 = 4 # Minimal auditing: Includes only Agent & Tooling Details, and core identifiers.

class AgentAuditing:
    def __init__(self, log_storage_path: str = "audit_logs.jsonl"):
        """
        Initializes the AgentAuditing system.

        Args:
            log_storage_path: Path to the file where audit logs will be stored.
                               Uses JSON Lines format for efficient appending.
        """
        self.log_storage_path = log_storage_path
        # Map audit levels to the specific fields that should be included in the log.
        self.audit_field_mapping = self._define_audit_field_mapping()

    def _define_audit_field_mapping(self) -> Dict[int, List[str]]:
        """
        Defines which fields are included for each audit level.
        This allows for flexible configuration and easy adaptation to changing requirements.
        """
        # Comprehensive list of all possible fields that can be logged
        ALL_FIELDS = [
            "timestamp", "request_id", "user_id", "session_id", "ip_address",
            "agent_id", "agent_name", "agent_version", "step_type",
            "llm_model_name", "llm_provider", "llm_input", "llm_output", 
            "tokens_input", "tokens_output", "tool_calls", "retrieved_chunks", 
            "final_decision", "duration_ms", "error_details", "user_feedback", 
            "score", "revision_attempts", "post_edit_distance", "resource_consumption"
        ]

        # Fields for Level 2: Detailed auditing
        LEVEL_2_FIELDS = [
            "timestamp", "request_id", "user_id", "session_id", "ip_address",
            "agent_id", "agent_name", "agent_version", "step_type",
            "llm_model_name", "llm_provider", "llm_input", "llm_output", 
            "tokens_input", "tokens_output", "tool_calls", "final_decision", 
            "duration_ms", "error_details"
        ]

        # Fields for Level 3: Summary auditing
        LEVEL_3_FIELDS = [
            "timestamp", "request_id", "user_id", "agent_id", "agent_name",
            "step_type", "llm_model_name", "final_decision", "duration_ms", "error_details"
        ]

        # Fields for Level 4: Minimal auditing (Agent & Tooling Details)
        LEVEL_4_FIELDS = [
            "timestamp", "request_id", "agent_id", "agent_name", "step_type",
            "llm_model_name", "tool_calls", "duration_ms", "error_details"
        ]

        return {
            AuditLevel.LEVEL_0.value: [], # No fields for level 0
            AuditLevel.LEVEL_1.value: ALL_FIELDS,
            AuditLevel.LEVEL_2.value: LEVEL_2_FIELDS,
            AuditLevel.LEVEL_3.value: LEVEL_3_FIELDS,
            AuditLevel.LEVEL_4.value: LEVEL_4_FIELDS,
        }

    def _filter_log_data(self, raw_log: Dict[str, Any], audit_level: int) -> Dict[str, Any]:
        """
        Filters the raw log data based on the specified audit level.
        Ensures only permitted fields are included and sensitive data is anonymized.
        """
        if audit_level == AuditLevel.LEVEL_0.value:
            return {}

        fields_to_include = self.audit_field_mapping.get(audit_level, [])
        filtered_log = {}
        
        # Pre-define sets for O(1) lookup performance instead of O(n) list searches
        sensitive_fields = {"user_id", "ip_address"}
        anonymous_values = {"anonymous", "N/A"}
        json_serializable_fields = {"llm_input", "llm_output", "final_decision"}

        for field in fields_to_include:
            if field in raw_log:
                value = raw_log[field]
                # Special handling for sensitive data: Redact or anonymize PII (O(1) set lookup)
                if field in sensitive_fields and value not in anonymous_values:
                    filtered_log[field] = self._anonymize_pii(str(value))
                # For complex objects like llm_input/output, ensure they are JSON serializable (O(1) set lookup)
                elif field in json_serializable_fields and isinstance(value, (dict, list)):
                    try:
                        filtered_log[field] = json.dumps(value)
                    except TypeError:
                        filtered_log[field] = str(value) # Fallback to string if not serializable
                else:
                    filtered_log[field] = value
        return filtered_log

    def _anonymize_pii(self, data: str) -> str:
        """
        Simple PII anonymization (e.g., hashing or masking).
        In a real production system, this would involve robust, irreversible hashing
        or tokenization using a dedicated PII management service.
        """
        # Example: Simple SHA256 hash for demonstration purposes
        return hashlib.sha256(data.encode('utf-8')).hexdigest()[:12] + "..."

    def log_agent_activity(self, **kwargs) -> Dict[str, Any]:
        """
        Logs the activity of an AI agent based on the specified audit level.
        Accepts a wide range of keyword arguments for flexibility in capturing context.

        Returns:
            The filtered log entry dictionary that was written (or would have been written).
        """
        audit_level = kwargs.get("audit_level", AuditLevel.LEVEL_1.value)
        raw_log_entry = {
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            **kwargs
        }

        # Filter the raw log data based on the configured audit level
        filtered_log_entry = self._filter_log_data(raw_log_entry, audit_level)

        if filtered_log_entry: # Only write to log if there are fields to include
            try:
                with open(self.log_storage_path, "a") as f:
                    f.write(json.dumps(filtered_log_entry) + "\n")
                print(f"Audit log entry written for request_id: {filtered_log_entry.get('request_id', 'N/A')} (Level {audit_level})")
            except IOError as e:
                print(f"Error writing audit log to file: {e}")
        else:
            print(f"No audit log entry generated for request_id: {kwargs.get('request_id', 'N/A')} (Level {audit_level}) - Audit level 0 or no fields configured.")

        return filtered_log_entry # Return the generated log for immediate use/response